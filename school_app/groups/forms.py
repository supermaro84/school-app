from django import forms
from django.utils.translation import gettext_lazy as _
from .models import GroupProfile, Group
from groups.models import GroupProfile


class GroupForm(forms.ModelForm):
    name = forms.CharField(max_length=150, required=True, label=_("Group name"))

    class Meta:
        model = GroupProfile
        fields = ["name", "description", "admins", "members"]


class GroupEditForm(forms.ModelForm):
    class Meta:
        model = GroupProfile
        fields = ["description", "admins", "members"]

    def clean_admins(self):
        admins = self.cleaned_data.get("admins")
        # Without an admin nobody could manage the group any more.
        if not admins:
            raise forms.ValidationError(_("A group needs at least one admin."))
        return admins
