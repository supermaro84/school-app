import csv
from datetime import date, datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import UserProfile
from events.models import Event, EventStatus, EventType
from groups.models import GroupProfile

REQUIRED_COLUMNS = {
    "owner", "name", "description", "type", "status", "start", "end", "groups", "users",
}


def split_names(value):
    return [name for name in map(str.strip, value.split(";")) if name]


def parse_datetime(value, column, line):
    """Parse 'YYYY-MM-DD HH:MM' as a naive local time (made aware on save)."""
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError:
        raise CommandError(
            f"Line {line}: {column} '{value}' is not in YYYY-MM-DD HH:MM format"
        )


class Command(BaseCommand):
    help = (
        "Import events from a CSV file. Columns: owner (username), name, "
        "description, type, status (names of existing event types/statuses), "
        "start, end (YYYY-MM-DD HH:MM), groups (group names separated by ';'), "
        "users (usernames separated by ';'), and optionally "
        "repeat_weekly_until (YYYY-MM-DD) to repeat the event every week up to "
        "that date. The owner is always added to the event's users. Events with "
        "the same owner, name and start time as an existing one are skipped."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_file", help="Path to the CSV file with events")

    def handle(self, *args, **options):
        try:
            with open(options["csv_file"], newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
                if missing:
                    raise CommandError(
                        f"Missing columns: {', '.join(sorted(missing))}"
                    )
                rows = list(reader)
        except FileNotFoundError:
            raise CommandError(f"File {options['csv_file']} not found")

        created = 0
        skipped = 0

        with transaction.atomic():
            for line, row in enumerate(rows, start=2):
                row = {key: (value or "").strip() for key, value in row.items()}
                if not row["name"]:
                    raise CommandError(f"Line {line}: name is empty")
                try:
                    owner = UserProfile.objects.get(user__username=row["owner"])
                except UserProfile.DoesNotExist:
                    raise CommandError(f"Line {line}: unknown owner '{row['owner']}'")
                event_type = self.get_option(EventType, row["type"], "type", line)
                status = self.get_option(EventStatus, row["status"], "status", line)
                groups = self.get_groups(row["groups"], line)
                users = self.get_users(row["users"], line)

                start = parse_datetime(row["start"], "start", line)
                end = parse_datetime(row["end"], "end", line)
                if end <= start:
                    raise CommandError(f"Line {line}: end must be after start")

                for occurrence_start in self.occurrences(start, row, line):
                    occurrence_end = occurrence_start + (end - start)
                    # Aware per occurrence, so lessons keep their local time across DST
                    aware_start = timezone.make_aware(occurrence_start)
                    if Event.objects.filter(
                        owner=owner, event_name=row["name"], event_start_time=aware_start
                    ).exists():
                        skipped += 1
                        continue
                    event = Event.objects.create(
                        owner=owner,
                        event_name=row["name"],
                        event_description=row["description"],
                        event_type=event_type,
                        status=status,
                        event_start_time=aware_start,
                        event_end_time=timezone.make_aware(occurrence_end),
                    )
                    event.groups.add(*groups)
                    event.users.add(owner, *users)
                    created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created} events, skipped {skipped}.")
        )

    def occurrences(self, start, row, line):
        repeat_until = row.get("repeat_weekly_until", "")
        if not repeat_until:
            return [start]
        try:
            until = date.fromisoformat(repeat_until)
        except ValueError:
            raise CommandError(
                f"Line {line}: repeat_weekly_until '{repeat_until}' "
                "is not in YYYY-MM-DD format"
            )
        if until < start.date():
            raise CommandError(f"Line {line}: repeat_weekly_until is before start")
        result = []
        current = start
        while current.date() <= until:
            result.append(current)
            current += timedelta(weeks=1)
        return result

    def get_option(self, model, name, column, line):
        try:
            return model.objects.get(name__iexact=name)
        except model.DoesNotExist:
            raise CommandError(f"Line {line}: unknown {column} '{name}'")

    def get_groups(self, value, line):
        names = split_names(value)
        groups = {
            group.group.name: group
            for group in GroupProfile.objects.select_related("group").filter(
                group__name__in=names
            )
        }
        unknown = [name for name in names if name not in groups]
        if unknown:
            raise CommandError(f"Line {line}: unknown groups: {', '.join(unknown)}")
        return list(groups.values())

    def get_users(self, value, line):
        usernames = split_names(value)
        profiles = {
            profile.user.username: profile
            for profile in UserProfile.objects.select_related("user").filter(
                user__username__in=usernames
            )
        }
        unknown = [username for username in usernames if username not in profiles]
        if unknown:
            raise CommandError(f"Line {line}: unknown users: {', '.join(unknown)}")
        return list(profiles.values())
