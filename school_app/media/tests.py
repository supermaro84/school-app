from io import BytesIO

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from announcements.models import Announcement, AnnouncementImage
from media.models import ImageFile
from media.utils import MAX_IMAGE_SIDE, compress_image
from messages.models import Message, MessageImage, MessageThread

# Tests that save files use this so nothing is uploaded to the real bucket.
IN_MEMORY_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


def image_upload(name="photo.png", size=(100, 80), mode="RGB", color="red", fmt="PNG", exif=None):
    buffer = BytesIO()
    kwargs = {"exif": exif} if exif is not None else {}
    Image.new(mode, size, color).save(buffer, format=fmt, **kwargs)
    content_type = "image/png" if fmt == "PNG" else "image/jpeg"
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


class CompressImageTests(TestCase):
    def open(self, content_file):
        return Image.open(BytesIO(content_file.read()))

    def test_large_image_is_scaled_down_to_jpeg(self):
        result = compress_image(image_upload("big.png", size=(4000, 3000)))
        self.assertEqual(result.name, "big.jpg")
        image = self.open(result)
        self.assertEqual(image.format, "JPEG")
        self.assertEqual(image.size, (MAX_IMAGE_SIDE, 1440))

    def test_small_image_keeps_its_size(self):
        image = self.open(compress_image(image_upload(size=(300, 200))))
        self.assertEqual(image.size, (300, 200))

    def test_transparency_becomes_white(self):
        upload = image_upload(mode="RGBA", color=(0, 0, 0, 0))
        image = self.open(compress_image(upload))
        self.assertEqual(image.mode, "RGB")
        r, g, b = image.getpixel((10, 10))
        self.assertTrue(min(r, g, b) > 245)

    def test_rotates_upright_and_strips_metadata(self):
        exif = Image.Exif()
        exif[0x0112] = 6  # orientation: rotate 90° clockwise to display
        exif[0x8825] = {2: (59.0, 54.0, 0.0)}  # GPS latitude
        upload = image_upload("phone.jpg", size=(200, 100), fmt="JPEG", exif=exif)
        image = self.open(compress_image(upload))
        self.assertEqual(image.size, (100, 200))
        self.assertEqual(len(image.getexif()), 0)

    def test_non_image_is_rejected(self):
        upload = SimpleUploadedFile("notes.txt", b"just text", content_type="text/plain")
        with self.assertRaises(ValidationError):
            compress_image(upload)


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class MyImagesTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teacher", password="pw")
        self.other = User.objects.create_user(username="other", password="pw")
        self.announcement = Announcement.objects.create(author=self.teacher, title="Trip", text="x")
        self.thread = MessageThread.objects.create(title="Forms", author=self.teacher)
        message = Message.objects.create(thread=self.thread, sender=self.teacher, text="See")
        self.gallery = ImageFile.objects.create(owner=self.teacher, file=compress_image(image_upload("g.png")))
        self.ann_image = AnnouncementImage.objects.create(
            announcement=self.announcement, file=compress_image(image_upload("a.png"))
        )
        self.msg_image = MessageImage.objects.create(message=message, file=compress_image(image_upload("m.png")))
        # Someone else's images must not show up.
        ImageFile.objects.create(owner=self.other, file=compress_image(image_upload("x.png")))
        other_ann = Announcement.objects.create(author=self.other, title="Other", text="x")
        AnnouncementImage.objects.create(announcement=other_ann, file=compress_image(image_upload("y.png")))
        self.client.force_login(self.teacher)

    def test_lists_only_own_images_with_where_they_are_posted(self):
        response = self.client.get(reverse("images_list"))
        items = response.context["my_images"]
        self.assertEqual(
            {(item["source"], item["image"].pk) for item in items},
            {("gallery", self.gallery.pk), ("announcement", self.ann_image.pk), ("message", self.msg_image.pk)},
        )
        self.assertContains(response, reverse("announcement_detail", args=[self.announcement.pk]))
        self.assertContains(response, reverse("message_thread_detail", args=[self.thread.pk]))
        self.assertContains(response, reverse("image_delete", args=["message", self.msg_image.pk]))

    def test_delete_removes_image_and_file(self):
        for source, image in [("gallery", self.gallery), ("announcement", self.ann_image), ("message", self.msg_image)]:
            response = self.client.post(reverse("image_delete", args=[source, image.pk]))
            self.assertRedirects(response, reverse("images_list"), fetch_redirect_response=False)
            self.assertFalse(type(image).objects.filter(pk=image.pk).exists())
            self.assertFalse(default_storage.exists(image.file.name))
        self.assertContains(self.client.get(reverse("images_list")), "Image deleted.")

    def test_cannot_delete_someone_elses_image(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse("image_delete", args=["announcement", self.ann_image.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(AnnouncementImage.objects.filter(pk=self.ann_image.pk).exists())

    def test_delete_needs_post_and_known_source(self):
        self.assertEqual(self.client.get(reverse("image_delete", args=["gallery", self.gallery.pk])).status_code, 405)
        self.assertEqual(self.client.post(reverse("image_delete", args=["bogus", self.gallery.pk])).status_code, 404)

    def test_upload_sets_owner_and_compresses(self):
        self.client.post(reverse("images_list"), {"file": image_upload("new.png", size=(3000, 1500))})
        image = ImageFile.objects.get(file__endswith="new.jpg")
        self.assertEqual(image.owner, self.teacher)
        self.assertEqual(image.file.name, "images/teacher/new.jpg")
        self.assertEqual(image.file.width, MAX_IMAGE_SIDE)

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("images_list")).status_code, 302)
