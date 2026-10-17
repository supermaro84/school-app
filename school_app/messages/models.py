from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from media.models import AttachedImage, delete_attached_file


class MessageThread(models.Model):
    title = models.CharField(max_length=200, default="Title")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="authored_messages",
        null=True,
    )
    recipients = models.ManyToManyField(
        User, related_name="massage_threads", verbose_name=_("recipients")
    )
    @property
    def all_recipients(self):
        return [self.author]+list(self.recipients.all())



# Create your models here.
class Message(models.Model):
    thread = models.ForeignKey(
        MessageThread, related_name="messages", on_delete=models.CASCADE
    )
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    text = models.CharField(_("message"), max_length=1500)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True)



def message_image_path(instance, filename):
    # messages/<sender username>/<thread id>/<filename>
    sender = instance.message.sender
    username = sender.username if sender else "unknown"
    return f"messages/{username}/{instance.message.thread_id}/{filename}"


class MessageImage(AttachedImage):
    message = models.ForeignKey(Message, related_name="images", on_delete=models.CASCADE)
    file = models.ImageField(_("image"), upload_to=message_image_path)

    class Meta(AttachedImage.Meta):
        pass


post_delete.connect(delete_attached_file, sender=MessageImage)
