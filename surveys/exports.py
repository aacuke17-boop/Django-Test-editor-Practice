import csv
from collections import defaultdict

from django.http import HttpResponse
from django.utils import timezone

from .formatting import format_duration, participant_label
from .models import Attempt, UserAnswer

UNSAFE_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value):
    """Protects spreadsheet programs from formulas typed into text cells."""
    text = str(value)
    if text.startswith(UNSAFE_PREFIXES):
        return "'" + text
    return text


def format_time(value):
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M:%S")


def build_csv_response(material):
    questions = list(material.questions.all())
    attempts = list(
        material.attempts.filter(status=Attempt.STATUS_COMPLETED)
        .select_related("user")
        .order_by("completed_at")
    )

    answers = defaultdict(lambda: defaultdict(list))
    selected = (
        UserAnswer.objects.filter(attempt__in=attempts)
        .select_related("option")
        .order_by("option__position", "option_id")
    )
    for answer in selected:
        answers[answer.attempt_id][answer.question_id].append(answer.option.option_text)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="material-{material.pk}-attempts.csv"'
    )
    response.write("\ufeff")
    writer = csv.writer(response)

    header = ["Attempt ID", "Participant", "Started", "Completed", "Duration"]
    if material.is_test:
        header.append("Score")
    header += [
        safe_cell(f"Answers to question: {question.question_text}")
        for question in questions
    ]
    writer.writerow(header)

    for attempt in attempts:
        row = [
            attempt.pk,
            safe_cell(participant_label(attempt.user)),
            format_time(attempt.started_at),
            format_time(attempt.completed_at),
            format_duration(attempt.completed_at - attempt.started_at),
        ]
        if material.is_test:
            row.append(attempt.score)
        for question in questions:
            options = answers[attempt.pk][question.pk]
            row.append(safe_cell("; ".join(options)))
        writer.writerow(row)

    return response