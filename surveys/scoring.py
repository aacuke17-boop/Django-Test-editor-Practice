from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Sum


def question_score(points, correct_total, wrong_total, correct_selected, wrong_selected):
    correct_share = Decimal(correct_selected) / Decimal(correct_total) if correct_total else Decimal(0)
    wrong_share = Decimal(wrong_selected) / Decimal(wrong_total) if wrong_total else Decimal(0)
    share = max(Decimal(0), correct_share - wrong_share)
    return points * share


def calculate_attempt_score(attempt):
    """Total score of an attempt, or None for surveys."""
    form = attempt.form
    if not form.is_test:
        return None
    selected_ids = set(attempt.answers.values_list("option_id", flat=True))
    total = Decimal("0")
    for question in form.questions.prefetch_related("options"):
        options = list(question.options.all())
        correct_ids = {option.option_id for option in options if option.is_correct}
        wrong_ids = {option.option_id for option in options if not option.is_correct}
        total += question_score(
            question.points,
            len(correct_ids),
            len(wrong_ids),
            len(selected_ids & correct_ids),
            len(selected_ids & wrong_ids),
        )
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_max_score(form):
    total = form.questions.aggregate(total=Sum("points"))["total"]
    return total or Decimal("0")