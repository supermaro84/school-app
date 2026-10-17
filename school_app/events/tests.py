import tempfile
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
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
