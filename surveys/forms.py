from django import forms

from .models import Questionnaire


class QuestionnaireForm(forms.ModelForm):
    class Meta:
        model = Questionnaire
        fields = ["title", "description", "is_test", "restricted_access"]
        labels = {
            "is_test": "This is a test (with points and correct answers)",
            "restricted_access": "Restricted access (only me and users I grant access to)",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "cols": 60}),
        }
