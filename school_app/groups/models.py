from django.contrib.auth.models import Group, User
from django.db import models

class GroupProfile(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="profile")
    description = models.TextField(blank=True)
    admins = models.ManyToManyField(User, related_name="administered_groups", blank=True)
    members = models.ManyToManyField(User, related_name="member_groups", blank=True)

    def __str__(self):
        return self.group.name