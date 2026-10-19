from collections import Counter, defaultdict
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Avg

from .formatting import format_duration
from .models import Attempt, UserAnswer
from .scoring import calculate_max_score


def percent(part, total):
    return (part * 100 / total) if total else 0


def compute_statistics(material):
    completed = material.attempts.filter(status=Attempt.STATUS_COMPLETED)
    attempts = list(completed)
    total = len(attempts)
    is_test = material.is_test

    average_duration = "-"
    average_score = None
    max_score = None
    if total:
        durations = [attempt.completed_at - attempt.started_at for attempt in attempts]
        average_duration = format_duration(sum(durations, timedelta()) / total)
    if is_test:
        max_score = calculate_max_score(material)
        average = completed.aggregate(avg=Avg("score"))["avg"]
        if average is not None:
            average_score = Decimal(str(average)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

    selected = defaultdict(lambda: defaultdict(set))
    option_counts = Counter()
    rows = UserAnswer.objects.filter(
        attempt__form=material, attempt__status=Attempt.STATUS_COMPLETED
    ).values_list("attempt_id", "question_id", "option_id")
    for attempt_id, question_id, option_id in rows:
        selected[attempt_id][question_id].add(option_id)
        option_counts[option_id] += 1

    questions = []
    for question in material.questions.prefetch_related("options"):
        options = list(question.options.all())
        correct_ids = {option.pk for option in options if option.is_correct}
        positive = 0
        for attempt in attempts:
            chosen = selected[attempt.pk][question.pk]
            if is_test:
                if chosen == correct_ids:
                    positive += 1
            elif chosen:
                positive += 1
        questions.append(
            {
                "question": question,
                "positive": positive,
                "negative": total - positive,
                "percent": percent(positive, total),
                "options": [
                    {
                        "option": option,
                        "count": option_counts[option.pk],
                        "percent": percent(option_counts[option.pk], total),
                    }
                    for option in options
                ],
            }
        )

    return {
        "total": total,
        "average_score": average_score,
        "max_score": max_score,
        "average_duration": average_duration,
        "questions": questions,
    }