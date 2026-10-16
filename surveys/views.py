from django.shortcuts import get_object_or_404, render

from .models import Questionnaire


def home(request):
    materials = (
        Questionnaire.objects.available_to(request.user)
        .select_related("creator")
        .order_by("-creation_time")
    )
    return render(request, "surveys/home.html", {"materials": materials})


def material_detail(request, pk):
    material = get_object_or_404(
        Questionnaire.objects.available_to(request.user).select_related("creator"),
        pk=pk,
    )
    return render(request, "surveys/material_detail.html", {"material": material})