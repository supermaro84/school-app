from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone
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


class AttachedDocument(models.Model):
    """Base for documents (PDF, Office files, ...) attached to other content.

    Subclasses add a ForeignKey to what the document belongs to and an
    ``upload_to``; connect ``delete_attached_file`` to their post_delete.
    """

    file = models.FileField(_("document"), upload_to="attachments/", max_length=255)
    # Stored at upload so lists don't ask the storage for each file's size
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["pk"]

    def save(self, *args, **kwargs):
        if self.file and self.file_size is None:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def extension(self):
        return os.path.splitext(self.file.name)[1].lower().lstrip(".")



def delete_attached_file(sender, instance, **kwargs):
    # Remove the file from storage once its row is gone.
    if instance.file:
        instance.file.delete(save=False)


post_delete.connect(delete_attached_file, sender=ImageFile)


class Gallery(models.Model):
    """A named collection of images, shared with users and/or groups.

    Sharing is optional: an unshared gallery is visible to its owner only.
    """

    owner = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="galleries")
    name = models.CharField(_("name"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    users = models.ManyToManyField(
        "auth.User", related_name="shared_galleries", blank=True, verbose_name=_("users")
    )
    groups = models.ManyToManyField(
        "groups.GroupProfile", related_name="galleries", blank=True, verbose_name=_("groups")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # Changed on every save, including when images are added (see gallery_detail)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "updated_at" not in update_fields:
            kwargs["update_fields"] = [*update_fields, "updated_at"]
        super().save(*args, **kwargs)

    @property
    def recipients(self):
        """Users the gallery is shared with directly or through a group."""
        return set(self.users.all()) | {user for g in self.groups.all() for user in g.all_members}

    def can_upload(self, user):
        # Owner and recipients may add images; guardians who only see the
        # gallery through an affiliated child may not.
        return user == self.owner or user in self.recipients


def gallery_image_path(instance, filename):
    # galleries/<uploader username>/<gallery id>/<filename>
    return f"galleries/{instance.uploaded_by.username}/{instance.gallery_id}/{filename}"


class GalleryImage(AttachedImage):
    gallery = models.ForeignKey(Gallery, related_name="images", on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(
        "auth.User", related_name="gallery_images", on_delete=models.CASCADE
    )
    file = models.ImageField(_("image"), upload_to=gallery_image_path)

    class Meta(AttachedImage.Meta):
        pass


post_delete.connect(delete_attached_file, sender=GalleryImage)


class GalleryView(models.Model):
    """When a user last opened a gallery; a later update makes it new again."""

    gallery = models.ForeignKey(Gallery, related_name="views", on_delete=models.CASCADE)
    user = models.ForeignKey("auth.User", related_name="gallery_views", on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["gallery", "user"], name="unique_gallery_view")]

