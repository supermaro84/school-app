from django import forms
from .models import Event
from django.contrib.auth.models import Group, User

class EventForm(forms.ModelForm):
    event_start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    event_end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    
    class Meta:
        model = Event
        fields = ['event_name', 'event_start_time', 'event_end_time', 'users','status','event_type','groups']
        widgets = {
            'users': forms.SelectMultiple(attrs={'class': 'form-control form-control-sm'}),  # Multi-select dropdown
            'status': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'event_type': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'groups': forms.SelectMultiple(attrs={'class': 'form-control form-control-sm'}),
        }
