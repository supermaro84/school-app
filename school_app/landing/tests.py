from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from datetime import timedelta

from django.utils import timezone

from accounts.models import UserRoles
from events.models import Event, EventStatus, EventType
from announcements.models import Announcement, AnnouncementRead


class LanguageSwitchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="lucy", password="pw", first_name="Lucy")
        self.client.force_login(self.user)

    def switch_to(self, language, next_url="/groups/"):
        return self.client.post(
            reverse("set_language"), {"language": language, "next": next_url}
        )

    def test_english_by_default(self):
        response = self.client.get(reverse("groups"))
        self.assertContains(response, '<html lang="en" ')
        self.assertContains(response, "My groups")

    def test_switching_to_polish_translates_pages_and_persists(self):
        response = self.switch_to("pl")
        self.assertRedirects(response, "/groups/", fetch_redirect_response=False)
        self.assertEqual(self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, "pl")

        response = self.client.get(reverse("groups"))
        self.assertContains(response, '<html lang="pl" ')
        self.assertContains(response, "Moje grupy")
        self.assertContains(response, "Witaj, Lucy!")

        self.assertContains(self.client.get(reverse("announcements_page")), "Wszystkie ogłoszenia")

    def test_switching_to_norwegian(self):
        self.switch_to("nb")
        response = self.client.get(reverse("groups"))
        self.assertContains(response, '<html lang="nb" ')
        self.assertContains(response, "Mine grupper")
        self.assertContains(response, "Velkommen, Lucy!")
        self.assertContains(response, 'value="nb"')  # switcher offers all three

    def test_switching_back_to_english(self):
        self.switch_to("pl")
        self.switch_to("en")
        self.assertContains(self.client.get(reverse("groups")), "My groups")

    def test_database_values_are_not_translated(self):
        self.user.profile.user_role = UserRoles.objects.create(user_role="Teacher")
        self.user.profile.save()
        self.switch_to("pl")
        response = self.client.get(reverse("user_detail", args=[self.user.pk]))
        self.assertContains(response, "Rola:")  # interface label is translated
        self.assertContains(response, "Teacher")  # stored value is shown as is
        self.assertNotContains(response, "Nauczyciel")

    def test_login_page_has_switcher_and_translates(self):
        self.client.logout()
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "pl"
        response = self.client.get(reverse("login"))
        self.assertContains(response, reverse("set_language"))
        self.assertContains(response, "Nie pamiętasz hasła?")

    def test_user_who_must_change_password_can_switch_language(self):
        self.user.profile.must_change_password = True
        self.user.profile.save()
        response = self.switch_to("pl", next_url=reverse("password_change"))
        self.assertRedirects(
            response, reverse("password_change"), fetch_redirect_response=False
        )
        self.assertContains(self.client.get(reverse("password_change")), "Zmień hasło")


class LandingAnnouncementsTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(username="parent", password="pw")
        self.child = User.objects.create_user(username="child", password="pw")
        self.parent.profile.affiliated_users.add(self.child)
        author = User.objects.create_user(username="teacher", password="pw")
        self.read = Announcement.objects.create(author=author, title="Read one", text="x")
        self.read.users.add(self.parent)
        self.unread = Announcement.objects.create(author=author, title="Unread one", text="x")
        self.unread.users.add(self.parent, self.child)
        AnnouncementRead.objects.create(announcement=self.read, user=self.parent)
        self.client.force_login(self.parent)

    def test_counts_and_unread_per_user(self):
        response = self.client.get(reverse("landing"))
        parent, child = response.context["affiliated_users"]
        self.assertEqual(len(parent.announcement_items), 2)
        self.assertEqual(parent.unread_count, 1)
        self.assertEqual(len(child.announcement_items), 1)
        self.assertEqual(child.unread_count, 1)
        self.assertContains(response, "Unread: 1", count=2)
        self.assertContains(response, reverse("announcement_detail", args=[self.unread.pk]))

    def test_opening_announcement_clears_unread(self):
        self.client.get(reverse("announcement_detail", args=[self.unread.pk]))
        response = self.client.get(reverse("landing"))
        self.assertNotContains(response, "Unread:")


class LandingUpcomingEventsTests(TestCase):
    def test_event_shows_type_and_status_tags(self):
        user = User.objects.create_user(username="student", password="pw")
        start = timezone.now() + timedelta(hours=3)
        event = Event.objects.create(
            owner=user.profile,
            event_name="Field trip",
            event_type=EventType.objects.create(name="Wycieczka"),
            status=EventStatus.objects.create(name="Wstępne"),
            event_start_time=start,
            event_end_time=start + timedelta(hours=1),
        )
        event.users.add(user.profile)
        self.client.force_login(user)
        response = self.client.get(reverse("landing"))
        self.assertContains(response, ">Wycieczka</span>")
        self.assertContains(response, ">Wstępne</span>")
