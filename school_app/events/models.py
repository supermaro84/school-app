from django.db import models
from django.contrib.auth.models import Group, User

# Create your models here.
class EventType(models.Model):
    name = models.CharField(max_length=100,default="Misc")
    def __str__(self):
        return self.name

class EventStatus(models.Model):
    name = models.CharField(max_length=100,default='Active')
    def __str__(self):
        return self.name

class EventParticipation(models.Model):
    participant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='event_participant',
    )
    invited = models.BooleanField(default=True)
    accepted = models.BooleanField(default=True)
    decline_reason = models.CharField(max_length=100)

class Event(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_events',
    )
    event_name = models.CharField(max_length=200,default="Event")
    event_description = models.TextField(default="Event Description")
    event_type = models.ForeignKey(EventType, on_delete=models.CASCADE)
    event_start_time = models.DateTimeField('event start time')
    event_end_time = models.DateTimeField('event end time')
    groups = models.ManyToManyField(Group, related_name="events")
    users = models.ManyToManyField(User, related_name="events")
    status = models.ForeignKey(EventStatus, on_delete=models.CASCADE)
    participations = models.ManyToManyField(EventParticipation, related_name="events")
    def __str__(self):
        return self.event_name


