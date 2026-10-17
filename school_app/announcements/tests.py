import tempfile
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from announcements.models import Announcement, AnnouncementImage, AnnouncementRead
from groups.models import GroupProfile
from media.tests import IN_MEMORY_STORAGES, image_upload
from media.utils import compress_image

CSV_HEADER = "author,title,text,groups,users,pub_date,exp_date\n"


class ImportAnnouncementsTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teacher")
        self.lucy = User.objects.create_user(username="lucy")
        self.group = GroupProfile.objects.create(group=Group.objects.create(name="Class 1A"))
        self.tmp = Path(tempfile.mkdtemp())

    def run_import(self, rows):
        csv_file = self.tmp / "announcements.csv"
        csv_file.write_text(CSV_HEADER + rows)
        call_command("import_announcements", str(csv_file), stdout=open("/dev/null", "w"))

    def test_creates_announcements_with_recipients_and_dates(self):
        self.run_import(
            'teacher,Leaf art,"<p>Bring a leaf, please</p>",Class 1A,lucy,2026-10-15 14:00,2026-10-19\n'
            "teacher,Public news,Hello,,,,\n"
        )
        leaf = Announcement.objects.get(title="Leaf art")
        public = Announcement.objects.get(title="Public news")

        self.assertEqual(leaf.author, self.teacher)
        self.assertEqual(leaf.text, "<p>Bring a leaf, please</p>")
        self.assertEqual(list(leaf.groups.all()), [self.group])
        self.assertEqual(list(leaf.users.all()), [self.lucy])
        self.assertEqual(leaf.pub_date.isoformat(), "2026-10-15T12:00:00+00:00")
        self.assertEqual(leaf.exp_date.date().isoformat(), "2026-10-19")
        self.assertFalse(public.groups.exists() or public.users.exists())
        self.assertIsNone(public.exp_date)

    def test_skips_existing_announcement_with_same_author_and_title(self):
        Announcement.objects.create(author=self.teacher, title="Leaf art", text="Old")
        self.run_import("teacher,Leaf art,New,,,,\n")
        self.assertEqual(Announcement.objects.get(title="Leaf art").text, "Old")

    def test_unknown_group_rolls_back_whole_import(self):
        with self.assertRaises(CommandError):
            self.run_import(
                "teacher,First,Text,Class 1A,,,\n"
                "teacher,Second,Text,Class 9Z,,,\n"
            )
        self.assertFalse(Announcement.objects.exists())


class AnnouncementReadStatusTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teacher")
        self.lucy = User.objects.create_user(username="lucy", password="pw")
        self.max = User.objects.create_user(username="max", password="pw")
        self.announcement = Announcement.objects.create(
            author=self.teacher, title="Leaf art", text="Bring a leaf"
        )
        self.announcement.users.add(self.lucy, self.max)
        self.client.force_login(self.lucy)

    def card(self, url):
        cards = self.client.get(url).context["announcements_data"]
        return next(c for c in cards if c["announcement"] == self.announcement)

    def test_card_is_new_until_opened(self):
        response = self.client.get(reverse("announcements_page"))
        self.assertFalse(response.context["announcements_data"][0]["opened"])
        self.assertContains(response, "New")

    def test_opening_detail_marks_it_opened_on_the_same_page(self):
        url = reverse("announcement_detail", args=[self.announcement.pk])
        self.assertTrue(self.card(url)["opened"])
        self.assertTrue(self.card(reverse("announcements_page"))["opened"])
        self.client.get(url)
        self.assertEqual(AnnouncementRead.objects.count(), 1)

    def test_status_is_per_user(self):
        self.client.get(reverse("announcement_detail", args=[self.announcement.pk]))
        self.client.force_login(self.max)
        self.assertFalse(self.card(reverse("announcements_page"))["opened"])

    def test_author_sees_own_announcement_as_opened(self):
        self.client.force_login(self.teacher)
        self.assertTrue(self.card(reverse("announcements_page"))["opened"])


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class AnnouncementImageTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teacher", password="pw")
        self.lucy = User.objects.create_user(username="lucy", password="pw")
        self.client.force_login(self.teacher)

    def post_data(self, **extra):
        return {"title": "Trip photos", "text": "<p>Look!</p>", "users": [self.lucy.pk], **extra}

    def test_create_with_several_images_compresses_them(self):
        response = self.client.post(
            reverse("announcement_create"),
            self.post_data(images=[image_upload("a.png", size=(3000, 2000)), image_upload("b.png")]),
        )
        announcement = Announcement.objects.get(title="Trip photos")
        self.assertRedirects(response, reverse("announcement_detail", args=[announcement.pk]))
        names = sorted(img.file.name for img in announcement.images.all())
        self.assertEqual(names, [f"announcements/teacher/{announcement.pk}/a.jpg", f"announcements/teacher/{announcement.pk}/b.jpg"])
        self.assertEqual(announcement.images.get(file__endswith="a.jpg").file.width, 1920)

        response = self.client.get(reverse("announcement_detail", args=[announcement.pk]))
        self.assertContains(response, 'class="img-thumbnail', count=2)

    def test_non_image_is_rejected_and_nothing_is_saved(self):
        bad = SimpleUploadedFile("notes.txt", b"text", content_type="text/plain")
        response = self.client.post(reverse("announcement_create"), self.post_data(images=[bad]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["images"])
        self.assertFalse(Announcement.objects.exists())

    def test_edit_adds_and_removes_images(self):
        announcement = Announcement.objects.create(author=self.teacher, title="Trip photos", text="x")
        announcement.users.add(self.lucy)
        old = AnnouncementImage.objects.create(announcement=announcement, file=compress_image(image_upload("old.png")))
        self.client.post(
            reverse("announcement_edit", args=[announcement.pk]),
            self.post_data(remove_images=[old.pk], images=[image_upload("new.png")]),
        )
        self.assertEqual([img.file.name for img in announcement.images.all()], [f"announcements/teacher/{announcement.pk}/new.jpg"])
        self.assertFalse(default_storage.exists(old.file.name))

    def test_deleting_announcement_deletes_files(self):
        announcement = Announcement.objects.create(author=self.teacher, title="Trip photos", text="x")
        image = AnnouncementImage.objects.create(announcement=announcement, file=compress_image(image_upload()))
        self.assertTrue(default_storage.exists(image.file.name))
        announcement.delete()
        self.assertFalse(default_storage.exists(image.file.name))


class AnnouncementRecipientsTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teacher", password="pw")
        self.lucy = User.objects.create_user(username="lucy", password="pw")
        self.group = GroupProfile.objects.create(group=Group.objects.create(name="Class 1A"))
        self.client.force_login(self.teacher)

    def create(self, **recipients):
        return self.client.post(reverse("announcement_create"), {"title": "Trip", "text": "<p>x</p>", **recipients})

    def test_groups_alone_are_enough(self):
        self.create(groups=[self.group.pk])
        announcement = Announcement.objects.get(title="Trip")
        self.assertEqual(list(announcement.groups.all()), [self.group])
        self.assertFalse(announcement.users.exists())

    def test_users_alone_are_enough(self):
        self.create(users=[self.lucy.pk])
        self.assertEqual(list(Announcement.objects.get(title="Trip").users.all()), [self.lucy])

    def test_needs_groups_or_users(self):
        response = self.create()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select at least one group or user.")
        self.assertFalse(Announcement.objects.exists())
