from io import BytesIO
from unittest import mock

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from announcements.models import Announcement, AnnouncementDocument, AnnouncementImage
from groups.models import GroupProfile
from media.models import Gallery, GalleryImage, ImageFile
from media.utils import MAX_IMAGE_SIDE, compress_image
from messages.models import Message, MessageDocument, MessageImage, MessageThread

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
            {("upload", self.gallery.pk), ("announcement", self.ann_image.pk), ("message", self.msg_image.pk)},
        )
        self.assertContains(response, reverse("announcement_detail", args=[self.announcement.pk]))
        self.assertContains(response, reverse("message_thread_detail", args=[self.thread.pk]))
        self.assertContains(response, reverse("image_delete", args=["message", self.msg_image.pk]))

    def test_delete_removes_image_and_file(self):
        for source, image in [("upload", self.gallery), ("announcement", self.ann_image), ("message", self.msg_image)]:
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
        self.assertEqual(self.client.get(reverse("image_delete", args=["upload", self.gallery.pk])).status_code, 405)
        self.assertEqual(self.client.post(reverse("image_delete", args=["bogus", self.gallery.pk])).status_code, 404)

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("images_list")).status_code, 302)


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class GalleryTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teacher", password="pw")
        self.student = User.objects.create_user(username="student", password="pw")
        self.classmate = User.objects.create_user(username="classmate", password="pw")
        self.parent = User.objects.create_user(username="parent", password="pw")
        self.stranger = User.objects.create_user(username="stranger", password="pw")
        self.parent.profile.affiliated_users.add(self.student)
        self.group = GroupProfile.objects.create(group=Group.objects.create(name="Class 1A"))
        self.group.members.add(self.classmate)
        self.gallery = Gallery.objects.create(owner=self.teacher, name="Trip", description="Zoo day")
        self.gallery.users.add(self.student)
        self.gallery.groups.add(self.group)
        self.client.force_login(self.teacher)

    def upload(self, user, *names):
        self.client.force_login(user)
        return self.client.post(
            reverse("gallery_detail", args=[self.gallery.pk]), {"images": [image_upload(n) for n in names]}
        )

    def test_create_gallery_with_optional_sharing(self):
        response = self.client.post(reverse("gallery_create"), {"name": "Private", "description": ""})
        gallery = Gallery.objects.get(name="Private")
        self.assertRedirects(response, reverse("gallery_detail", args=[gallery.pk]))
        self.assertEqual(gallery.owner, self.teacher)
        self.assertFalse(gallery.users.exists() or gallery.groups.exists())
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("gallery_detail", args=[gallery.pk])).status_code, 404)

    def test_who_can_see_a_shared_gallery(self):
        for user in (self.teacher, self.student, self.classmate, self.parent):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse("gallery_detail", args=[self.gallery.pk])).status_code, 200, user)
            self.assertIn(self.gallery, self.client.get(reverse("images_list")).context["galleries"], user)
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(reverse("gallery_detail", args=[self.gallery.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("images_list")).context["galleries"], [])

    def test_guardian_sees_which_child_it_is_shared_with(self):
        self.client.force_login(self.parent)
        gallery = self.client.get(reverse("images_list")).context["galleries"][0]
        self.assertEqual(gallery.connected_users, [self.student])

    def test_filter_mine_and_shared(self):
        mine = self.client.get(reverse("images_list") + "?show=mine").context["galleries"]
        shared = self.client.get(reverse("images_list") + "?show=shared").context["galleries"]
        self.assertEqual((mine, shared), ([self.gallery], []))
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("images_list") + "?show=shared").context["galleries"], [self.gallery])

    def test_owner_and_recipients_can_upload(self):
        self.upload(self.teacher, "owner.png")
        self.upload(self.student, "student.png")
        self.upload(self.classmate, "classmate.png", "second.png")
        names = sorted(image.file.name for image in self.gallery.images.all())
        g = self.gallery.pk
        self.assertEqual(names, sorted([
            f"galleries/teacher/{g}/owner.jpg", f"galleries/student/{g}/student.jpg",
            f"galleries/classmate/{g}/classmate.jpg", f"galleries/classmate/{g}/second.jpg",
        ]))

    def test_guardian_and_stranger_cannot_upload(self):
        self.assertEqual(self.upload(self.parent, "p.png").status_code, 403)
        self.assertEqual(self.upload(self.stranger, "s.png").status_code, 404)
        self.assertFalse(self.gallery.images.exists())

    def test_upload_form_only_for_uploaders(self):
        self.assertContains(self.client.get(reverse("gallery_detail", args=[self.gallery.pk])), 'name="images"')
        self.client.force_login(self.parent)
        self.assertNotContains(self.client.get(reverse("gallery_detail", args=[self.gallery.pk])), 'name="images"')

    def test_image_delete_rights(self):
        self.upload(self.student, "student.png")
        self.upload(self.classmate, "classmate.png")
        student_image = self.gallery.images.get(uploaded_by=self.student)
        classmate_image = self.gallery.images.get(uploaded_by=self.classmate)
        # A recipient can't delete someone else's image...
        self.client.force_login(self.classmate)
        self.assertEqual(self.client.post(reverse("image_delete", args=["gallery", student_image.pk])).status_code, 404)
        # ...but can delete their own, and comes back to the gallery.
        detail = reverse("gallery_detail", args=[self.gallery.pk])
        response = self.client.post(reverse("image_delete", args=["gallery", classmate_image.pk]), {"next": detail})
        self.assertRedirects(response, detail, fetch_redirect_response=False)
        # The owner can delete anyone's image.
        self.client.force_login(self.teacher)
        self.client.post(reverse("image_delete", args=["gallery", student_image.pk]))
        self.assertFalse(self.gallery.images.exists())
        self.assertFalse(default_storage.exists(student_image.file.name))

    def test_delete_redirect_ignores_other_sites(self):
        self.upload(self.teacher, "a.png")
        image = self.gallery.images.get()
        response = self.client.post(reverse("image_delete", args=["gallery", image.pk]), {"next": "https://evil.example/"})
        self.assertRedirects(response, reverse("images_list"), fetch_redirect_response=False)

    def test_only_owner_edits_and_deletes_gallery(self):
        data = {"name": "Zoo trip", "description": "New", "users": [self.classmate.pk]}
        for user in (self.student, self.parent):
            self.client.force_login(user)
            self.assertEqual(self.client.post(reverse("gallery_edit", args=[self.gallery.pk]), data).status_code, 404)
            self.assertEqual(self.client.post(reverse("gallery_delete", args=[self.gallery.pk])).status_code, 404)
        self.client.force_login(self.teacher)
        self.client.post(reverse("gallery_edit", args=[self.gallery.pk]), data)
        self.gallery.refresh_from_db()
        self.assertEqual(self.gallery.name, "Zoo trip")
        self.assertEqual(list(self.gallery.users.all()), [self.classmate])
        self.assertFalse(self.gallery.groups.exists())

    def test_deleting_gallery_deletes_images_and_files(self):
        self.upload(self.student, "a.png")
        image = self.gallery.images.get()
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("gallery_delete", args=[self.gallery.pk]))
        self.assertRedirects(response, reverse("images_list"), fetch_redirect_response=False)
        self.assertFalse(GalleryImage.objects.exists())
        self.assertFalse(default_storage.exists(image.file.name))

    def test_gallery_images_appear_in_my_images(self):
        self.upload(self.student, "a.png")
        self.client.force_login(self.teacher)
        items = self.client.get(reverse("images_list")).context["my_images"]
        self.assertEqual(items, [])  # the owner didn't upload it
        self.client.force_login(self.student)
        response = self.client.get(reverse("images_list"))
        [item] = response.context["my_images"]
        self.assertEqual((item["source"], item["post"]), ("gallery", self.gallery))
        self.assertContains(response, reverse("gallery_detail", args=[self.gallery.pk]))


