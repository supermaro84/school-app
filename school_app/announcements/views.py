from django.shortcuts import render, get_object_or_404
from .models import Announcement, AnnouncementComment
from .forms import AnnouncementForm, AnnouncementCommentForm
from django.views.generic import CreateView, UpdateView
import datetime
from zoneinfo import ZoneInfo
from school_app.settings import TIME_ZONE
from django.views.generic import DetailView
from django.views.generic.edit import FormMixin
from django.urls import reverse
from accounts.utils import get_affiliated_users, get_group_profiles_for_users_list
from accounts.models import UserProfile
from django.db.models import Q


def filter_announcements_for_user(user):
    group_profiles = UserProfile.objects.get(user=user).group_profiles
    announcements = (
        Announcement.objects.filter(
            Q(groups__in=group_profiles)  # Announcement's groups match user's groups
            | Q(users=user)  # Or user is directly assigned
            | Q(
                groups__isnull=True, users__isnull=True
            )  # Or public announcements (no groups/users)
        )
        .distinct()
        .order_by("-pub_date")
    )
    return announcements


def user_and_affiliates(user):
    affiliated_users = get_affiliated_users(user)
    return [user] + list(affiliated_users)


def get_announcements_for_user_and_affiliates(user):
    all_users = user_and_affiliates(user)
    all_group_profiles = get_group_profiles_for_users_list(all_users)
    announcements = []
    for a in Announcement.objects.all():
        if bool(set(all_users) & set(a.all_users)):
            announcements.append(a)
    return announcements


def get_own_announcements(user):
    print(user)
    print(Announcement.objects.filter(author=user).order_by("-pub_date"))
    return Announcement.objects.filter(author=user).order_by("-pub_date")


def filter_users_not_present_in_list(user_list, users_to_preserve):
    return [user for user in user_list if user in users_to_preserve]


def announcements_page(request):
    announcements = get_announcements_for_user_and_affiliates(request.user)
    announcements_data = [
        {
            "announcement": ann,
            "users_present": filter_users_not_present_in_list(
                ann.all_users, user_and_affiliates(request.user)
            ),
        }
        for ann in announcements
    ]
    own_announcements = get_own_announcements(request.user)
    return render(
        request,
        "announcements_page.html",
        {
            "announcements_data": announcements_data,
            "own_announcements": own_announcements,
        },
    )


class CreateAnnouncementView(CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "announcement_form.html"
    success_url = "/"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["announcements"] = filter_announcements_for_user(self.request.user)
        announcements = get_announcements_for_user_and_affiliates(self.request.user)
        announcements_data = [
            {
                "announcement": ann,
                "users_present": filter_users_not_present_in_list(
                    ann.all_users, user_and_affiliates(self.request.user)
                ),
            }
            for ann in announcements
        ]
        context["announcements_data"] = announcements_data
        context["own_announcements"] = get_own_announcements(self.request.user)
        return context

    def get_success_url(self):
        return reverse("announcement_detail", kwargs={"pk": self.object.pk})


class EditAnnouncementView(UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "announcement_edit_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["announcements"] = filter_announcements_for_user(self.request.user)
        announcements = get_announcements_for_user_and_affiliates(self.request.user)
        announcements_data = [
            {
                "announcement": ann,
                "users_present": filter_users_not_present_in_list(
                    ann.all_users, user_and_affiliates(self.request.user)
                ),
            }
            for ann in announcements
        ]
        context["announcements_data"] = announcements_data
        context["own_announcements"] = get_own_announcements(self.request.user)

        return context

    def get_success_url(self):
        return reverse("announcement_detail", kwargs={"pk": self.object.pk})


class CreateAnnouncementCommentView(CreateView):
    model = AnnouncementComment
    form_class = AnnouncementCommentForm
    template_name = "announcement.html"


class AnnouncementDetailView(FormMixin, DetailView):
    model = Announcement
    template_name = "announcement.html"
    context_object_name = "announcement"
    form_class = AnnouncementCommentForm

    def get_status(self, announcement):
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
        context["form"] = self.get_form()

        # Add the comments for the current announcement
        context["comments"] = (
            self.object.comments.all()
        )  # All comments related to this announcement
        context["status"] = self.get_status(self.object)
        context["announcements"] = filter_announcements_for_user(self.request.user)
        announcements = get_announcements_for_user_and_affiliates(self.request.user)
        announcements_data = [
            {
                "announcement": ann,
                "users_present": filter_users_not_present_in_list(
                    ann.all_users, user_and_affiliates(self.request.user)
                ),
            }
            for ann in announcements
        ]
        context["announcements_data"] = announcements_data
        context["own_announcements"] = get_own_announcements(self.request.user)
        if self.request.user == self.object.author:
            context["is_author"] = True
        else:
            context["is_author"] = False
        return context

    def get_success_url(self):
        return reverse("announcement_detail", kwargs={"pk": self.object.pk})

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
        form.instance.users.append(self.request.user)        
        form.save()
        return super().form_valid(form)
