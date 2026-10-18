from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .editor import (
    blank_option,
    blank_question,
    load_questions,
    parse_questions,
    replace_questions,
    save_questions,
    validate_editor,
)
from .forms import GrantAccessForm, QuestionnaireForm
from .models import Access, Attempt, Questionnaire, UserAnswer
from .scoring import calculate_attempt_score, calculate_max_score


def get_own_material(request, pk):
    return get_object_or_404(Questionnaire, pk=pk, creator=request.user)


def get_own_attempt(request, attempt_id):
    return get_object_or_404(
        Attempt.objects.select_related("form"),
        pk=attempt_id,
        user=request.user,
    )


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
    return render(
        request,
        "surveys/material_detail.html",
        {"material": material, "has_questions": material.questions.exists()},
    )


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


@login_required
def material_access(request, pk):
    material = get_own_material(request, pk)
    if request.method == "POST":
        form = GrantAccessForm(material, request.POST)
        if form.is_valid():
            Access.objects.create(form=material, user=form.user)
            messages.success(request, f"Access granted to {form.user.email}.")
            return redirect("material_access", pk=material.pk)
    else:
        form = GrantAccessForm(material)
    entries = material.access_entries.select_related("user").order_by("user__email")
    return render(
        request,
        "surveys/material_access.html",
        {"material": material, "entries": entries, "form": form},
    )


@login_required
@require_POST
def material_access_revoke(request, pk, user_id):
    material = get_own_material(request, pk)
    entry = material.access_entries.select_related("user").filter(user_id=user_id).first()
    if entry is None:
        messages.error(request, "This user does not have access.")
    else:
        email = entry.user.email
        material.access_entries.filter(user_id=user_id).delete()
        messages.success(request, f"Access revoked from {email}.")
    return redirect("material_access", pk=material.pk)

@login_required
@require_POST
def attempt_start(request, pk):
    material = get_object_or_404(Questionnaire.objects.available_to(request.user), pk=pk)
    if not material.questions.exists():
        messages.error(request, "This material has no questions yet.")
        return redirect("material_detail", pk=material.pk)
    attempt = Attempt.objects.create(form=material, user=request.user)
    return redirect("attempt_take", attempt_id=attempt.pk)


@login_required
def attempt_take(request, attempt_id):
    attempt = get_own_attempt(request, attempt_id)
    if attempt.status == Attempt.STATUS_COMPLETED:
        return redirect("attempt_result", attempt_id=attempt.pk)
    material = attempt.form
    questions = list(material.questions.prefetch_related("options"))

    if request.method == "POST":
        answers = []
        for question in questions:
            options = list(question.options.all())
            allowed = {option.pk for option in options}
            chosen = {
                int(value)
                for value in request.POST.getlist(f"question_{question.pk}")
                if value.isascii() and value.isdigit()
            } & allowed
            for option in options:
                if option.pk in chosen:
                    answers.append(UserAnswer(attempt=attempt, question=question, option=option))

        with transaction.atomic():
            locked = Attempt.objects.select_for_update().get(pk=attempt.pk)
            if locked.status == Attempt.STATUS_COMPLETED:
                return redirect("attempt_result", attempt_id=locked.pk)
            UserAnswer.objects.bulk_create(answers)
            locked.completed_at = timezone.now()
            locked.status = Attempt.STATUS_COMPLETED
            locked.score = calculate_attempt_score(locked)
            locked.save(update_fields=["completed_at", "status", "score"])
        return redirect("attempt_result", attempt_id=attempt.pk)

    return render(
        request,
        "surveys/attempt_take.html",
        {"attempt": attempt, "material": material, "questions": questions},
    )


@login_required
def attempt_result(request, attempt_id):
    attempt = get_own_attempt(request, attempt_id)
    if attempt.status != Attempt.STATUS_COMPLETED:
        return redirect("attempt_take", attempt_id=attempt.pk)
    material = attempt.form
    context = {"attempt": attempt, "material": material}
    if material.is_test:
        max_score = calculate_max_score(material)
        context["max_score"] = max_score
        context["percent"] = (attempt.score / max_score * 100) if max_score else 0
    return render(request, "surveys/attempt_result.html", context)