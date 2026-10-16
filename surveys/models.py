from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class QuestionnaireQuerySet(models.QuerySet):
    def available_to(self, user):
        public = Q(restricted_access=False)
        if user is None or not user.is_authenticated:
            return self.filter(public)
        granted = Access.objects.filter(user=user).values("form_id")
        return self.filter(public | Q(creator=user) | Q(pk__in=granted))

class Questionnaire(models.Model):
    form_id = models.AutoField(primary_key=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        db_column="creator_id",
        related_name="questionnaires",
    )
    title = models.CharField(max_length=255)
    is_test = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    restricted_access = models.BooleanField(default=False)
    creation_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    objects = QuestionnaireQuerySet.as_manager()

    class Meta:
        managed = False
        db_table = "forms"

    def __str__(self):
        return self.title


class Question(models.Model):
    question_id = models.AutoField(primary_key=True)
    form = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        db_column="form_id",
        related_name="questions",
    )
    question_text = models.TextField()
    points = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    position = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "questions"
        ordering = ["position", "question_id"]

    def __str__(self):
        return self.question_text


class AnswerOption(models.Model):
    option_id = models.AutoField(primary_key=True)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        db_column="question_id",
        related_name="options",
    )
    option_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    position = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "answer_options"
        ordering = ["position", "option_id"]

    def __str__(self):
        return self.option_text


class Access(models.Model):
    pk = models.CompositePrimaryKey("form_id", "user_id")
    form = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        db_column="form_id",
        related_name="access_entries",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="access_entries",
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "access"

    def __str__(self):
        return f"{self.user} -> {self.form}"


class Attempt(models.Model):
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, "In progress"),
        (STATUS_COMPLETED, "Completed"),
    ]

    attempt_id = models.AutoField(primary_key=True)
    form = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        db_column="form_id",
        related_name="attempts",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        db_column="user_id",
        related_name="attempts",
    )
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_IN_PROGRESS,
    )

    class Meta:
        managed = False
        db_table = "attempts"

    def __str__(self):
        return f"Attempt {self.attempt_id} ({self.status})"


class UserAnswer(models.Model):
    answer_id = models.AutoField(primary_key=True)
    attempt = models.ForeignKey(
        Attempt,
        on_delete=models.CASCADE,
        db_column="attempt_id",
        related_name="answers",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        db_column="question_id",
        related_name="user_answers",
    )
    option = models.ForeignKey(
        AnswerOption,
        on_delete=models.CASCADE,
        db_column="option_id",
        related_name="user_answers",
    )

    class Meta:
        managed = False
        db_table = "user_answers"

    def __str__(self):
        return f"Answer {self.answer_id} (attempt {self.attempt_id})"
