from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import QuestionnaireForm
from .models import Questionnaire


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
    if request.method == "POST":
        form = QuestionnaireForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.creator = request.user
            material.save()
            return redirect("my_materials")
    else:
        form = QuestionnaireForm()
    return render(request, "surveys/material_editor.html", {"form": form})