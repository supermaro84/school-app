import csv
import secrets
from datetime import date
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import UserRoles

REQUIRED_COLUMNS = {"username", "first_name", "last_name", "email", "role"}

# Characters that are easy to read and type (no 0/O, 1/l/I)
PASSWORD_ALPHABET = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789"


TRUE_VALUES = {"yes", "y", "true", "1"}
FALSE_VALUES = {"no", "n", "false", "0", ""}


def generate_password(username, suffix_length=6):
    suffix = "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(suffix_length))
    return f"{username}-{suffix}"


def parse_flag(row, column, line):
    value = row.get(column, "").lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise CommandError(f"Line {line}: {column} must be yes or no, got '{row[column]}'")


class Command(BaseCommand):
    help = (
        "Import users from a CSV file. Each new user gets a temporary password "
        "(username + random suffix) that must be changed after the first login. "
        "Columns: username, first_name, last_name, email, role, and optionally "
        "birthdate (YYYY-MM-DD), phone_number, affiliated_users "
        "(usernames separated by ';'), is_staff and is_superuser (yes/no)."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_file", help="Path to the CSV file with users")
        parser.add_argument(
            "--output",
            default="credentials.csv",
            help="Where to write the generated usernames and passwords "
            "(default: credentials.csv). Must not exist yet.",
        )

    def handle(self, *args, **options):
        output_path = Path(options["output"])
        if output_path.exists():
            raise CommandError(f"Output file {output_path} already exists")

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

        roles = {role.user_role.lower(): role for role in UserRoles.objects.all()}
        credentials = []
        skipped = 0

        with transaction.atomic():
            created = []
            for line, row in enumerate(rows, start=2):
                row = {key: (value or "").strip() for key, value in row.items()}
                username = row["username"]
                if not username:
                    raise CommandError(f"Line {line}: username is empty")
                if User.objects.filter(username=username).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Line {line}: user {username} already exists, skipped"
                        )
                    )
                    skipped += 1
                    continue

                role = roles.get(row["role"].lower())
                if role is None:
                    raise CommandError(f"Line {line}: unknown role '{row['role']}'")

                birthdate = None
                if row.get("birthdate"):
                    try:
                        birthdate = date.fromisoformat(row["birthdate"])
                    except ValueError:
                        raise CommandError(
                            f"Line {line}: birthdate '{row['birthdate']}' "
                            "is not in YYYY-MM-DD format"
                        )

                is_staff = parse_flag(row, "is_staff", line)
                is_superuser = parse_flag(row, "is_superuser", line)

                password = generate_password(username)
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=row["email"],
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                    is_staff=is_staff or is_superuser,
                    is_superuser=is_superuser,
                )
                profile = user.profile
                profile.user_role = role
                profile.birthdate = birthdate
                profile.phone_number = row.get("phone_number", "")
                profile.must_change_password = True
                profile.save()

                created.append((line, profile, row.get("affiliated_users", "")))
                credentials.append(
                    {
                        "username": username,
                        "password": password,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "role": role.user_role,
                    }
                )

            # Link affiliations after all users exist, so a row can refer to users
            # defined later in the file
            for line, profile, affiliated in created:
                for affiliated_username in filter(None, map(str.strip, affiliated.split(";"))):
                    try:
                        affiliated_user = User.objects.get(username=affiliated_username)
                    except User.DoesNotExist:
                        raise CommandError(
                            f"Line {line}: affiliated user "
                            f"'{affiliated_username}' does not exist"
                        )
                    profile.affiliated_users.add(affiliated_user)

        if credentials:
            with open(output_path, "x", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(credentials[0]))
                writer.writeheader()
                writer.writerows(credentials)

        self.stdout.write(
            self.style.SUCCESS(f"Created {len(credentials)} users, skipped {skipped}.")
        )
        if credentials:
            self.stdout.write(
                f"Temporary passwords written to {output_path}. "
                "Hand them out securely, then delete the file."
            )
