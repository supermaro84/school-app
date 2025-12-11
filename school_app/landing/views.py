from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm
from announcements.models import Announcement
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
    ).distinct()
    user_event_counts = {}
    for user in affiliated_users:
        user.event_count = sum(1 for event in events if user in event.all_involved_users)
    return render(request, "landing.html", {"affiliated_users": affiliated_users, "events": events})



class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('landing')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password.')
        return self.render_to_response(self.get_context_data(form=form))


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('landing')
    http_method_names = ['get', 'post']  # Allow both GET and POST


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        messages.success(self.request, f'Account created for {username}! You can now log in.')
        return response


