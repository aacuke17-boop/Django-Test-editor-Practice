from decimal import Decimal, InvalidOperation

from .models import AnswerOption, Question


def blank_option(index):
    return {"index": str(index), "text": "", "correct": False}


def blank_question(index):
    return {
        "index": str(index),
        "text": "",
        "points": "0",
        "options": [blank_option(1), blank_option(2)],
    }


def parse_points(value):
    try:
        points = Decimal(value)
    except InvalidOperation:
        return Decimal("0")
    if not points.is_finite() or points < 0 or points > Decimal("999.99"):
        return Decimal("0")
    return points.quantize(Decimal("0.01"))


def parse_options(post, question_index):
    options = []
    for index in post.getlist(f"q{question_index}_option_index"):
        if not (index.isascii() and index.isdigit()):
            continue
        key = f"q{question_index}_o{index}"
        options.append(
            {
                "index": index,
                "text": post.get(f"{key}_text", "").strip(),
                "correct": f"{key}_correct" in post,
            }
        )
    return options


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
                "options": parse_options(post, index),
            }
        )
    return questions


def save_questions(material, questions):
    position = 0
    for item in questions:
        if not item["text"]:
            continue
        position += 1
        question = Question.objects.create(
            form=material,
            question_text=item["text"],
            points=parse_points(item["points"]),
            position=position,
        )
        option_position = 0
        for option in item["options"]:
            if not option["text"]:
                continue
            option_position += 1
            AnswerOption.objects.create(
                question=question,
                option_text=option["text"],
                is_correct=option["correct"],
                position=option_position,
            )