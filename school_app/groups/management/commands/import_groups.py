import csv

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from groups.models import GroupProfile

REQUIRED_COLUMNS = {"name", "description", "admins", "members"}


def split_usernames(value):
    return [username for username in map(str.strip, value.split(";")) if username]


class Command(BaseCommand):
    help = (
        "Import groups from a CSV file. Columns: name, description, admins, "
        "members (admins and members are usernames separated by ';'). "
        "Users must already exist; groups whose name exists are skipped."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_file", help="Path to the CSV file with groups")

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
                name = row["name"]
                if not name:
                    raise CommandError(f"Line {line}: name is empty")
                if Group.objects.filter(name=name).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Line {line}: group {name} already exists, skipped"
                        )
                    )
                    skipped += 1
                    continue

                admins = self.get_users(row["admins"], line)
                members = self.get_users(row["members"], line)

                group = Group.objects.create(name=name)
                profile = GroupProfile.objects.create(
                    group=group, description=row["description"]
                )
                profile.admins.add(*admins)
                profile.members.add(*members)
                profile.drop_admins_from_members()
                created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created} groups, skipped {skipped}.")
        )

    def get_users(self, value, line):
        usernames = split_usernames(value)
        users = {user.username: user for user in User.objects.filter(username__in=usernames)}
        unknown = [username for username in usernames if username not in users]
        if unknown:
            raise CommandError(f"Line {line}: unknown users: {', '.join(unknown)}")
        return list(users.values())
