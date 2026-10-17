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

    def test_auth_pages_use_the_theme(self):
        self.client.logout()
        with override_settings(THEME=load_theme({"APP_NAME": "Oak School"})):
            response = self.client.get(reverse("login"))
        self.assertContains(response, "Oak School")
        self.assertContains(response, "--app-primary:")

    def test_default_name_is_translated(self):
        self.assertEqual(settings.THEME["app_name"], "")
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "pl"
        self.assertContains(self.client.get(reverse("groups")), "Aplikacja szkolna")

    def test_active_section_is_highlighted(self):
        response = self.client.get(reverse("groups"))
        self.assertContains(response, f'class="nav-link active" href="{reverse("groups")}"')
