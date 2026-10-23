from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from school_app.theme import PRESETS, load_theme


class LoadThemeTests(TestCase):
    def test_defaults(self):
        theme = load_theme({})
        self.assertEqual(theme["preset"], "default")
        self.assertEqual(theme["primary"], PRESETS["default"]["primary"])
        self.assertEqual(theme["navbar"], "dark")
        self.assertTrue(theme["navbar_dark"])
        self.assertEqual(theme["mode"], "auto")  # follow the device
        self.assertEqual(theme["app_name"], "")

    def test_preset_with_overrides(self):
        theme = load_theme({"THEME_PRESET": "Forest", "THEME_PRIMARY_COLOR": "#ABC", "APP_NAME": " Oak School "})
        self.assertEqual(theme["preset"], "forest")
        self.assertEqual(theme["primary"], "#aabbcc")
        self.assertEqual(theme["primary_rgb"], "170, 187, 204")
        self.assertEqual(theme["secondary"], PRESETS["forest"]["secondary"])
        self.assertEqual(theme["app_name"], "Oak School")

    def test_invalid_values_fall_back_with_a_warning(self):
        env = {"THEME_PRESET": "neon", "THEME_PRIMARY_COLOR": "blue", "THEME_NAVBAR": "pink", "THEME_MODE": "dim"}
        with self.assertLogs("school_app.theme", "WARNING") as logs:
            theme = load_theme(env)
        self.assertEqual(len(logs.records), 4)
        self.assertEqual(theme["preset"], "default")
        self.assertEqual(theme["primary"], PRESETS["default"]["primary"])
        self.assertEqual(theme["navbar"], "dark")
        self.assertEqual(theme["mode"], "auto")

    def test_system_font_by_default(self):
        theme = load_theme({})
        self.assertEqual((theme["font"], theme["heading_font"], theme["font_urls"]), ("", "", []))
        self.assertTrue(theme["font_stack"].startswith("system-ui"))
        self.assertEqual(load_theme({"THEME_FONT": "System"})["font"], "")

    def test_google_fonts(self):
        theme = load_theme({"THEME_FONT": " Open  Sans ", "THEME_HEADING_FONT": "Poppins"})
        self.assertEqual(theme["font"], "Open Sans")
        self.assertTrue(theme["font_stack"].startswith('"Open Sans", system-ui'))
        self.assertTrue(theme["heading_font_stack"].startswith('"Poppins"'))
        weighted, plain = theme["font_urls"]
        self.assertIn("family=Open+Sans:wght@400;500;600;700&family=Poppins:wght@400;500;600;700", weighted)
        self.assertIn("family=Open+Sans&family=Poppins&display=swap", plain)

    def test_heading_font_defaults_to_body_font(self):
        theme = load_theme({"THEME_FONT": "Nunito"})
        self.assertEqual(theme["heading_font"], "Nunito")
        self.assertEqual(len(theme["font_urls"]), 2)
        self.assertNotIn("family=Nunito&family=Nunito", theme["font_urls"][1])

    def test_invalid_font_falls_back_with_a_warning(self):
        with self.assertLogs("school_app.theme", "WARNING"):
            theme = load_theme({"THEME_FONT": 'Inter"; } body { color: red'})
        self.assertEqual((theme["font"], theme["font_urls"]), ("", []))

    def test_text_colour_on_primary_follows_contrast(self):
        light = load_theme({"THEME_PRIMARY_COLOR": "#facc15", "THEME_NAVBAR": "primary"})
        self.assertEqual(light["on_primary"], "#111827")
        self.assertFalse(light["navbar_dark"])
        dark = load_theme({"THEME_PRIMARY_COLOR": "#1e3a8a", "THEME_NAVBAR": "primary"})
        self.assertEqual(dark["on_primary"], "#ffffff")
        self.assertTrue(dark["navbar_dark"])


class ThemeRenderingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="lucy", password="pw", first_name="Lucy")
        self.client.force_login(self.user)

    def test_theme_reaches_pages(self):
        theme = load_theme({
            "THEME_PRESET": "forest", "THEME_MODE": "dark", "THEME_NAVBAR": "light",
            "APP_NAME": "Oak School", "THEME_LOGO_URL": "https://example.com/logo.png",
            "THEME_FOOTER_TEXT": "Oak School, Main Street 1",
        })
        with override_settings(THEME=theme):
            response = self.client.get(reverse("groups"))
        self.assertContains(response, f"--app-primary: {PRESETS['forest']['primary']};")
        self.assertContains(response, 'data-bs-theme="dark"')
        self.assertContains(response, "app-navbar-light")
        self.assertContains(response, "<title>Groups · Oak School</title>", html=False)
        self.assertContains(response, 'src="https://example.com/logo.png"')
        self.assertContains(response, "Oak School, Main Street 1")

    def test_theme_toggle_on_every_page(self):
        response = self.client.get(reverse("groups"))
        for choice in ("light", "dark", "auto"):
            self.assertContains(response, f'data-theme-choice="{choice}"')
        # Without a saved choice the page follows the device.
        self.assertContains(response, "var fallback = 'auto';")
        self.assertContains(response, "prefers-color-scheme: dark")
        self.client.logout()
        self.assertContains(self.client.get(reverse("login")), 'data-theme-choice="dark"')

    def test_deployment_default_mode(self):
        with override_settings(THEME=load_theme({"THEME_MODE": "dark"})):
            response = self.client.get(reverse("groups"))
        self.assertContains(response, "var fallback = 'dark';")
        self.assertContains(response, '<html lang="en" data-bs-theme="dark">')

    def test_font_reaches_pages(self):
        with override_settings(THEME=load_theme({"THEME_FONT": "Nunito"})):
            response = self.client.get(reverse("groups"))
        self.assertContains(response, 'href="https://fonts.googleapis.com/css2?family=Nunito')
        self.assertContains(response, '--app-font: "Nunito", system-ui')
        with override_settings(THEME=load_theme({})):
            self.assertNotContains(self.client.get(reverse("groups")), "fonts.googleapis.com")

    def test_auth_pages_use_the_theme(self):
        self.client.logout()
        with override_settings(THEME=load_theme({"APP_NAME": "Oak School"})):
            response = self.client.get(reverse("login"))
        self.assertContains(response, "Oak School")
        self.assertContains(response, "--app-primary:")

    def test_default_name_is_translated(self):
        # Without APP_NAME (independent of the local .env) the name is translated.
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "pl"
        with override_settings(THEME=load_theme({})):
            self.assertContains(self.client.get(reverse("groups")), "Aplikacja szkolna")

    def test_active_section_is_highlighted(self):
        response = self.client.get(reverse("groups"))
        self.assertContains(response, f'class="nav-link active" href="{reverse("groups")}"')


