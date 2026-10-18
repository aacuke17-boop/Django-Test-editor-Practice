from django import forms
from django.contrib.auth import get_user_model

from accounts.models import ANONYMOUS_EMAIL

from .models import Access, Questionnaire

User = get_user_model()


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


class GrantAccessForm(forms.Form):
    email = forms.EmailField(max_length=254, label="User email")

    def __init__(self, material, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.material = material
        self.user = None

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        user = User.objects.filter(email__iexact=email).first()
        if user is None or user.email == ANONYMOUS_EMAIL:
            raise forms.ValidationError("No registered user with this email.")
        if user.pk == self.material.creator_id:
            raise forms.ValidationError("You are the author of this material and already have access.")
        if Access.objects.filter(form=self.material, user=user).exists():
            raise forms.ValidationError("This user already has access.")
        self.user = user
        return email