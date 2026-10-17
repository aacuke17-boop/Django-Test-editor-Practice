from decimal import Decimal, InvalidOperation

from .models import AnswerOption, Question

MAX_OPTION_LENGTH = 500
MAX_POINTS = Decimal("999.99")


def blank_option(index):
    return {"index": str(index), "text": "", "correct": False}


def blank_question(index):
    return {
        "index": str(index),
        "text": "",
        "points": "1",
        "options": [blank_option(1), blank_option(2)],
    }


def is_valid_points(value):
    try:
        points = Decimal(value)
    except InvalidOperation:
        return False
    return points.is_finite() and 0 <= points <= MAX_POINTS


def parse_points(value):
    return Decimal(value).quantize(Decimal("0.01"))


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


def validate_editor(questions, is_test):
    errors = []
    if not questions:
        errors.append("Add at least one question.")
    for number, item in enumerate(questions, start=1):
        label = f"Question {number}"
        if not item["text"]:
            errors.append(f"{label}: the question text is empty.")
        if not item["options"]:
            errors.append(f"{label}: add at least one option.")
        for option_number, option in enumerate(item["options"], start=1):
            if not option["text"]:
                errors.append(f"{label}, option {option_number}: the option text is empty.")
            elif len(option["text"]) > MAX_OPTION_LENGTH:
                errors.append(
                    f"{label}, option {option_number}: the option text is too long "
                    f"(max {MAX_OPTION_LENGTH} characters)."
                )
        if is_test:
            if item["options"] and not any(option["correct"] for option in item["options"]):
                errors.append(f"{label}: mark at least one correct option.")
            if not is_valid_points(item["points"]):
                errors.append(f"{label}: enter the points (a number from 0 to 999.99).")
    return errors


def save_questions(material, questions):
    is_test = material.is_test
    for position, item in enumerate(questions, start=1):
        question = Question.objects.create(
            form=material,
            question_text=item["text"],
            points=parse_points(item["points"]) if is_test else Decimal("0"),
            position=position,
        )
        for option_position, option in enumerate(item["options"], start=1):
            AnswerOption.objects.create(
                question=question,
                option_text=option["text"],
                is_correct=bool(option["correct"]) and is_test,
                position=option_position,
            )