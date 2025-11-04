from django import forms
from .models import Announcement,AnnouncementComment
from django.contrib.auth.models import Group

class AnnouncementForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # optional: renders as checkboxes
        required=False
    )
    exp_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    class Meta:
        model = Announcement
        fields = ['title', 'text', 'groups', 'users', 'exp_date']

class AnnouncementCommentForm(forms.ModelForm):
    class Meta:
        model = AnnouncementComment
        fields = ['text']
