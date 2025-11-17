from .models import Message,MessageThread
from django import forms



class MessageThreadForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label="Message text",
        required=True
    )
    title = forms.CharField(max_length=150, required=True, label="Message Title")
    class Meta:
        model = MessageThread
        fields = ['title', 'recipients']