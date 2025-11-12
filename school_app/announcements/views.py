from django.shortcuts import render,get_object_or_404
from .models import Announcement, AnnouncementComment
from .forms import AnnouncementForm, AnnouncementCommentForm
from django.views.generic import CreateView,UpdateView
import datetime
from zoneinfo import ZoneInfo
from school_app.settings import TIME_ZONE
from django.views.generic import DetailView
from django.views.generic.edit import FormMixin
from django.urls import reverse



def announcements_page(request):
    announcements = Announcement.objects.all()
    announcements = sorted(announcements, key=lambda x: x.pub_date, reverse=True)
    return render(request, "announcements_page.html", {"announcements": announcements})
# Create your views here.
def show_announcement_by_id(request, pk):
    announcement = Announcement.objects.get(pk=pk)
    def get_status(announcement):
        if announcement.exp_date is None:
            return "Unlimited"
        elif announcement.exp_date > datetime.datetime.now(tz=ZoneInfo(TIME_ZONE)):
            return "Active"
        elif announcement.exp_date < datetime.datetime.now(tz=ZoneInfo(TIME_ZONE)):
            return "Expired"
    # Logic to retrieve and display announcements
    return render(request, "announcement.html", {"announcement": announcement,"expired":get_status(announcement)})

class CreateAnnouncementView(CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcement_form.html'
    success_url = '/'
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['announcements'] = Announcement.objects.all().order_by('-pub_date')
        return context
    def get_success_url(self):
        return reverse('announcement_detail', kwargs={'pk': self.object.pk})
class EditAnnouncementView(UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcement_edit_form.html'
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['announcements'] = Announcement.objects.all().order_by('-pub_date')
        return context
    def get_success_url(self):
        return reverse('announcement_detail', kwargs={'pk': self.object.pk})    

class CreateAnnouncementCommentView(CreateView):
    model = AnnouncementComment
    form_class = AnnouncementCommentForm
    template_name = 'announcement.html'


class AnnouncementDetailView(FormMixin, DetailView):
    model = Announcement
    template_name = 'announcement.html'
    context_object_name = 'announcement'
    form_class = AnnouncementCommentForm

    def get_status(self,announcement):
        if announcement.exp_date is None:
            return "Unlimited"
        elif announcement.exp_date > datetime.datetime.now(tz=ZoneInfo(TIME_ZONE)):
            return "Active"
        elif announcement.exp_date < datetime.datetime.now(tz=ZoneInfo(TIME_ZONE)):
            return "Expired"
    # Logic to retrieve and display announc

    def get_context_data(self, **kwargs):
        # Get the default context data
        context = super().get_context_data(**kwargs)

        # Add the form to the context
        context['form'] = self.get_form()

        # Add the comments for the current announcement
        context['comments'] = self.object.comments.all()  # All comments related to this announcement
        context['status'] = self.get_status(self.object)
        context['announcements'] = Announcement.objects.all().order_by('-pub_date')
        return context

    def get_success_url(self):
        return reverse('announcement_detail', kwargs={'pk': self.object.pk})

    def post(self, request, *args, **kwargs):
        # self.get_object() loads the announcement
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        # Assign the logged-in user and related announcement
        form.instance.author = self.request.user
        form.instance.announcement = self.get_object()
        form.save()
        return super().form_valid(form)