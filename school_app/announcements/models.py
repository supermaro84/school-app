from django.db import models
from django.contrib.auth.models import Group, User


# Create your models here.
class Announcement(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="authored_announcements",
        null=True,
    )
    pub_date = models.DateTimeField("date published")
    text = models.CharField(max_length=1500)
    groups = models.ManyToManyField(Group, related_name="announcements")
    users = models.ManyToManyField(User, related_name="announcements")


class AnnouncementComment(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="announcement_comments"
    )
    comment_date = models.DateTimeField("published comment date")
    text = models.CharField(max_length=500)
