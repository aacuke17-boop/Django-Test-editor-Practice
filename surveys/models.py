from django.conf import settings
from django.db import models


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