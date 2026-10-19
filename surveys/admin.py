from django.contrib import admin

from .formatting import participant_label
from .models import AnswerOption, Attempt, Question, Questionnaire, UserAnswer


def shorten(text, limit=80):
    return text if len(text) <= limit else text[: limit - 1] + "…"


class ReadOnlyAdmin(admin.ModelAdmin):
    """Staff can look at the records, but not add, change or delete them."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = (
        "form_id",
        "title",
        "is_test",
        "restricted_access",
        "author",
        "creation_time",
    )
    list_filter = ("is_test", "restricted_access")
    search_fields = ("title", "description", "creator__email", "creator__username")
    list_select_related = ("creator",)
    ordering = ("-creation_time",)

    @admin.display(description="Author", ordering="creator__username")
    def author(self, obj):
        return obj.creator.username if obj.creator else "Deleted user"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_deleted_objects(self, objs, request):
        deletable, model_count, _perms_needed, protected = super().get_deleted_objects(
            objs, request
        )
        return deletable, model_count, set(), protected


@admin.register(Question)
class QuestionAdmin(ReadOnlyAdmin):
    list_display = ("question_id", "short_text", "form", "points", "position")
    search_fields = ("question_text", "form__title")
    list_select_related = ("form",)
    ordering = ("form_id", "position")

    @admin.display(description="Question")
    def short_text(self, obj):
        return shorten(obj.question_text)


@admin.register(AnswerOption)
class AnswerOptionAdmin(ReadOnlyAdmin):
    list_display = ("option_id", "option_text", "short_question", "is_correct", "position")
    list_filter = ("is_correct",)
    search_fields = ("option_text", "question__question_text", "question__form__title")
    list_select_related = ("question",)
    ordering = ("question_id", "position")

    @admin.display(description="Question")
    def short_question(self, obj):
        return shorten(obj.question.question_text, 50)


@admin.register(Attempt)
class AttemptAdmin(ReadOnlyAdmin):
    list_display = (
        "attempt_id",
        "form",
        "participant",
        "status",
        "score",
        "started_at",
        "completed_at",
    )
    list_filter = ("status", "form__is_test")
    search_fields = ("form__title", "user__email", "user__username")
    list_select_related = ("form", "user")
    ordering = ("-attempt_id",)

    @admin.display(description="Participant", ordering="user__username")
    def participant(self, obj):
        return participant_label(obj.user)


@admin.register(UserAnswer)
class UserAnswerAdmin(ReadOnlyAdmin):
    list_display = ("answer_id", "attempt", "short_question", "option")
    search_fields = (
        "attempt__form__title",
        "question__question_text",
        "option__option_text",
    )
    list_select_related = ("attempt", "question", "option")
    ordering = ("-answer_id",)

    @admin.display(description="Question")
    def short_question(self, obj):
        return shorten(obj.question.question_text, 50)