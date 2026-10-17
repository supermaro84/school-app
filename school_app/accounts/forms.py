import re
from datetime import date

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import UserProfile

PHONE = re.compile(r"^[0-9+()\- ]*$")


class OwnUserForm(forms.ModelForm):
    """The account fields a user may change themselves."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True


class OwnProfileForm(forms.ModelForm):
    """The profile fields a user may change themselves; role and affiliations
    stay with the administrators."""

    class Meta:
        model = UserProfile
        fields = ["birthdate", "phone_number", "description"]
        labels = {"birthdate": _("Birthdate"), "phone_number": _("Phone")}
        widgets = {
            "birthdate": forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "autocomplete": "tel", "inputmode": "tel"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def clean_birthdate(self):
        birthdate = self.cleaned_data.get("birthdate")
        if birthdate and birthdate > date.today():
            raise forms.ValidationError(_("The birthdate can't be in the future."))
        return birthdate

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()
        if not PHONE.match(phone):
            raise forms.ValidationError(_("Use only digits, spaces and + - ( )."))
        return phone
