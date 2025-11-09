from django import forms
from .models import Event
from django.contrib.auth.models import Group, User
from datetime import timedelta
class EventForm(forms.ModelForm):
    event_start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    # Separate hour and minute fields for better UX
    duration_hours = forms.IntegerField(
        min_value=0,
        max_value=23,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'style': 'width: 60px; display: inline-block;'
        })
    )
    
    duration_minutes = forms.IntegerField(
        min_value=0,
        max_value=59,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'style': 'width: 60px; display: inline-block;'
        })
    )
    
    
    class Meta:
        model = Event
        fields = ['event_name', 'event_start_time', 'users','status','event_type','groups','event_description']
        widgets = {
            'users': forms.SelectMultiple(attrs={'class': 'form-control form-control-sm'}),  # Multi-select dropdown
            'status': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'event_type': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'groups': forms.SelectMultiple(attrs={'class': 'form-control form-control-sm'}),
        }
    def save(self, commit=True):
        event = super().save(commit=False)
        hours = self.cleaned_data.get('duration_hours', 1)
        minutes = self.cleaned_data.get('duration_minutes', 0)
        duration = timedelta(hours=hours, minutes=minutes)

        event.event_end_time = event.event_start_time + duration
        print("this is not printed!")
        if commit:
            event.save()
            self.save_m2m()
        return event
