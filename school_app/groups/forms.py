from django import forms
from django.utils.translation import gettext_lazy as _
from .models import GroupProfile, Group
from groups.models import GroupProfile
from school_app.forms import UserChoiceLabelsMixin


class GroupForm(UserChoiceLabelsMixin, forms.ModelForm):
    name = forms.CharField(max_length=150, required=True, label=_("Group name"))
    source_groups = forms.ModelMultipleChoiceField(
        queryset=GroupProfile.objects.select_related("group").order_by("group__name"),
        required=False,
        label=_("Add members from groups"),
    )

    class Meta:
        model = GroupProfile
        fields = ["name", "description", "admins", "members"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if Group.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError(_("A group with this name already exists."))
        return name

    def new_members(self):
        """Chosen members plus everyone in the chosen groups, without duplicates."""
        people = set(self.cleaned_data.get("members") or [])
        for source in self.cleaned_data.get("source_groups") or []:
            people.update(source.admins.all())
            people.update(source.members.all())
        return people


class GroupEditForm(UserChoiceLabelsMixin, forms.ModelForm):
    class Meta:
        model = GroupProfile
        fields = ["description", "admins", "members"]

    def clean_admins(self):
        admins = self.cleaned_data.get("admins")
        # Without an admin nobody could manage the group any more.
        if not admins:
            raise forms.ValidationError(_("A group needs at least one admin."))
        return admins
