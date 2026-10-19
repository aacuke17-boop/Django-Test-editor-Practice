from .scoring import question_score


def build_review(attempt):
    selected_ids = set(attempt.answers.values_list("option_id", flat=True))
    review = []
    for question in attempt.form.questions.prefetch_related("options"):
        options = list(question.options.all())
        correct_ids = {option.option_id for option in options if option.is_correct}
        wrong_ids = {option.option_id for option in options if not option.is_correct}
        entries = []
        for option in options:
            selected = option.option_id in selected_ids
            if selected and option.is_correct:
                css, label = "option-ok", "your answer: correct"
            elif selected:
                css, label = "option-wrong", "your answer: wrong"
            elif option.is_correct:
                css, label = "option-missed", "correct answer"
            else:
                css, label = "", ""
            entries.append(
                {"option": option, "selected": selected, "css": css, "label": label}
            )
        earned = question_score(
            question.points,
            len(correct_ids),
            len(wrong_ids),
            len(selected_ids & correct_ids),
            len(selected_ids & wrong_ids),
        )
        review.append({"question": question, "options": entries, "earned": earned})
    return review