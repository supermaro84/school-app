from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm
from announcements.models import Announcement


# Create your views here.
def index(request):
    announcements = Announcement.objects.all()
    announcements=(sorted(announcements, key=lambda x: x.pub_date, reverse=True))
    return render(request, "landing.html", {"announcements": announcements})


def announcements_page(request):
    announcements = Announcement.objects.all()
    announcements = sorted(announcements, key=lambda x: x.pub_date, reverse=True)
    return render(request, "announcements_page.html", {"announcements": announcements})
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
