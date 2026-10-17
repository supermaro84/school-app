from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from groups.models import GroupProfile
from django_ckeditor_5.fields import CKEditor5Field



# Create your models here.
class Announcement(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="authored_announcements",
        null=True,
    )
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    exp_date = models.DateTimeField("expiration date", null=True)

    title = models.CharField(max_length=200, default="Title")
    text = CKEditor5Field('Text', config_name='extends')
    groups = models.ManyToManyField(GroupProfile, related_name="announcements")
    users = models.ManyToManyField(User, related_name="announcements")

    @property
    def all_users(self):
        return set(
            list(self.users.all())
            + [user for g in self.groups.all() for user in g.all_members]+ [self.author]
        )


class AnnouncementRead(models.Model):
    """Records that a user opened an announcement's detail page."""

    announcement = models.ForeignKey(
        Announcement, related_name="reads", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, related_name="announcement_reads", on_delete=models.CASCADE
    )
    read_at = models.DateTimeField("first opened", auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["announcement", "user"], name="unique_announcement_read"
            )
        ]


class AnnouncementComment(models.Model):
    announcement = models.ForeignKey(
        Announcement, related_name="comments", on_delete=models.CASCADE
    )  # related_name helps to match announcement with this
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="announcement_comments"
    )
    comment_date = models.DateTimeField("published comment date", auto_now_add=True)
    text = models.CharField(_("comment"), max_length=500)
