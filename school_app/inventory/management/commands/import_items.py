import csv

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from inventory.models import Book, Item

REQUIRED_COLUMNS = {"owner", "title", "author"}


class Command(BaseCommand):
    help = (
        "Import inventory items from a CSV file. Columns: owner (username), title, "
        "author, and optionally isbn (ISBN-10/13, hyphens allowed), description and "
        "category (only 'book' for now; the default). Owners must already exist. "
        "A row is skipped when its owner already has a book with the same title and "
        "author. Any other error rolls back the whole import."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_file", help="Path to the CSV file with items")

    def handle(self, *args, **options):
        try:
            with open(options["csv_file"], newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
                if missing:
                    raise CommandError(f"Missing columns: {', '.join(sorted(missing))}")
                rows = list(reader)
        except FileNotFoundError:
            raise CommandError(f"File {options['csv_file']} not found")

        owners = {}
        created = 0
        skipped = 0

        with transaction.atomic():
            for line, row in enumerate(rows, start=2):
                row = {key: (value or "").strip() for key, value in row.items()}
                category = (row.get("category") or Item.Category.BOOK).lower()
                if category != Item.Category.BOOK:
                    raise CommandError(f"Line {line}: unknown category '{category}'")

                username = row["owner"]
                if username not in owners:
                    try:
                        owners[username] = User.objects.get(username=username)
                    except User.DoesNotExist:
                        raise CommandError(f"Line {line}: unknown owner '{username}'")
                owner = owners[username]

                if Book.objects.filter(owner=owner, title=row["title"], author=row["author"]).exists():
                    self.stdout.write(
                        self.style.WARNING(f"Line {line}: {owner} already has '{row['title']}', skipped")
                    )
                    skipped += 1
                    continue

                book = Book(
                    owner=owner,
                    title=row["title"],
                    author=row["author"],
                    isbn=row.get("isbn", ""),
                    description=row.get("description", ""),
                    category=Item.Category.BOOK,
                )
                try:
                    book.full_clean()
                except ValidationError as error:
                    details = "; ".join(f"{field}: {' '.join(msgs)}" for field, msgs in error.message_dict.items())
                    raise CommandError(f"Line {line}: {details}")
                book.save()
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created} items, skipped {skipped}."))
