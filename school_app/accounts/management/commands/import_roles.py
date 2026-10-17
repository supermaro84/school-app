import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import UserRoles


class Command(BaseCommand):
    help = (
        "Import user roles from a CSV file with a 'name' column. "
        "Names that already exist (case-insensitive) are skipped."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_file", help="Path to the CSV file with roles")

    def handle(self, *args, **options):
        try:
            with open(options["csv_file"], newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if "name" not in (reader.fieldnames or []):
                    raise CommandError("Missing columns: name")
                rows = list(reader)
        except FileNotFoundError:
            raise CommandError(f"File {options['csv_file']} not found")

        created = 0
        skipped = 0

        with transaction.atomic():
            for line, row in enumerate(rows, start=2):
                name = (row["name"] or "").strip()
                if not name:
                    raise CommandError(f"Line {line}: name is empty")
                if UserRoles.objects.filter(user_role__iexact=name).exists():
                    skipped += 1
                    continue
                UserRoles.objects.create(user_role=name)
                created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created} roles, skipped {skipped}.")
        )