class UserPickerLabelTests(TestCase):
    def setUp(self):
        from accounts.models import UserRoles
        self.teacher = User.objects.create_user(username="t_kowalski", password="pw", first_name="Jan", last_name="Kowalski")
        self.teacher.profile.user_role = UserRoles.objects.create(user_role="Nauczyciel")
        self.teacher.profile.save()
        self.student = User.objects.create_user(username="zofia", first_name="Zofia", last_name="Mazur")
        self.student.profile.user_role = UserRoles.objects.create(user_role="Uczeń")
        self.student.profile.save()
        self.nameless = User.objects.create_user(username="anon_user")  # no name, no role
        self.client.force_login(self.teacher)

    def options(self, url, field):
        form = self.client.get(url).context["form"]
        return [label for _, label in form.fields[field].choices if _ != ""]

    def test_full_name_and_role_sorted_by_name(self):
        expected = ["anon_user", "Jan Kowalski (Nauczyciel)", "Zofia Mazur (Uczeń)"]
        self.assertEqual(self.options(reverse("announcement_create"), "users"), expected)
        self.assertEqual(self.options(reverse("message_create"), "recipients"), expected)
        self.assertEqual(self.options(reverse("gallery_create"), "users"), expected)
        self.assertEqual(self.options(reverse("group_create"), "members"), expected)

    def test_event_pickers_use_the_same_labels(self):
        form = self.client.get(reverse("calendar")).context["event_form"]
        labels = [label for _, label in form.fields["users"].choices]
        self.assertEqual(labels, ["anon_user", "Jan Kowalski (Nauczyciel)", "Zofia Mazur (Uczeń)"])

    def test_labels_shown_in_the_page(self):
        self.assertContains(self.client.get(reverse("announcement_create")), ">Zofia Mazur (Uczeń)</option>")


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class NotificationTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import Group
        from groups.models import GroupProfile
        self.teacher = User.objects.create_user(username="teacher", password="pw")
        self.student = User.objects.create_user(username="student", password="pw")
        self.parent = User.objects.create_user(username="parent", password="pw")
        self.parent.profile.affiliated_users.add(self.student)
        self.group = GroupProfile.objects.create(group=Group.objects.create(name="Class 1A"))
        self.group.members.add(self.student)

    def notify(self, user):
        self.client.force_login(user)
        return self.client.get(reverse("groups")).context["notify"]

    def test_announcements_counter(self):
        from announcements.models import Announcement
        announcement = Announcement.objects.create(author=self.teacher, title="Trip", text="x")
        announcement.groups.add(self.group)
        self.assertEqual(self.notify(self.teacher)["announcements"], "")  # own announcement
        self.assertEqual(self.notify(self.parent)["announcements"], "1")  # through the child
        self.assertEqual(self.notify(self.student)["announcements"], "1")
        response = self.client.get(reverse("groups"))
        self.assertContains(response, 'nav-count">1<')
        self.client.get(reverse("announcement_detail", args=[announcement.pk]))
        self.assertEqual(self.notify(self.student)["announcements"], "")
        self.assertNotContains(self.client.get(reverse("groups")), "nav-count")

    def test_messages_counter_counts_new_replies(self):
        from messages.models import Message, MessageThread
        thread = MessageThread.objects.create(title="Forms", author=self.teacher)
        thread.recipients.add(self.parent)
        Message.objects.create(thread=thread, sender=self.teacher, text="Hello")
        self.assertEqual(self.notify(self.teacher)["messages"], "")  # only own messages
        notify = self.notify(self.parent)
        self.assertEqual((notify["messages"], notify["thread_ids"]), ("1", {thread.pk}))
        self.assertContains(self.client.get(reverse("messages_page")), "is-unread")
        self.client.get(reverse("message_thread_detail", args=[thread.pk]))
        self.assertEqual(self.notify(self.parent)["messages"], "")
        # The parent's reply is not new for the parent, but is for the teacher
        self.client.post(reverse("reply_message", args=[thread.pk]), {"text": "Thanks"})
        self.assertEqual(self.notify(self.parent)["messages"], "")
        self.assertEqual(self.notify(self.teacher)["messages"], "1")

    def test_galleries_counter_new_and_updated(self):
        from media.models import Gallery
        from media.tests import image_upload
        gallery = Gallery.objects.create(owner=self.teacher, name="Trip")
        gallery.groups.add(self.group)
        self.assertEqual(self.notify(self.student)["galleries"], "1")
        self.assertEqual(self.notify(self.parent)["galleries"], "1")
        self.client.force_login(self.student)
        self.client.get(reverse("gallery_detail", args=[gallery.pk]))
        self.assertEqual(self.notify(self.student)["galleries"], "")
        # New images from the teacher make it new again for the student
        self.client.force_login(self.teacher)
        self.client.get(reverse("gallery_detail", args=[gallery.pk]))
        self.client.post(reverse("gallery_detail", args=[gallery.pk]), {"images": [image_upload("a.png")]})
        self.assertEqual(self.notify(self.teacher)["galleries"], "")  # uploader saw it after uploading
        self.assertEqual(self.notify(self.student)["galleries"], "1")

    def test_owner_does_not_see_own_new_gallery_as_new(self):
        self.client.force_login(self.teacher)
        self.client.post(reverse("gallery_create"), {"name": "Mine", "description": ""}, follow=True)
        self.assertEqual(self.notify(self.teacher)["galleries"], "")

    def test_badge_caps_at_99(self):
        from school_app.notifications import badge
        self.assertEqual((badge(5), badge(99), badge(150)), ("5", "99", "99+"))

    def test_counter_query_cost_is_fixed(self):
        from django.test import RequestFactory
        from school_app.notifications import notifications
        request = RequestFactory().get("/")
        request.user = self.parent
        with self.assertNumQueries(7):
            notifications(request)

    def test_new_comments_are_orange_and_counted_separately(self):
        from announcements.models import Announcement, AnnouncementComment
        announcement = Announcement.objects.create(author=self.teacher, title="Trip", text="x")
        announcement.groups.add(self.group)
        self.client.force_login(self.student)
        self.client.get(reverse("announcement_detail", args=[announcement.pk]))  # read it
        AnnouncementComment.objects.create(announcement=announcement, author=self.teacher, text="Bring lunch")
        AnnouncementComment.objects.create(announcement=announcement, author=self.parent, text="OK")
        notify = self.notify(self.student)
        self.assertEqual((notify["announcements"], notify["announcement_comments"]), ("", "2"))
        self.assertEqual(notify["comment_counts"], {announcement.pk: 2})
        response = self.client.get(reverse("announcements_page"))
        self.assertContains(response, 'class="badge rounded-pill text-bg-orange nav-count"')
        self.assertContains(response, '<i class="bi bi-chat-fill me-1"></i>2</span>')
        # The author gets the comments too (never opened it after publishing)
        self.assertEqual(self.notify(self.teacher)["announcement_comments"], "1")
        # Opening it clears the orange count
        self.client.force_login(self.student)
        self.client.get(reverse("announcement_detail", args=[announcement.pk]))
        self.assertEqual(self.notify(self.student)["announcement_comments"], "")
        # Own comments never count
        self.client.post(reverse("announcement_detail", args=[announcement.pk]), {"text": "Thanks"})
        self.assertEqual(self.notify(self.student)["announcement_comments"], "")

    def test_new_replies_are_orange_and_counted_per_message(self):
        from messages.models import Message, MessageThread
        thread = MessageThread.objects.create(title="Forms", author=self.teacher)
        thread.recipients.add(self.parent)
        Message.objects.create(thread=thread, sender=self.teacher, text="Hello")
        self.assertEqual(self.notify(self.parent)["messages"], "1")  # red: never opened
        self.client.get(reverse("message_thread_detail", args=[thread.pk]))
        Message.objects.create(thread=thread, sender=self.teacher, text="One more thing")
        Message.objects.create(thread=thread, sender=self.teacher, text="And another")
        notify = self.notify(self.parent)
        self.assertEqual((notify["messages"], notify["message_replies"]), ("", "2"))
        self.assertContains(self.client.get(reverse("messages_page")), '<i class="bi bi-chat-fill me-1"></i>2</span>')
        self.client.get(reverse("message_thread_detail", args=[thread.pk]))
        self.assertEqual(self.notify(self.parent)["message_replies"], "")
