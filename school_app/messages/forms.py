from .models import Message, MessageThread
from django import forms
from django.utils.translation import gettext_lazy as _


class MessageThreadForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}), label=_("Message text"), required=True
    )
    title = forms.CharField(max_length=150, required=True, label=_("Message title"))

    class Meta:
        model = MessageThread
        fields = ["title", "recipients"]
