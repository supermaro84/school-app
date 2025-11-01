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
    pub_date = models.DateTimeField("date published",auto_now_add=True)
    exp_date = models.DateTimeField("expiration date",null=True)

    title = models.CharField(max_length=200,default="Title")
    text = models.CharField(max_length=1500)
    groups = models.ManyToManyField(Group, related_name="announcements")
    users = models.ManyToManyField(User, related_name="announcements")


class AnnouncementComment(models.Model):
    announcement = models.ForeignKey(Announcement,related_name='comments', on_delete=models.CASCADE) #related_name helps to match announcement with this
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="announcement_comments"
    )
    comment_date = models.DateTimeField("published comment date",auto_now_add=True)
    text = models.CharField(max_length=500)
