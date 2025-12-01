from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm
from announcements.models import Announcement
from accounts.models import UserProfile
from accounts.utils import get_affiliated_users
from django.contrib.auth.decorators import login_required


@login_required
def summary(request):
    affiliated_users = get_affiliated_users(request.user)
    return render(request, "landing.html", {"affiliated_users": affiliated_users})


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("landing")

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password.")
        return self.render_to_response(self.get_context_data(form=form))


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("landing")
    http_method_names = ["get", "post"]  # Allow both GET and POST


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get("username")
        messages.success(
            self.request, f"Account created for {username}! You can now log in."
        )
        return response
