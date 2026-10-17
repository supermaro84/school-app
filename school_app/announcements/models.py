from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from groups.models import GroupProfile
from django_ckeditor_5.fields import CKEditor5Field
from django.db.models.signals import post_delete
from media.models import AttachedDocument, AttachedImage, delete_attached_file



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
    # Set when the author edits the announcement (used for "recent activity")
    updated_at = models.DateTimeField("last edited", null=True, blank=True)

    title = models.CharField(max_length=200, default="Title")
    text = CKEditor5Field('Text', config_name='extends')
    # Either may be empty; forms require at least one of them.
    groups = models.ManyToManyField(GroupProfile, related_name="announcements", blank=True)
    users = models.ManyToManyField(User, related_name="announcements", blank=True)

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
    # Updated on every visit; comments from others after it are new
    last_seen_at = models.DateTimeField("last opened", default=timezone.now)

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


def announcement_image_path(instance, filename):
    # announcements/<author username>/<announcement id>/<filename>
    author = instance.announcement.author
    username = author.username if author else "unknown"
    return f"announcements/{username}/{instance.announcement_id}/{filename}"


class AnnouncementImage(AttachedImage):
    announcement = models.ForeignKey(
        Announcement, related_name="images", on_delete=models.CASCADE
    )
    file = models.ImageField(_("image"), upload_to=announcement_image_path)

    class Meta(AttachedImage.Meta):
        pass


post_delete.connect(delete_attached_file, sender=AnnouncementImage)


class AnnouncementDocument(AttachedDocument):
    announcement = models.ForeignKey(
        Announcement, related_name="documents", on_delete=models.CASCADE
    )
    # Same folder as the announcement's images
    file = models.FileField(_("document"), upload_to=announcement_image_path, max_length=255)

    class Meta(AttachedDocument.Meta):
        pass


post_delete.connect(delete_attached_file, sender=AnnouncementDocument)
