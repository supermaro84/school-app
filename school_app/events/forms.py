from django import forms
from .models import Event
from django.contrib.auth.models import Group, User
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from school_app.forms import GroupsOrUsersRequiredMixin
from media.forms import MultipleDocumentField
from .models import EventDocument


DATETIME_LOCAL = "%Y-%m-%dT%H:%M"  # value format of <input type="datetime-local">


def datetime_field(label):
    return forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"}, format=DATETIME_LOCAL
        ),
        input_formats=[DATETIME_LOCAL],
        label=label,
    )


EVENT_WIDGETS = {
    "event_name": forms.TextInput(attrs={"class": "form-control"}),
    "event_description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    "users": forms.SelectMultiple(attrs={"class": "event-users-select"}),
    "status": forms.Select(attrs={"class": "form-select"}),
    "event_type": forms.Select(attrs={"class": "form-select"}),
    "groups": forms.SelectMultiple(attrs={"class": "event-groups-select"}),
}


class EventForm(GroupsOrUsersRequiredMixin, forms.ModelForm):
    event_start_time = datetime_field(_("Start time"))
    documents = MultipleDocumentField()
    # Separate hour and minute fields for better UX
    duration_hours = forms.IntegerField(
        min_value=0,
        max_value=23,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    duration_minutes = forms.IntegerField(
        min_value=0,
        max_value=59,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Event
        fields = [
            "event_name",
            "event_start_time",
            "users",
            "status",
            "event_type",
            "groups",
            "event_description",
        ]
        widgets = EVENT_WIDGETS
    
    def save(self, commit=True):
        event = super().save(commit=False)
        hours = self.cleaned_data.get("duration_hours", 1)
        minutes = self.cleaned_data.get("duration_minutes", 0)
        duration = timedelta(hours=hours, minutes=minutes)
        event.event_end_time = event.event_start_time + duration
        #if commit:
        #    event.save()
        #    users = list(self.cleaned_data["users"])
        #    print(f"USERS BEFORE: {users}")
        #    if hasattr(self, 'owner') and self.owner:
        #        users.append(self.owner)
        #    print(f"USERS AFTER: {users}")
        #    event.users.set(users)
        #    users=self.cleaned_data["users"]
        #    print(f"USERS BEFORE: {users}")
        #    if hasattr(self, 'owner') and self.owner:
        #        users.append(self.owner)
        #    print(f"USERS AFTER: {users}")
        #    event.users.set(users)
        #    self.save_m2m()
        return event


class EventEditForm(GroupsOrUsersRequiredMixin, forms.ModelForm):
    """Edit every part of an existing event; start and end are set directly."""

    event_start_time = datetime_field(_("Start time"))
    event_end_time = datetime_field(_("End time"))
    documents = MultipleDocumentField()
    remove_documents = forms.ModelMultipleChoiceField(
        queryset=EventDocument.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Remove documents"),
    )

    class Meta:
        model = Event
        fields = [
            "event_name",
            "event_description",
            "event_type",
            "status",
            "event_start_time",
            "event_end_time",
            "groups",
            "users",
        ]
        widgets = EVENT_WIDGETS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["remove_documents"].queryset = self.instance.documents.all()

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("event_start_time"), cleaned.get("event_end_time")
        if start and end and end <= start:
            self.add_error("event_end_time", _("The end must be after the start."))
        return cleaned

