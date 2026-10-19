from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import Http404

from accounts.models import ANONYMOUS_EMAIL, User

from .editor import (
    blank_option,
    blank_question,
    load_questions,
    parse_questions,
    posted_signature,
    replace_questions,
    save_questions,
    stored_signature,
    validate_editor,
)
from .forms import GrantAccessForm, QuestionnaireForm
from .models import Access, Attempt, Questionnaire, UserAnswer
from .scoring import calculate_attempt_score, calculate_max_score
from .review import build_review
from .formatting import format_duration, participant_label


def get_own_material(request, pk):
    return get_object_or_404(Questionnaire, pk=pk, creator=request.user)


class AttemptRemoved(Exception):
    def __init__(self, material_id):
        super().__init__(material_id)
        self.material_id = material_id


def remember_attempt(request, attempt):
    remembered = request.session.get("attempts", {})
    remembered[str(attempt.pk)] = attempt.form_id
    if len(remembered) > 50:
        remembered = dict(list(remembered.items())[-50:])
    request.session["attempts"] = remembered


def get_own_attempt(request, attempt_id):
    queryset = Attempt.objects.select_related("form")
    remembered = request.session.get("attempts", {})
    if request.user.is_authenticated:
        attempt = queryset.filter(pk=attempt_id, user=request.user).first()
    elif str(attempt_id) in remembered:
        attempt = queryset.filter(pk=attempt_id, user__email=ANONYMOUS_EMAIL).first()
    else:
        raise Http404
    if attempt is None:
        material_id = remembered.get(str(attempt_id))
        if material_id is None:
            raise Http404
        raise AttemptRemoved(material_id)
    return attempt


def attempt_removed_response(request, material_id):
    material = Questionnaire.objects.available_to(request.user).filter(pk=material_id).first()
    return render(
        request,
        "surveys/attempt_removed.html",
        {"material": material},
        status=410,
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
    original_is_test = material.is_test
    editor_errors = []
    confirm_count = 0
    if request.method == "POST":
        form = QuestionnaireForm(request.POST, instance=material)
        questions = parse_questions(request.POST)
        form_valid = form.is_valid()
        is_test = form.cleaned_data.get("is_test", False)
        editor_errors = validate_editor(questions, is_test)
        if form_valid and not editor_errors:
            changed = posted_signature(questions, is_test) != stored_signature(
                material, original_is_test
            )
            completed_count = material.attempts.filter(
                status=Attempt.STATUS_COMPLETED
            ).count()
            if changed and completed_count and request.POST.get("confirm_delete") != "1":
                confirm_count = completed_count
            else:
                with transaction.atomic():
                    form.save()
                    if changed:
                        material.attempts.all().delete()
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
            "confirm_count": confirm_count,
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

@require_POST
def attempt_start(request, pk):
    material = get_object_or_404(Questionnaire.objects.available_to(request.user), pk=pk)
    if not material.questions.exists():
        messages.error(request, "This material has no questions yet.")
        return redirect("material_detail", pk=material.pk)
    if request.user.is_authenticated:
        attempt = Attempt.objects.create(form=material, user=request.user)
    else:
        anonymous = User.objects.get(email=ANONYMOUS_EMAIL)
        attempt = Attempt.objects.create(form=material, user=anonymous)
    remember_attempt(request, attempt)
    return redirect("attempt_take", attempt_id=attempt.pk)


def attempt_take(request, attempt_id):
    try:
        attempt = get_own_attempt(request, attempt_id)
    except AttemptRemoved as removed:
        return attempt_removed_response(request, removed.material_id)
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
            locked = Attempt.objects.select_for_update().filter(pk=attempt.pk).first()
            if locked is None:
                return redirect("attempt_take", attempt_id=attempt_id)
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


def attempt_result(request, attempt_id):
    try:
        attempt = get_own_attempt(request, attempt_id)
    except AttemptRemoved as removed:
        return attempt_removed_response(request, removed.material_id)
    if attempt.status != Attempt.STATUS_COMPLETED:
        return redirect("attempt_take", attempt_id=attempt.pk)
    material = attempt.form
    context = {"attempt": attempt, "material": material}
    if material.is_test:
        max_score = calculate_max_score(material)
        context["max_score"] = max_score
        context["percent"] = (attempt.score / max_score * 100) if max_score else 0
        context["review"] = build_review(attempt)
    return render(request, "surveys/attempt_result.html", context)

@login_required
def my_attempts(request):
    attempts = (
        Attempt.objects.filter(user=request.user, status=Attempt.STATUS_COMPLETED)
        .select_related("form")
        .order_by("-completed_at")
    )
    max_scores = {}
    rows = []
    for attempt in attempts:
        material = attempt.form
        max_score = None
        if material.is_test:
            if material.pk not in max_scores:
                max_scores[material.pk] = calculate_max_score(material)
            max_score = max_scores[material.pk]
        rows.append(
            {
                "attempt": attempt,
                "duration": format_duration(attempt.completed_at - attempt.started_at),
                "max_score": max_score,
            }
        )
    return render(request, "surveys/my_attempts.html", {"rows": rows})

@login_required
def material_attempts(request, pk):
    material = get_own_material(request, pk)
    attempts = (
        material.attempts.filter(status=Attempt.STATUS_COMPLETED)
        .select_related("user")
        .order_by("-completed_at")
    )
    rows = [
        {
            "attempt": attempt,
            "participant": participant_label(attempt.user),
            "duration": format_duration(attempt.completed_at - attempt.started_at),
        }
        for attempt in attempts
    ]
    max_score = calculate_max_score(material) if material.is_test else None
    return render(
        request,
        "surveys/material_attempts.html",
        {"material": material, "rows": rows, "max_score": max_score},
    )

@login_required
def material_attempt_detail(request, pk, attempt_id):
    material = get_own_material(request, pk)
    attempt = get_object_or_404(
        material.attempts.select_related("user", "form"),
        pk=attempt_id,
        status=Attempt.STATUS_COMPLETED,
    )
    context = {
        "material": material,
        "attempt": attempt,
        "participant": participant_label(attempt.user),
        "duration": format_duration(attempt.completed_at - attempt.started_at),
        "review": build_review(attempt),
    }
    if material.is_test:
        context["max_score"] = calculate_max_score(material)
    return render(request, "surveys/material_attempt_detail.html", context)