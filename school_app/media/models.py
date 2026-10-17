from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.signals import post_delete
from django.utils.translation import gettext_lazy as _
import os


# Create your models here.
def user_directory_path(instance, filename):
    # file will be uploaded to images/<username>/<filename>
    return f"images/{instance.owner.username}/{filename}"


class ImageFile(models.Model):
    owner = models.ForeignKey("auth.User", on_delete=models.CASCADE, default=1)
    file = models.ImageField(_("image"), upload_to=user_directory_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class DocumentFile(models.Model):
    owner = models.ForeignKey("auth.User", on_delete=models.CASCADE, default=1)
    file = models.FileField(upload_to="documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def file_extension(self):
        return os.path.splitext(self.file.name)[1]

    @property
    def file_size(self):
        if self.file:
            return self.file.size
        return 0


class AttachedImage(models.Model):
    """Base for compressed images attached to other content.

    Subclasses add a ForeignKey to what the image belongs to and define
    ``upload_to``; connect ``delete_attached_file`` to their post_delete.
    """

    file = models.ImageField(_("image"), upload_to="attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["pk"]


def delete_attached_file(sender, instance, **kwargs):
    # Remove the file from storage once its row is gone.
    if instance.file:
        instance.file.delete(save=False)


post_delete.connect(delete_attached_file, sender=ImageFile)
