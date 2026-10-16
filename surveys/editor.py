from decimal import Decimal, InvalidOperation

from .models import Question


def blank_question(index):
    return {"index": str(index), "text": "", "points": "0"}


def parse_points(value):
    try:
        points = Decimal(value)
    except InvalidOperation:
        return Decimal("0")
    if not points.is_finite() or points < 0 or points > Decimal("999.99"):
        return Decimal("0")
    return points.quantize(Decimal("0.01"))


def parse_questions(post):
    questions = []
    for index in post.getlist("question_index"):
        if not (index.isascii() and index.isdigit()):
            continue
        questions.append(
            {
                "index": index,
                "text": post.get(f"q{index}_text", "").strip(),
                "points": post.get(f"q{index}_points", "").strip(),
            }
        )
    return questions


def save_questions(material, questions):
    position = 0
    for item in questions:
        if not item["text"]:
            continue
        position += 1
        Question.objects.create(
            form=material,
            question_text=item["text"],
            points=parse_points(item["points"]),
            position=position,
        )