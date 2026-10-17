import tempfile
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import CommandError
from datetime import datetime, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event, EventStatus, EventType
from groups.models import GroupProfile

CSV_HEADER = "kind,name\n"


class ImportEventOptionsTests(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def run_import(self, rows):
        csv_file = self.tmp / "event_options.csv"
        csv_file.write_text(CSV_HEADER + rows)
        call_command("import_event_options", str(csv_file), stdout=open("/dev/null", "w"))

    def names(self, model):
        return sorted(model.objects.values_list("name", flat=True))

    def test_creates_types_and_statuses(self):
        self.run_import("type,Academic\ntype,Social\nstatus,Active\n")
        self.assertEqual(self.names(EventType), ["Academic", "Social"])
        self.assertEqual(self.names(EventStatus), ["Active"])

    def test_skips_existing_names(self):
        EventType.objects.create(name="Academic")
        self.run_import("type,academic\ntype,Social\n")
        self.assertEqual(self.names(EventType), ["Academic", "Social"])

    def test_unknown_kind_rolls_back_whole_import(self):
        with self.assertRaises(CommandError):
            self.run_import("type,Academic\ncolour,Red\n")
        self.assertFalse(EventType.objects.exists())


EVENTS_HEADER = "owner,name,description,type,status,start,end,groups,users,repeat_weekly_until\n"


class ImportEventsTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teacher")
        self.lucy = User.objects.create_user(username="lucy")
        self.group = GroupProfile.objects.create(group=Group.objects.create(name="Class 1A"))
        EventType.objects.create(name="Lesson")
        EventStatus.objects.create(name="Active")
        self.tmp = Path(tempfile.mkdtemp())

    def run_import(self, rows):
        csv_file = self.tmp / "events.csv"
        csv_file.write_text(EVENTS_HEADER + rows)
        call_command("import_events", str(csv_file), stdout=open("/dev/null", "w"))

    def test_creates_event_with_owner_groups_and_users(self):
        self.run_import(
            "teacher,Maths 1A,Numbers,Lesson,Active,2026-10-19 08:00,2026-10-19 08:45,Class 1A,lucy,\n"
        )
        event = Event.objects.get()
        self.assertEqual(event.owner.user, self.teacher)
        self.assertEqual(event.event_type.name, "Lesson")
        self.assertEqual(list(event.groups.all()), [self.group])
        self.assertEqual(
            sorted(event.users.values_list("user__username", flat=True)), ["lucy", "teacher"]
        )

    def test_repeats_weekly_and_keeps_local_time_across_dst(self):
        # Europe/Oslo switches from summer to winter time on 25 October 2026
        self.run_import(
            "teacher,Maths 1A,,Lesson,Active,2026-10-19 08:00,2026-10-19 08:45,Class 1A,,2026-11-02\n"
        )
        starts = [
            timezone.localtime(e.event_start_time).strftime("%Y-%m-%d %H:%M")
            for e in Event.objects.order_by("event_start_time")
        ]
        self.assertEqual(starts, ["2026-10-19 08:00", "2026-10-26 08:00", "2026-11-02 08:00"])

    def test_skips_existing_events(self):
        row = "teacher,Maths 1A,,Lesson,Active,2026-10-19 08:00,2026-10-19 08:45,,,\n"
        self.run_import(row)
        self.run_import(row)
        self.assertEqual(Event.objects.count(), 1)

    def test_invalid_row_rolls_back_whole_import(self):
        with self.assertRaises(CommandError):
            self.run_import(
                "teacher,Maths 1A,,Lesson,Active,2026-10-19 08:00,2026-10-19 08:45,,,\n"
                "teacher,Trip,,Excursion,Active,2026-10-20 08:00,2026-10-20 12:00,,,\n"
            )
        self.assertFalse(Event.objects.exists())


class EventsFeedTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(username="parent", password="pw")
        self.child = User.objects.create_user(username="child", password="pw")
        self.stranger = User.objects.create_user(username="stranger", password="pw")
        self.parent.profile.affiliated_users.add(self.child)
        self.group = GroupProfile.objects.create(group=Group.objects.create(name="Class 1A"))
        self.group.members.add(self.child)
        self.type = EventType.objects.create(name="Lesson")
        self.status = EventStatus.objects.create(name="Active")
        self.client.force_login(self.parent)

    def make_event(self, name, day, groups=(), users=()):
        start = timezone.make_aware(datetime(2026, 10, day, 9, 0))
        event = Event.objects.create(
            owner=self.stranger.profile, event_name=name, event_type=self.type, status=self.status,
            event_start_time=start, event_end_time=start + timedelta(hours=1),
        )
        event.groups.add(*groups)
        event.users.add(*users)
        return event

    def feed(self, query=""):
        return self.client.get(reverse("events") + query).json()

    def test_returns_events_of_user_and_affiliates_only(self):
        self.make_event("Class trip", 5, groups=[self.group])
        self.make_event("Meeting", 6, users=[self.parent.profile, self.child.profile])
        self.make_event("Not ours", 7, users=[self.stranger.profile])
        titles = sorted(e["title"] for e in self.feed())
        # One entry per involved person, as before.
        self.assertEqual(titles, ["Class trip (child) ", "Meeting (child) ", "Meeting (parent) "])

    def test_only_events_in_requested_range(self):
        self.make_event("Early", 1, groups=[self.group])
        self.make_event("Inside", 15, groups=[self.group])
        self.make_event("Late", 30, groups=[self.group])
        query = "?start=2026-10-10T00:00:00%2B02:00&end=2026-10-20T00:00:00%2B02:00"
        self.assertEqual([e["title"] for e in self.feed(query)], ["Inside (child) "])
        # Date-only values, as FullCalendar may send them, work too.
        self.assertEqual(len(self.feed("?start=2026-10-10&end=2026-10-20")), 1)

    def test_query_count_does_not_grow_with_events(self):
        for day in range(1, 21):
            self.make_event(f"Lesson {day}", day, groups=[self.group], users=[self.parent.profile])
        with self.assertNumQueries(10):
            self.assertEqual(len(self.feed()), 40)

    def test_anonymous_gets_empty_list(self):
        self.client.logout()
        self.assertEqual(self.feed(), [])


class EventEditTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="author", password="pw")
        self.other = User.objects.create_user(username="other", password="pw")
        self.lucy = User.objects.create_user(username="lucy", password="pw")
        self.class_a = GroupProfile.objects.create(group=Group.objects.create(name="Class 1A"))
        self.class_b = GroupProfile.objects.create(group=Group.objects.create(name="Class 2B"))
        self.lesson = EventType.objects.create(name="Lesson")
        self.trip = EventType.objects.create(name="Trip")
        self.active = EventStatus.objects.create(name="Active")
        self.cancelled = EventStatus.objects.create(name="Cancelled")
        start = timezone.make_aware(datetime(2026, 10, 20, 9, 0))
        self.event = Event.objects.create(
            owner=self.author.profile, event_name="Maths", event_description="Fractions",
            event_type=self.lesson, status=self.active,
            event_start_time=start, event_end_time=start + timedelta(hours=1),
        )
        self.event.groups.add(self.class_a)
        self.event.users.add(self.author.profile)
        self.client.force_login(self.author)

    def edit_data(self, **changes):
        data = {
            "event_name": "Museum trip", "event_description": "Bring lunch",
            "event_type": self.trip.pk, "status": self.cancelled.pk,
            "event_start_time": "2026-10-22T08:30", "event_end_time": "2026-10-23T14:00",
            "groups": [self.class_b.pk], "users": [self.lucy.profile.pk],
        }
        data.update(changes)
        return data

    def test_edit_page_is_prefilled(self):
        response = self.client.get(reverse("event_edit", args=[self.event.pk]))
        self.assertContains(response, 'value="Maths"')
        self.assertContains(response, 'value="2026-10-20T09:00"')
        self.assertContains(response, 'value="2026-10-20T10:00"')

    def test_author_can_change_every_field(self):
        response = self.client.post(reverse("event_edit", args=[self.event.pk]), self.edit_data())
        self.assertRedirects(response, reverse("calendar") + "?date=2026-10-22", fetch_redirect_response=False)
        self.event.refresh_from_db()
        self.assertEqual(self.event.event_name, "Museum trip")
        self.assertEqual(self.event.event_description, "Bring lunch")
        self.assertEqual(self.event.event_type, self.trip)
        self.assertEqual(self.event.status, self.cancelled)
        self.assertEqual(self.event.event_start_time, timezone.make_aware(datetime(2026, 10, 22, 8, 30)))
        self.assertEqual(self.event.event_end_time, timezone.make_aware(datetime(2026, 10, 23, 14, 0)))
        self.assertEqual(list(self.event.groups.all()), [self.class_b])
        # The author always stays involved, as when creating an event.
        self.assertEqual(set(self.event.users.all()), {self.lucy.profile, self.author.profile})

    def test_end_must_be_after_start(self):
        response = self.client.post(
            reverse("event_edit", args=[self.event.pk]), self.edit_data(event_end_time="2026-10-22T08:00")
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["event_end_time"])
        self.event.refresh_from_db()
        self.assertEqual(self.event.event_name, "Maths")

    def test_only_the_author_can_edit_or_delete(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("event_edit", args=[self.event.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("event_edit", args=[self.event.pk]), self.edit_data()).status_code, 404)
        self.assertEqual(self.client.post(reverse("event_delete", args=[self.event.pk])).status_code, 404)
        self.event.refresh_from_db()
        self.assertEqual(self.event.event_name, "Maths")

    def test_author_can_delete(self):
        self.assertEqual(self.client.get(reverse("event_delete", args=[self.event.pk])).status_code, 405)
        response = self.client.post(reverse("event_delete", args=[self.event.pk]))
        self.assertRedirects(response, reverse("calendar") + "?date=2026-10-20", fetch_redirect_response=False)
        self.assertFalse(Event.objects.filter(pk=self.event.pk).exists())

    def test_feed_offers_edit_only_to_the_author(self):
        self.event.users.add(self.other.profile)
        entry = self.client.get(reverse("events")).json()[0]
        self.assertTrue(entry["can_edit"])
        self.assertEqual(entry["edit_url"], reverse("event_edit", args=[self.event.pk]))
        self.client.force_login(self.other)
        entry = self.client.get(reverse("events")).json()[0]
        self.assertFalse(entry["can_edit"])
        self.assertEqual(entry["edit_url"], "")

    def test_calendar_opens_at_requested_date(self):
        self.assertContains(self.client.get(reverse("calendar") + "?date=2026-10-22"), "initialDate: '2026-10-22'")
        self.assertContains(self.client.get(reverse("calendar") + "?date=nonsense"), "initialDate: ''")


class EventRecipientsTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teacher", password="pw")
        self.lucy = User.objects.create_user(username="lucy", password="pw")
        self.group = GroupProfile.objects.create(group=Group.objects.create(name="Class 1A"))
        self.type = EventType.objects.create(name="Lesson")
        self.status = EventStatus.objects.create(name="Active")
        self.client.force_login(self.teacher)

    def create(self, **recipients):
        data = {
            "event_name": "Maths", "event_description": "x", "event_start_time": "2026-10-20T09:00",
            "duration_hours": 1, "duration_minutes": 0, "event_type": self.type.pk, "status": self.status.pk,
            **recipients,
        }
        return self.client.post(reverse("calendar"), data)

    def test_groups_alone_are_enough(self):
        self.assertRedirects(self.create(groups=[self.group.pk]), reverse("calendar"), fetch_redirect_response=False)
        event = Event.objects.get(event_name="Maths")
        self.assertEqual(list(event.groups.all()), [self.group])
        self.assertEqual(list(event.users.all()), [self.teacher.profile])  # the author is added

    def test_users_alone_are_enough(self):
        self.create(users=[self.lucy.profile.pk])
        event = Event.objects.get(event_name="Maths")
        self.assertFalse(event.groups.exists())
        self.assertEqual(set(event.users.all()), {self.lucy.profile, self.teacher.profile})

    def test_create_needs_groups_or_users(self):
        response = self.create()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select at least one group or user.")
        self.assertFalse(Event.objects.exists())

    def test_edit_needs_groups_or_users(self):
        self.create(groups=[self.group.pk])
        event = Event.objects.get(event_name="Maths")
        data = {
            "event_name": "Maths", "event_description": "x", "event_type": self.type.pk, "status": self.status.pk,
            "event_start_time": "2026-10-20T09:00", "event_end_time": "2026-10-20T10:00",
        }
        response = self.client.post(reverse("event_edit", args=[event.pk]), data)
        self.assertContains(response, "Select at least one group or user.")
        data["users"] = [self.lucy.profile.pk]
        self.client.post(reverse("event_edit", args=[event.pk]), data)
        self.assertFalse(event.groups.exists())
        self.assertIn(self.lucy.profile, event.users.all())
