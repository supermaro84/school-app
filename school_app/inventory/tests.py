import tempfile
from datetime import timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from media.tests import IN_MEMORY_STORAGES, image_upload

from .models import Book, Item, ItemImage, Loan, validate_isbn


class IsbnTests(TestCase):
    def test_valid_isbns(self):
        for value in ["978-0-306-40615-7", "9780306406157", "0-306-40615-2", "080442957X", "0 8044 2957 x"]:
            validate_isbn(value)  # no error

    def test_invalid_isbns(self):
        for value in ["9780306406158", "0306406153", "12345", "abcdefghij"]:
            with self.assertRaises(ValidationError, msg=value):
                validate_isbn(value)

    def test_isbn_is_stored_without_hyphens(self):
        owner = User.objects.create_user("owner")
        book = Book.objects.create(title="Lalka", author="Bolesław Prus", isbn="978-0-306-40615-7", owner=owner)
        self.assertEqual(book.isbn, "9780306406157")
        self.assertEqual(book.category, Item.Category.BOOK)
        self.assertEqual(Item.objects.get(pk=book.pk).details, book)


class InventoryTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", password="pw", first_name="Olga", last_name="Owner")
        self.friend = User.objects.create_user("friend", password="pw", first_name="Filip", last_name="Friend")
        self.other = User.objects.create_user("other", password="pw")
        self.book = Book.objects.create(title="Pan Tadeusz", author="Adam Mickiewicz", owner=self.owner)

    def lend(self, user=None, borrower=None, due_date=""):
        self.client.force_login(user or self.owner)
        return self.client.post(
            reverse("item_lend", args=[self.book.pk]),
            {"borrower": (borrower or self.friend).pk, "due_date": due_date},
        )


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class AddItemTests(InventoryTestCase):
    def test_add_book_with_photos(self):
        self.client.force_login(self.friend)
        response = self.client.post(
            reverse("item_create"),
            {"title": "Quo vadis", "author": "Henryk Sienkiewicz", "isbn": "978-0-306-40615-7",
             "description": "", "images": [image_upload("a.png"), image_upload("b.png")]},
        )
        book = Book.objects.get(title="Quo vadis")
        self.assertRedirects(response, reverse("item_detail", args=[book.pk]))
        self.assertEqual(book.owner, self.friend)
        self.assertEqual(book.images.count(), 2)

    def test_invalid_isbn_is_rejected(self):
        self.client.force_login(self.friend)
        response = self.client.post(reverse("item_create"), {"title": "X", "author": "Y", "isbn": "123"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Book.objects.filter(title="X").exists())

    def test_only_owner_can_edit_and_delete_photos(self):
        image = ItemImage.objects.create(item=self.book, file=image_upload("c.png"))
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("item_edit", args=[self.book.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("item_image_delete", args=[image.pk])).status_code, 404)
        self.client.force_login(self.owner)
        self.client.post(reverse("item_image_delete", args=[image.pk]))
        self.assertFalse(ItemImage.objects.exists())


class LendingTests(InventoryTestCase):
    def test_lent_item_shows_in_both_inventories(self):
        self.lend(due_date=(timezone.localdate() + timedelta(days=14)).isoformat())
        loan = Loan.objects.get()
        self.assertEqual(loan.borrower, self.friend)
        self.assertEqual(self.book.holder, self.friend)

        # Owner's list says who has it
        mine = self.client.get(reverse("inventory"))
        self.assertContains(mine, "Pan Tadeusz")
        self.assertContains(mine, "Filip Friend")

        # Borrower sees it among borrowed items
        self.client.force_login(self.friend)
        borrowed = self.client.get(reverse("inventory") + "?tab=borrowed")
        self.assertContains(borrowed, "Pan Tadeusz")
        self.assertNotContains(self.client.get(reverse("inventory")), "Pan Tadeusz")

    def test_catalog_shows_everyones_items_without_borrower_name(self):
        self.lend()
        self.client = self.client_class()  # new session: no flash message from the owner
        self.client.force_login(self.other)
        catalog = self.client.get(reverse("inventory") + "?tab=catalog")
        self.assertContains(catalog, "Pan Tadeusz")
        self.assertNotContains(catalog, "Filip Friend")
        self.assertEqual(self.client.get(reverse("item_detail", args=[self.book.pk])).status_code, 200)

    def test_search(self):
        Book.objects.create(title="Lalka", author="Bolesław Prus", owner=self.owner)
        self.client.force_login(self.owner)
        response = self.client.get(reverse("inventory") + "?q=mickiewicz")
        self.assertContains(response, "Pan Tadeusz")
        self.assertNotContains(response, "Lalka")

    def test_cannot_lend_twice(self):
        self.lend()
        self.lend(borrower=self.other)
        self.assertEqual(Loan.objects.get().borrower, self.friend)

    def test_cannot_lend_to_yourself_or_with_past_due_date(self):
        self.lend(borrower=self.owner)
        self.lend(due_date=(timezone.localdate() - timedelta(days=1)).isoformat())
        self.assertFalse(Loan.objects.exists())

    def test_only_owner_can_lend_return_and_delete(self):
        self.assertEqual(self.lend(user=self.other).status_code, 404)
        self.lend()
        self.client.force_login(self.friend)
        self.assertEqual(self.client.post(reverse("item_return", args=[self.book.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("item_delete", args=[self.book.pk])).status_code, 404)

    def test_return_closes_the_loan_and_keeps_history(self):
        self.lend()
        self.client.post(reverse("item_return", args=[self.book.pk]))
        loan = Loan.objects.get()
        self.assertIsNotNone(loan.returned_at)
        self.assertTrue(Item.objects.get(pk=self.book.pk).is_available)
        self.client.force_login(self.friend)
        self.assertNotContains(self.client.get(reverse("inventory") + "?tab=borrowed"), "Pan Tadeusz")
        # It can be lent again
        self.lend(borrower=self.other)
        self.assertEqual(Loan.objects.count(), 2)

    def test_lent_item_cannot_be_deleted(self):
        self.lend()
        self.client.post(reverse("item_delete", args=[self.book.pk]))
        self.assertTrue(Item.objects.filter(pk=self.book.pk).exists())
        self.client.post(reverse("item_return", args=[self.book.pk]))
        self.client.post(reverse("item_delete", args=[self.book.pk]))
        self.assertFalse(Item.objects.filter(pk=self.book.pk).exists())

    def test_overdue(self):
        loan = Loan.objects.create(item=self.book, borrower=self.friend, due_date=timezone.localdate() - timedelta(days=1))
        self.assertTrue(loan.is_overdue)

    def test_login_required(self):
        response = self.client.get(reverse("inventory"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class ImportItemsTests(TestCase):
    def setUp(self):
        self.library = User.objects.create_user("biblioteka")
        self.tmp = Path(tempfile.mkdtemp())

    def run_import(self, rows, header="owner,title,author,isbn,description\n"):
        csv_file = self.tmp / "books.csv"
        csv_file.write_text(header + rows, encoding="utf-8")
        call_command("import_items", str(csv_file), stdout=open("/dev/null", "w"))

    def test_creates_books(self):
        self.run_import(
            'biblioteka,Pan Tadeusz,Adam Mickiewicz,978-0-306-40615-7,"Epopeja, klasy 7-8"\n'
            "biblioteka,Lalka,Bolesław Prus,,\n"
        )
        books = Book.objects.order_by("title")
        self.assertEqual([b.title for b in books], ["Lalka", "Pan Tadeusz"])
        self.assertEqual(books[1].isbn, "9780306406157")
        self.assertEqual(books[1].description, "Epopeja, klasy 7-8")
        self.assertTrue(all(b.owner == self.library and b.category == "book" for b in books))

    def test_reimport_skips_existing_books(self):
        self.run_import("biblioteka,Lalka,Bolesław Prus,,\n")
        self.run_import("biblioteka,Lalka,Bolesław Prus,,\n")
        self.assertEqual(Book.objects.count(), 1)

    def test_errors_roll_back_whole_import(self):
        for bad_row in ["nobody,Lalka,Bolesław Prus,,\n", "biblioteka,Lalka,Bolesław Prus,123,\n", "biblioteka,,Bolesław Prus,,\n"]:
            with self.assertRaises(CommandError, msg=bad_row):
                self.run_import("biblioteka,Pan Tadeusz,Adam Mickiewicz,,\n" + bad_row)
        self.assertFalse(Book.objects.exists())

    def test_unknown_category_is_rejected(self):
        with self.assertRaises(CommandError):
            self.run_import("biblioteka,Chess,,,,game\n", header="owner,title,author,isbn,description,category\n")
