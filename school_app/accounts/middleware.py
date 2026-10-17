from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """Redirect users flagged with must_change_password to the password change page."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if (
            user.is_authenticated
            and hasattr(user, "profile")
            and user.profile.must_change_password
        ):
            allowed_paths = [
                reverse("password_change"),
                reverse("logout"),
                reverse("set_language"),
            ]
            static_url = "/" + settings.STATIC_URL.lstrip("/")
            if request.path not in allowed_paths and not request.path.startswith(
                static_url
            ):
                return redirect("password_change")
        return self.get_response(request)
