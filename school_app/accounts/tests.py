import csv
import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserRoles

CSV_HEADER = "username,first_name,last_name,email,role,birthdate,phone_number,affiliated_users\n"


class ImportUsersTests(TestCase):
    def setUp(self):
        for name in ["Admin", "Teacher", "Student", "Guardian"]:
            UserRoles.objects.create(user_role=name)
        self.tmp = Path(tempfile.mkdtemp())
        self.output = self.tmp / "credentials.csv"

    def run_import(self, rows):
        csv_file = self.tmp / "users.csv"
        csv_file.write_text(CSV_HEADER + rows)
        call_command("import_users", str(csv_file), output=str(self.output), stdout=open("/dev/null", "w"))

    def read_credentials(self):
        with open(self.output, newline="") as f:
            return {row["username"]: row for row in csv.DictReader(f)}

    def test_creates_users_with_temporary_passwords(self):
        self.run_import(
            "tom,Tom,Novak,tom@example.com,Guardian,1981-02-14,+123,lucy\n"
            "lucy,Lucy,Novak,lucy@example.com,Student,2016-09-03,,\n"
        )
        credentials = self.read_credentials()
        tom = User.objects.get(username="tom")

        password = credentials["tom"]["password"]
        self.assertRegex(password, r"^tom-[A-Za-z0-9]{6}$")
        self.assertTrue(tom.check_password(password))
        self.assertTrue(tom.profile.must_change_password)
        self.assertEqual(tom.profile.user_role.user_role, "Guardian")
        self.assertEqual(str(tom.profile.birthdate), "1981-02-14")
        self.assertEqual(
            list(tom.profile.affiliated_users.values_list("username", flat=True)),
            ["lucy"],
        )

    def test_skips_existing_users(self):
        User.objects.create_user(username="tom", password="keep-me")
        self.run_import("tom,Tom,Novak,tom@example.com,Guardian,,,\n")
        self.assertTrue(User.objects.get(username="tom").check_password("keep-me"))
        self.assertFalse(self.output.exists())

    def test_unknown_role_rolls_back_whole_import(self):
        with self.assertRaises(CommandError):
            self.run_import(
                "tom,Tom,Novak,tom@example.com,Guardian,,,\n"
                "lucy,Lucy,Novak,lucy@example.com,Pupil,,,\n"
            )
        self.assertFalse(User.objects.filter(username="tom").exists())
        self.assertFalse(self.output.exists())


class ForcePasswordChangeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tom", password="tom-Abc234")
        self.user.profile.must_change_password = True
        self.user.profile.save()
        self.client.login(username="tom", password="tom-Abc234")

    def test_redirects_to_password_change(self):
        response = self.client.get(reverse("users_list"))
        self.assertRedirects(response, reverse("password_change"))

    def test_changing_password_clears_flag(self):
        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "tom-Abc234",
                "new_password1": "Sunny-Meadow-42",
                "new_password2": "Sunny-Meadow-42",
            },
        )
        self.assertRedirects(response, reverse("landing"), fetch_redirect_response=False)
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.must_change_password)
        self.assertEqual(self.client.get(reverse("users_list")).status_code, 200)


class ImportRolesTests(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def run_import(self, rows):
        csv_file = self.tmp / "roles.csv"
        csv_file.write_text("name\n" + rows)
        call_command("import_roles", str(csv_file), stdout=open("/dev/null", "w"))

    def test_creates_roles_and_skips_existing(self):
        UserRoles.objects.create(user_role="Nauczyciel")
        self.run_import("nauczyciel\nUczeń\nOpiekun\n")
        self.assertEqual(
            sorted(UserRoles.objects.values_list("user_role", flat=True)),
            ["Nauczyciel", "Opiekun", "Uczeń"],
        )

    def test_empty_name_rolls_back_whole_import(self):
        with self.assertRaises(CommandError):
            self.run_import("Nauczyciel\n   \n")
        self.assertFalse(UserRoles.objects.exists())
