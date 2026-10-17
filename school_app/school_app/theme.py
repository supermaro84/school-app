"""Deployment theme: colours, name, logo and mode, read from environment variables.

Each deployment sets these in its .env (see .env.example); nothing is stored in
the database. ``load_theme()`` runs once at startup (settings.THEME) and the
``theme`` context processor exposes the result to every template, where
base.html turns it into Bootstrap CSS variables.
"""

import logging
import re

from django.conf import settings
from django.utils.translation import gettext

logger = logging.getLogger(__name__)

PRESETS = {
    "default": {"primary": "#2563eb", "secondary": "#64748b"},
    "ocean": {"primary": "#0e7490", "secondary": "#475569"},
    "forest": {"primary": "#15803d", "secondary": "#57534e"},
    "sunset": {"primary": "#ea580c", "secondary": "#6b7280"},
    "plum": {"primary": "#7c3aed", "secondary": "#64748b"},
}
NAVBAR_STYLES = ("dark", "light", "primary")
MODES = ("light", "dark", "auto")

HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def normalize_hex(value):
    """'#abc' -> '#aabbcc'; returns None for anything that isn't a hex colour."""
    value = (value or "").strip()
    if not HEX_COLOR.match(value):
        return None
    if len(value) == 4:
        value = "#" + "".join(c * 2 for c in value[1:])
    return value.lower()


def hex_to_rgb(value):
    return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))


def is_light(value):
    """True if dark text reads better than white text on this colour."""
    r, g, b = hex_to_rgb(value)
    # Relative luminance (WCAG), compared with the point where black and
    # white text have equal contrast.
    def channel(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    luminance = 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
    return luminance > 0.179


def _choice(env, name, allowed, default):
    value = (env.get(name) or "").strip().lower()
    if not value:
        return default
    if value not in allowed:
        logger.warning("%s=%r is not one of %s; using %r.", name, value, ", ".join(allowed), default)
        return default
    return value


def _color(env, name, default):
    raw = env.get(name)
    if not raw:
        return default
    value = normalize_hex(raw)
    if value is None:
        logger.warning("%s=%r is not a hex colour like #2563eb; using %s.", name, raw, default)
        return default
    return value


def load_theme(env):
    """Build the theme dict from a mapping of environment variables."""
    preset_name = _choice(env, "THEME_PRESET", tuple(PRESETS), "default")
    preset = PRESETS[preset_name]
    primary = _color(env, "THEME_PRIMARY_COLOR", preset["primary"])
    secondary = _color(env, "THEME_SECONDARY_COLOR", preset["secondary"])
    navbar = _choice(env, "THEME_NAVBAR", NAVBAR_STYLES, "dark")
    return {
        "preset": preset_name,
        "app_name": (env.get("APP_NAME") or "").strip(),
        "primary": primary,
        "primary_rgb": ", ".join(map(str, hex_to_rgb(primary))),
        "on_primary": "#111827" if is_light(primary) else "#ffffff",
        "secondary": secondary,
        "secondary_rgb": ", ".join(map(str, hex_to_rgb(secondary))),
        "navbar": navbar,
        # Navbars with a dark background get light text (data-bs-theme="dark").
        "navbar_dark": navbar == "dark" or (navbar == "primary" and not is_light(primary)),
        # Default colour mode; each viewer can switch with the theme toggle.
        "mode": _choice(env, "THEME_MODE", MODES, "auto"),
        "logo_url": (env.get("THEME_LOGO_URL") or "").strip(),
        "favicon_url": (env.get("THEME_FAVICON_URL") or "").strip(),
        "footer_text": (env.get("THEME_FOOTER_TEXT") or "").strip(),
    }


def theme(request):
    """Context processor: ``theme``, ``app_name`` and ``nav_section`` for every template."""
    current = settings.THEME
    # The deployment's name is shown as configured; the default is translated.
    return {
        "theme": current,
        "app_name": current["app_name"] or gettext("School App"),
        # First URL segment ("announcements", "calendar", ...) to highlight the navbar.
        "nav_section": request.path.strip("/").split("/")[0],
    }
