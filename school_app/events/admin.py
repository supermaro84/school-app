from django.contrib import admin
from .models import Event,EventType,EventStatus,EventParticipation
# Register your models here.
admin.site.register(Event)
admin.site.register(EventStatus)
admin.site.register(EventType)
admin.site.register(EventParticipation)