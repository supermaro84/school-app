import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from events.models import EventStatus, EventType

REQUIRED_COLUMNS = {"kind", "name"}
MODELS = {"type": EventType, "status": EventStatus}


class Command(BaseCommand):
    help = (
        "Import event types and statuses from a CSV file. Columns: kind "
        "('type' or 'status'), name. Names that already exist are skipped."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_file", help="Path to the CSV file with event options")

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
                model = MODELS.get(row["kind"].lower())
                if model is None:
                    raise CommandError(
                        f"Line {line}: kind must be 'type' or 'status', got '{row['kind']}'"
                    )
                if not row["name"]:
                    raise CommandError(f"Line {line}: name is empty")

                if model.objects.filter(name__iexact=row["name"]).exists():
                    skipped += 1
                    continue
                model.objects.create(name=row["name"])
                created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created} event options, skipped {skipped}.")
        )
