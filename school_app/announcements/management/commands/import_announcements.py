import csv
from datetime import datetime, time

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from announcements.models import Announcement
from groups.models import GroupProfile

REQUIRED_COLUMNS = {"author", "title", "text", "groups", "users"}


def split_names(value):
    return [name for name in map(str.strip, value.split(";")) if name]


def parse_datetime(value, column, line, default_time=time.min):
    """Parse 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM' as a time in TIME_ZONE."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise CommandError(
            f"Line {line}: {column} '{value}' is not in YYYY-MM-DD [HH:MM] format"
        )
    if len(value) == 10:
        parsed = datetime.combine(parsed.date(), default_time)
    return timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed


class Command(BaseCommand):
    help = (
        "Import announcements from a CSV file. Columns: author, title, text "
        "(HTML allowed), groups (group names separated by ';'), users "
        "(usernames separated by ';'), and optionally pub_date and exp_date "
        "(YYYY-MM-DD or YYYY-MM-DD HH:MM). An announcement with no groups and "
        "no users is public. Announcements with the same author and title as "
        "an existing one are skipped."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_file", help="Path to the CSV file with announcements")

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
                title = row["title"]
                if not title:
                    raise CommandError(f"Line {line}: title is empty")
                try:
                    author = User.objects.get(username=row["author"])
                except User.DoesNotExist:
                    raise CommandError(f"Line {line}: unknown author '{row['author']}'")

                if Announcement.objects.filter(author=author, title=title).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Line {line}: announcement '{title}' by "
                            f"{author.username} already exists, skipped"
                        )
                    )
                    skipped += 1
                    continue

                groups = self.get_groups(row["groups"], line)
                users = self.get_users(row["users"], line)
                pub_date = parse_datetime(row.get("pub_date", ""), "pub_date", line)
                exp_date = parse_datetime(
                    row.get("exp_date", ""), "exp_date", line, default_time=time.max
                )

                announcement = Announcement.objects.create(
                    author=author, title=title, text=row["text"], exp_date=exp_date
                )
                announcement.groups.add(*groups)
                announcement.users.add(*users)
                if pub_date:
                    # pub_date is auto_now_add, so it can only be overridden after saving
                    Announcement.objects.filter(pk=announcement.pk).update(pub_date=pub_date)
                created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created} announcements, skipped {skipped}.")
        )

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
        users = {user.username: user for user in User.objects.filter(username__in=usernames)}
        unknown = [username for username in usernames if username not in users]
        if unknown:
            raise CommandError(f"Line {line}: unknown users: {', '.join(unknown)}")
        return list(users.values())
