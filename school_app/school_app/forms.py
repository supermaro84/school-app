from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from accounts.models import UserProfile


def user_label(user, role=None):
    """"Full Name (Role)" for user pickers; username if no name, no () without a role."""
    name = user.get_full_name() or user.username
    return f"{name} ({role})" if role else name


class UserChoiceLabelsMixin:
    """Form mixin: user pickers list "Full Name (Role)", sorted by name.

    Applies to every choice field over User or UserProfile in the form.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field, forms.ModelChoiceField):
                continue
            model = field.queryset.model
            if model is User:
                field.queryset = field.queryset.select_related("profile__user_role").order_by(
                    "first_name", "last_name", "username"
                )
                field.label_from_instance = lambda user: user_label(
                    user, getattr(getattr(user, "profile", None), "user_role", None)
                )
            elif model is UserProfile:
                field.queryset = field.queryset.select_related("user", "user_role").order_by(
                    "user__first_name", "user__last_name", "user__username"
                )
                field.label_from_instance = lambda profile: user_label(profile.user, profile.user_role)


class GroupsOrUsersRequiredMixin:
    """Form mixin: the recipients can be groups, users or both, but not nothing."""

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("groups") and not cleaned.get("users"):
            raise forms.ValidationError(_("Select at least one group or user."))
        return cleaned
