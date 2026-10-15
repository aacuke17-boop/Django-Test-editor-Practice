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