def document_upload(name="plan.pdf", content=b"%PDF-1.4 test"):
    return SimpleUploadedFile(name, content, content_type="application/octet-stream")


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class DocumentTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teacher", password="pw")
        self.student = User.objects.create_user(username="student", password="pw")
        self.parent = User.objects.create_user(username="parent", password="pw")
        self.stranger = User.objects.create_user(username="stranger", password="pw")
        self.parent.profile.affiliated_users.add(self.student)
        self.group = GroupProfile.objects.create(group=Group.objects.create(name="Class 1A"))
        self.group.members.add(self.student)
        self.client.force_login(self.teacher)

    def documents(self, user, query=""):
        self.client.force_login(user)
        return self.client.get(reverse("documents_page") + query).context["documents"]

    def test_field_accepts_documents_and_rejects_other_files(self):
        from media.forms import MultipleDocumentField
        field = MultipleDocumentField()
        self.assertEqual(len(field.clean([document_upload("a.pdf"), document_upload("b.DOCX")])), 2)
        with self.assertRaises(ValidationError):
            field.clean([document_upload("virus.exe")])
        with mock.patch("media.forms.MAX_DOCUMENT_SIZE", 5):
            with self.assertRaises(ValidationError):
                field.clean([document_upload("big.pdf", b"0123456789")])

    def test_announcement_documents(self):
        self.client.post(reverse("announcement_create"), {
            "title": "Trip", "text": "<p>x</p>", "groups": [self.group.pk],
            "documents": [document_upload("programme.pdf"), document_upload("list.xlsx")],
        })
        announcement = Announcement.objects.get(title="Trip")
        doc = announcement.documents.get(file__endswith="programme.pdf")
        self.assertEqual(doc.file.name, f"announcements/teacher/{announcement.pk}/programme.pdf")
        self.assertEqual(doc.file_size, len(b"%PDF-1.4 test"))
        self.assertContains(self.client.get(reverse("announcement_detail", args=[announcement.pk])), "programme.pdf")
        # Removing on edit deletes the file
        self.client.post(reverse("announcement_edit", args=[announcement.pk]), {
            "title": "Trip", "text": "<p>x</p>", "groups": [self.group.pk], "remove_documents": [doc.pk],
        })
        self.assertEqual(announcement.documents.count(), 1)
        self.assertFalse(default_storage.exists(doc.file.name))

    def test_message_and_event_documents(self):
        self.client.post(reverse("message_create"), {
            "title": "Forms", "recipients": [self.student.pk], "text": "See attached",
            "documents": [document_upload("consent.docx")],
        })
        thread = MessageThread.objects.get(title="Forms")
        self.assertContains(self.client.get(reverse("message_thread_detail", args=[thread.pk])), "consent.docx")

        from events.models import Event, EventStatus, EventType
        self.client.post(reverse("calendar"), {
            "event_name": "Meeting", "event_description": "x", "event_start_time": "2026-10-20T09:00",
            "duration_hours": 1, "duration_minutes": 0, "groups": [self.group.pk],
            "event_type": EventType.objects.create(name="Meeting").pk,
            "status": EventStatus.objects.create(name="Active").pk,
            "documents": [document_upload("agenda.pdf")],
        })
        event = Event.objects.get(event_name="Meeting")
        self.assertEqual(event.documents.get().file.name, f"events/teacher/{event.pk}/agenda.pdf")
        entry = self.client.get(reverse("events")).json()[0]
        self.assertEqual(entry["documents"][0]["name"], "agenda.pdf")

    def make_documents(self):
        announcement = Announcement.objects.create(author=self.teacher, title="Trip", text="x")
        announcement.groups.add(self.group)
        trip = AnnouncementDocument.objects.create(announcement=announcement, file=document_upload("trip.pdf"))
        thread = MessageThread.objects.create(title="Private", author=self.teacher)
        thread.recipients.add(self.stranger)
        message = Message.objects.create(thread=thread, sender=self.stranger, text="x")
        private = MessageDocument.objects.create(message=message, file=document_upload("private.pdf"))
        return trip, private

    def test_documents_page_lists_what_each_user_can_see(self):
        trip, private = self.make_documents()
        docs = lambda user: {item["document"] for item in self.documents(user)}
        self.assertEqual(docs(self.teacher), {trip, private})
        self.assertEqual(docs(self.student), {trip})
        self.assertEqual(docs(self.parent), {trip})  # through the child
        self.assertEqual(docs(self.stranger), {private})

    def test_mine_filter_and_delete_rights(self):
        doc, _ = self.make_documents()
        mine = [item["document"] for item in self.documents(self.teacher, "?show=mine")]
        self.assertEqual(mine, [doc])
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(reverse("document_delete", args=["announcement", doc.pk])).status_code, 404)
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(reverse("document_delete", args=["announcement", doc.pk])).status_code, 405)
        response = self.client.post(reverse("document_delete", args=["announcement", doc.pk]))
        self.assertRedirects(response, reverse("documents_page"), fetch_redirect_response=False)
        self.assertFalse(AnnouncementDocument.objects.exists())
        self.assertFalse(default_storage.exists(doc.file.name))

    def test_documents_menu_is_in_the_navbar(self):
        response = self.client.get(reverse("documents_page"))
        self.assertContains(response, f'class="nav-link active" href="{reverse("documents_page")}"')
        self.assertNotContains(self.client.get(reverse("images_list")), "bi-folder2-open")
