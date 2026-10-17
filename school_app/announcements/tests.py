import tempfile
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from announcements.models import Announcement, AnnouncementRead
from groups.models import GroupProfile

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
