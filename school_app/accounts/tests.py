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

    def test_optional_description_column(self):
        csv_file = self.tmp / "users.csv"
        csv_file.write_text(
            "username,first_name,last_name,email,role,description\n"
            'anna,Anna,Mazur,anna@example.com,Guardian,"Class rep for 1A, speaks Norwegian"\n'
            "piotr,Piotr,Nowak,piotr@example.com,Teacher,\n"
        )
        call_command("import_users", str(csv_file), output=str(self.output), stdout=open("/dev/null", "w"))
        self.assertEqual(User.objects.get(username="anna").profile.description, "Class rep for 1A, speaks Norwegian")
        self.assertEqual(User.objects.get(username="piotr").profile.description, "")

    def test_birthdate_column_is_optional(self):
        csv_file = self.tmp / "users3.csv"
        csv_file.write_text("username,first_name,last_name,email,role\nola,Ola,Nowak,ola@example.com,Student\n")
        call_command("import_users", str(csv_file), output=str(self.tmp / "c3.csv"), stdout=open("/dev/null", "w"))
        self.assertIsNone(User.objects.get(username="ola").profile.birthdate)

    def test_update_descriptions_of_existing_users(self):
        self.run_import("anna,Anna,Mazur,anna@example.com,Guardian,,,\n")
        anna = User.objects.get(username="anna")
        password_hash = anna.password
        csv_file = self.tmp / "users2.csv"
        csv_file.write_text(
            "username,first_name,last_name,email,role,description\n"
            "anna,Changed,Name,x@example.com,Teacher,Class rep for 1A\n"
            "piotr,Piotr,Nowak,piotr@example.com,Teacher,New teacher\n"
        )
        call_command("import_users", str(csv_file), "--update-descriptions",
                     output=str(self.tmp / "new.csv"), stdout=open("/dev/null", "w"))
        anna.refresh_from_db()
        # Only the description changed for the existing user...
        self.assertEqual(anna.profile.description, "Class rep for 1A")
        self.assertEqual((anna.first_name, anna.email, anna.password), ("Anna", "anna@example.com", password_hash))
        self.assertEqual(anna.profile.user_role.user_role, "Guardian")
        # ...and new users are still created
        self.assertEqual(User.objects.get(username="piotr").profile.description, "New teacher")

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


class UserDescriptionTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(username="viewer", password="pw")
        self.teacher = User.objects.create_user(username="teacher", first_name="Ewa", last_name="Nowak")
        self.client.force_login(self.viewer)

    def test_description_on_user_page(self):
        self.teacher.profile.description = "Maths teacher.\nOffice hours on Tuesdays."
        self.teacher.profile.save()
        response = self.client.get(reverse("user_detail", args=[self.teacher.pk]))
        self.assertContains(response, "Maths teacher.<br>Office hours on Tuesdays.")

    def test_email_on_user_page(self):
        self.teacher.email = "ewa.nowak@example.com"
        self.teacher.save()
        response = self.client.get(reverse("user_detail", args=[self.teacher.pk]))
        self.assertContains(response, '<a href="mailto:ewa.nowak@example.com" class="text-break">ewa.nowak@example.com</a>', html=True)

    def test_birthdate_not_on_user_page(self):
        from datetime import date
        self.teacher.profile.birthdate = date(1985, 9, 23)
        self.teacher.profile.save()
        response = self.client.get(reverse("user_detail", args=[self.teacher.pk]))
        self.assertNotContains(response, "1985")
        self.assertNotContains(response, "Birthdate")

    def test_empty_description_shows_a_dash(self):
        response = self.client.get(reverse("user_detail", args=[self.teacher.pk]))
        self.assertContains(response, "<dt>Description</dt><dd>–</dd>", html=True)



class ProfileEditTests(TestCase):
    def setUp(self):
        self.role = UserRoles.objects.create(user_role="Teacher")
        self.user = User.objects.create_user(username="ewa", password="pw", first_name="Ewa", email="ewa@example.com")
        self.user.profile.user_role = self.role
        self.user.profile.save()
        self.other = User.objects.create_user(username="other", password="pw")
        self.client.force_login(self.user)

    def data(self, **changes):
        data = {
            "first_name": "Ewa", "last_name": "Nowak", "email": "ewa.nowak@example.com",
            "birthdate": "1985-09-23", "phone_number": "+48 600 000 102", "description": "Maths teacher",
        }
        data.update(changes)
        return data

    def test_edit_own_data(self):
        response = self.client.post(reverse("profile_edit"), self.data())
        self.assertRedirects(response, reverse("user_detail", args=[self.user.pk]), fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertEqual((self.user.first_name, self.user.last_name, self.user.email), ("Ewa", "Nowak", "ewa.nowak@example.com"))
        profile = self.user.profile
        profile.refresh_from_db()
        self.assertEqual(str(profile.birthdate), "1985-09-23")
        self.assertEqual(profile.phone_number, "+48 600 000 102")
        self.assertEqual(profile.description, "Maths teacher")
        self.assertContains(self.client.get(reverse("user_detail", args=[self.user.pk])), "Your profile has been saved.")

    def test_role_username_and_affiliations_cannot_be_changed(self):
        other_role = UserRoles.objects.create(user_role="Admin")
        self.client.post(reverse("profile_edit"), self.data(
            username="hacker", user_role=other_role.pk, affiliated_users=[self.other.pk], is_superuser="on",
        ))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "ewa")
        self.assertFalse(self.user.is_superuser)
        self.assertEqual(self.user.profile.user_role, self.role)
        self.assertFalse(self.user.profile.affiliated_users.exists())

    def test_birthdate_is_optional(self):
        response = self.client.post(reverse("profile_edit"), self.data(birthdate=""))
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertIsNone(self.user.profile.birthdate)

    def test_validation(self):
        response = self.client.post(reverse("profile_edit"), self.data(email="", phone_number="call me", birthdate="2999-01-01"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user_form"].errors["email"])
        self.assertTrue(response.context["profile_form"].errors["phone_number"])
        self.assertTrue(response.context["profile_form"].errors["birthdate"])
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "ewa@example.com")

    def test_form_is_prefilled_with_own_data(self):
        response = self.client.get(reverse("profile_edit"))
        self.assertContains(response, 'value="ewa@example.com"')
        self.assertContains(response, "Username: ewa.")

    def test_edit_button_only_on_own_page(self):
        self.assertContains(self.client.get(reverse("user_detail", args=[self.user.pk])), reverse("profile_edit"))
        self.assertNotContains(self.client.get(reverse("user_detail", args=[self.other.pk])), 'href="/profile/edit/"')

    def test_my_profile_link(self):
        self.assertRedirects(self.client.get(reverse("my_profile")), reverse("user_detail", args=[self.user.pk]))
        self.assertContains(self.client.get(reverse("groups")), f'href="{reverse("my_profile")}"')

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("profile_edit")).status_code, 302)
