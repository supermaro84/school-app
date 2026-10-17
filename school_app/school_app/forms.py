from django import forms
from django.utils.translation import gettext_lazy as _


class GroupsOrUsersRequiredMixin:
    """Form mixin: the recipients can be groups, users or both, but not nothing."""

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("groups") and not cleaned.get("users"):
            raise forms.ValidationError(_("Select at least one group or user."))
        return cleaned
