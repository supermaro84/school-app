from django.shortcuts import render,get_object_or_404
from .models import Announcement
from .forms import AnnouncementForm
from django.views.generic import CreateView,UpdateView
import datetime
from zoneinfo import ZoneInfo
from school_app.settings import TIME_ZONE
 
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
    
class EditAnnouncementView(UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcement_edit_form.html'
    success_url = '/'
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)