from django.shortcuts import render, get_object_or_404,redirect
from .models import Announcement, AnnouncementComment, AnnouncementDocument, AnnouncementImage, AnnouncementRead
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
from django.db.models import Max, Q
from school_app.sorting import get_sort
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext as _
from media.forms import save_images



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
    return Announcement.objects.filter(author=user).order_by("-pub_date")


def filter_users_not_present_in_list(user_list, users_to_preserve):
    return [user for user in user_list if user in users_to_preserve]


def get_announcements_data(user):
    """Cards for the announcement list, with whether ``user`` has opened each one.

    The author's own announcements count as opened.
    """
    announcements = get_announcements_for_user_and_affiliates(user)
    people = user_and_affiliates(user)
    read_ids = set(
        AnnouncementRead.objects.filter(user=user).values_list(
            "announcement_id", flat=True
        )
    )
    return [
        {
            "announcement": ann,
            "users_present": filter_users_not_present_in_list(ann.all_users, people),
            "opened": ann.author_id == user.id or ann.pk in read_ids,
        }
        for ann in announcements
    ]


def sort_announcements_data(data, sort):
    """Sort cards: "newest" (published), "activity" (published, edited or
    commented, whichever is latest) or "title" (A-Z)."""
    if sort == "title":
        return sorted(data, key=lambda card: card["announcement"].title.casefold())
    if sort == "activity":
        ids = [card["announcement"].pk for card in data]
        last_comment = dict(
            AnnouncementComment.objects.filter(announcement__in=ids)
            .values("announcement")
            .annotate(latest=Max("comment_date"))
            .values_list("announcement", "latest")
        )

        def activity(card):
            ann = card["announcement"]
            return max(d for d in (ann.pub_date, ann.updated_at, last_comment.get(ann.pk)) if d)

        return sorted(data, key=activity, reverse=True)
    return sorted(data, key=lambda card: card["announcement"].pub_date, reverse=True)


def sorted_announcements_context(request):
    sort = get_sort(request, "announcement_sort", default="newest")
    return {
        "announcements_data": sort_announcements_data(get_announcements_data(request.user), sort),
        "sort": sort,
    }


def announcements_page(request):
    own_announcements = get_own_announcements(request.user)
    return render(
        request,
        "announcements_page.html",
        {
            **sorted_announcements_context(request),
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
        response = super().form_valid(form)
        save_images(AnnouncementImage, form.cleaned_data["images"], announcement=self.object)
        save_images(AnnouncementDocument, form.cleaned_data["documents"], announcement=self.object)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["announcements"] = filter_announcements_for_user(self.request.user)
        context.update(sorted_announcements_context(self.request))
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
        form.instance.updated_at = timezone.now()
        response = super().form_valid(form)
        for attachment in [*form.cleaned_data["remove_images"], *form.cleaned_data["remove_documents"]]:
            attachment.delete()
        save_images(AnnouncementImage, form.cleaned_data["images"], announcement=self.object)
        save_images(AnnouncementDocument, form.cleaned_data["documents"], announcement=self.object)
        return response
    
    def post(self, request, *args, **kwargs):
        # Handle delete action
        if 'delete' in request.POST:
            self.object = self.get_object()
            announcement_id = self.object.pk
            self.object.delete()
            messages.success(request, _('Announcement deleted successfully.'))
            return redirect('announcements_page')
        # Handle normal update
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["announcements"] = filter_announcements_for_user(self.request.user)
        context.update(sorted_announcements_context(self.request))
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

    def recipients_by_read_status(self, announcement):
        """Recipients (without the author), split into who opened it and who not.

        Each user gets ``read_at`` (when they first opened it) and ``role``.
        """
        reads = {r.user_id: r.read_at for r in announcement.reads.all()}
        recipients = [user for user in announcement.all_users if user != announcement.author]
        profiles = UserProfile.objects.filter(user__in=recipients).select_related("user_role")
        roles = {p.user_id: p.user_role for p in profiles}
        for user in recipients:
            user.read_at = reads.get(user.pk)
            user.role = roles.get(user.pk)
        recipients.sort(key=lambda u: ((u.get_full_name() or u.username).lower()))
        return {
            "recipients": recipients,
            "recipients_read": [u for u in recipients if u.read_at],
            "recipients_unread": [u for u in recipients if not u.read_at],
        }

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
        context.update(self.recipients_by_read_status(self.object))
        context["announcements"] = filter_announcements_for_user(self.request.user)
        context.update(sorted_announcements_context(self.request))
        context["own_announcements"] = get_own_announcements(self.request.user)
        if self.request.user == self.object.author:
            context["is_author"] = True
        else:
            context["is_author"] = False
        return context

    def get_success_url(self):
        return reverse("announcement_detail", kwargs={"pk": self.object.pk})

    def get(self, request, *args, **kwargs):
        # Opening the detail page marks the announcement as read for this user.
        # Recorded before rendering so the card in the list already shows it.
        self.object = self.get_object()
        if request.user.is_authenticated:
            read, created = AnnouncementRead.objects.get_or_create(
                announcement=self.object, user=request.user
            )
            if not created:
                read.last_seen_at = timezone.now()
                read.save(update_fields=["last_seen_at"])
        return self.render_to_response(self.get_context_data(object=self.object))

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
        #form.instance.users.append(self.request.user)        
        form.save()
        return super().form_valid(form)
