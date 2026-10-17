from .models import Message, MessageThread
from django import forms
from django.utils.translation import gettext_lazy as _
from media.forms import MultipleImageField


class MessageThreadForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}), label=_("Message text"), required=True
    )
    title = forms.CharField(max_length=150, required=True, label=_("Message title"))
    images = MultipleImageField()

    class Meta:
        model = MessageThread
        fields = ["title", "recipients"]


class MessageReplyForm(forms.ModelForm):
    images = MultipleImageField()

    class Meta:
        model = Message
        fields = ["text"]
