from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib import messages
from django.utils.translation import gettext as _
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm
from announcements.models import Announcement
from announcements.views import get_announcements_data
from accounts.models import UserProfile
from accounts.utils import get_affiliated_users
from events.models import Event
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta


@login_required
def summary(request):
    affiliated_users = UserProfile.objects.get(user=request.user).user_and_affiliated_usernames
    affiliated_profiles = UserProfile.objects.filter(user__in=affiliated_users)
    today = timezone.now()
    two_days_ahead = today + timedelta(days=2)
    events = Event.objects.filter(
        Q(users__in=affiliated_profiles) | 
        Q(groups__admins__in=affiliated_users) | 
        Q(groups__members__in=affiliated_users),event_start_time__gte=today,
        event_start_time__lte=two_days_ahead
    ).select_related("event_type", "status").distinct().order_by("event_start_time")
    # Who each event involves, worked out once per event rather than per tab.
    involved = [(event, event.all_involved_users) for event in events]
    # Read status is the logged-in user's, as on the announcements page.
    announcements_data = get_announcements_data(request.user)
    for user in affiliated_users:
        user.upcoming_events = [event for event, people in involved if user in people]
        user.event_count = len(user.upcoming_events)
        user.announcement_items = [
            item for item in announcements_data if user in item["users_present"]
        ]
        user.unread_count = sum(1 for item in user.announcement_items if not item["opened"])
    return render(request, "landing.html", {"affiliated_users": affiliated_users, "events": events})



class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('landing')
    
    def form_invalid(self, form):
        messages.error(self.request, _('Invalid username or password.'))
        return self.render_to_response(self.get_context_data(form=form))


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('landing')
    http_method_names = ['get', 'post']  # Allow both GET and POST


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('landing')

    def form_valid(self, form):
        response = super().form_valid(form)
        profile = self.request.user.profile
        if profile.must_change_password:
            profile.must_change_password = False
            profile.save(update_fields=['must_change_password'])
        messages.success(self.request, _('Your password has been changed.'))
        return response


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        messages.success(
            self.request,
            _('Account created for %(username)s! You can now log in.') % {'username': username},
        )
        return response


