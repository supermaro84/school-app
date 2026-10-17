from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import UserProfile
from groups.models import GroupProfile


# Create your models here.
class EventType(models.Model):
    name = models.CharField(max_length=100, default="Misc")

    def __str__(self):
        return self.name


class EventStatus(models.Model):
    name = models.CharField(max_length=100, default="Active")

    def __str__(self):
        return self.name


class EventParticipation(models.Model):
    participant = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="event_participant",
    )
    invited = models.BooleanField(default=True)
    accepted = models.BooleanField(default=True)
    decline_reason = models.CharField(max_length=100)


class Event(models.Model):
    owner = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="owned_events",
    )
    event_name = models.CharField(_("event name"), max_length=200, default="Event")
    event_description = models.TextField(_("description"), default="Event Description")
    event_type = models.ForeignKey(EventType, on_delete=models.CASCADE, verbose_name=_("type"))
    event_start_time = models.DateTimeField(_("event start time"))
    event_end_time = models.DateTimeField(_("event end time"))
    # Either may be empty; forms require at least one of them.
    groups = models.ManyToManyField(GroupProfile, related_name="events", verbose_name=_("groups"), blank=True)
    users = models.ManyToManyField(UserProfile, related_name="events", verbose_name=_("users"), blank=True)
    status = models.ForeignKey(EventStatus, on_delete=models.CASCADE, verbose_name=_("status"))
    participations = models.ManyToManyField(EventParticipation, related_name="events")

    @property
    def list_of_groups(self):
        return ", ".join([group.group.name for group in self.groups.all()])
    @property
    def all_involved_users(self):
        return set(
            list(user.user for user in self.users.all())
            + 
            [user for g in self.groups.all() for user in g.all_members]
        )

    def __str__(self):
        return self.event_name
