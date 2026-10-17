from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .editor import (
    blank_option,
    blank_question,
    load_questions,
    parse_questions,
    replace_questions,
    save_questions,
    validate_editor,
)
from .forms import QuestionnaireForm
from .models import Questionnaire


def get_own_material(request, pk):
    return get_object_or_404(Questionnaire, pk=pk, creator=request.user)


def home(request):
    query = request.GET.get("q", "").strip()
    materials = (
        Questionnaire.objects.available_to(request.user)
        .search(query)
        .select_related("creator")
        .order_by("-creation_time")
    )
    return render(
        request,
        "surveys/home.html",
        {"materials": materials, "query": query},
    )


def material_detail(request, pk):
    material = get_object_or_404(
        Questionnaire.objects.available_to(request.user).select_related("creator"),
        pk=pk,
    )
    return render(request, "surveys/material_detail.html", {"material": material})


@login_required
def my_materials(request):
    query = request.GET.get("q", "").strip()
    materials = (
        Questionnaire.objects.filter(creator=request.user)
        .search(query)
        .order_by("-creation_time")
    )
    return render(
        request,
        "surveys/my_materials.html",
        {"materials": materials, "query": query},
    )


@login_required
def material_create(request):
    editor_errors = []
    if request.method == "POST":
        form = QuestionnaireForm(request.POST)
        questions = parse_questions(request.POST)
        form_valid = form.is_valid()
        editor_errors = validate_editor(questions, form.cleaned_data.get("is_test", False))
        if form_valid and not editor_errors:
            with transaction.atomic():
                material = form.save(commit=False)
                material.creator = request.user
                material.save()
                save_questions(material, questions)
            return redirect("my_materials")
    else:
        form = QuestionnaireForm()
        questions = [blank_question(1)]
    return render(
        request,
        "surveys/material_editor.html",
        {
            "form": form,
            "questions": questions,
            "editor_errors": editor_errors,
            "blank_question": blank_question("__index__"),
            "blank_option": blank_option("__oindex__"),
        },
    )

@login_required
def material_edit(request, pk):
    material = get_own_material(request, pk)
    editor_errors = []
    if request.method == "POST":
        form = QuestionnaireForm(request.POST, instance=material)
        questions = parse_questions(request.POST)
        form_valid = form.is_valid()
        editor_errors = validate_editor(questions, form.cleaned_data.get("is_test", False))
        if form_valid and not editor_errors:
            with transaction.atomic():
                form.save()
                replace_questions(material, questions)
            return redirect("my_materials")
    else:
        form = QuestionnaireForm(instance=material)
        questions = load_questions(material) or [blank_question(1)]
    return render(
        request,
        "surveys/material_editor.html",
        {
            "form": form,
            "material": material,
            "questions": questions,
            "editor_errors": editor_errors,
            "blank_question": blank_question("__index__"),
            "blank_option": blank_option("__oindex__"),
        },
    )

@login_required
def material_delete(request, pk):
    material = get_own_material(request, pk)
    if request.method == "POST":
        material.delete()
        return redirect("my_materials")
    return render(
        request,
        "surveys/material_confirm_delete.html",
        {"material": material, "attempts_count": material.attempts.count()},
    )