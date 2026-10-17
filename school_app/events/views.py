from django.shortcuts import get_object_or_404, render, redirect

# Create your views here.
from django.http import JsonResponse
from .forms import EventEditForm, EventForm
from .models import Event, EventDocument
from media.forms import save_images
from django.views.generic import CreateView, UpdateView
from accounts.models import UserProfile
from groups.models import GroupProfile
from datetime import datetime, time
from django.db.models import Prefetch, Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST


def parse_range_param(value):
    """Parse FullCalendar's ``start``/``end`` query value (ISO date or datetime)."""
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        day = parse_date(value[:10])
        if day is None:
            return None
        parsed = datetime.combine(day, time.min)
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)
    return parsed


def events(request):
    """Calendar feed: events involving the user or their affiliated users.

    FullCalendar sends the visible range as ``start``/``end``; only events
    overlapping it are returned. One entry per event and involved person.
    """
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)
    affiliated = list(request.user.profile.affiliated_users.all())
    people = [request.user] + affiliated
    affiliated_usernames = [user.username for user in affiliated]

    matching = Event.objects.filter(
        Q(users__user__in=people) | Q(groups__admins__in=people) | Q(groups__members__in=people)
    ).values("pk")
    queryset = (
        Event.objects.filter(pk__in=matching)
        .select_related("owner__user", "status", "event_type")
        .prefetch_related(
            "documents",
            Prefetch("users", queryset=UserProfile.objects.select_related("user")),
            Prefetch(
                "groups",
                queryset=GroupProfile.objects.select_related("group").prefetch_related(
                    "admins", "members"
                ),
            ),
        )
        .order_by("event_start_time", "pk")
    )
    start = parse_range_param(request.GET.get("start"))
    end = parse_range_param(request.GET.get("end"))
    if start:
        queryset = queryset.filter(event_end_time__gte=start)
    if end:
        queryset = queryset.filter(event_start_time__lt=end)

    events_list = []
    for event in queryset:
        involved = event.all_involved_users  # computed once, from prefetched data
        can_edit = event.owner.user_id == request.user.id
        documents = [{"name": d.filename, "url": d.file.url} for d in event.documents.all()]
        for u in people:
            if u in involved:
                events_list.append(
                    {
                        "id": event.id,
                        "owner": event.owner.user.username,
                        "title": f"{event.event_name} ({u.username}) ",
                        "start": event.event_start_time.isoformat(),
                        "end": event.event_end_time.isoformat(),
                        "description": event.event_description,
                        "status": str(event.status),
                        "type": str(event.event_type),
                        "list_of_groups": event.list_of_groups,
                        "users": ", ".join([user.user.username for user in event.users.all()]),
                        "all_involved_users": [user.username for user in involved],
                        "affiliated_users": affiliated_usernames,
                        "can_edit": can_edit,
                        "documents": documents,
                        "edit_url": reverse("event_edit", args=[event.id]) if can_edit else "",
                    }
                )
    return JsonResponse(events_list, safe=False)


def event_editing(request):
    if request.method == "POST":
        # Handle form submission
        print("POST received")
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.owner = UserProfile.objects.get(user=request.user)
            event.save()        
            form.save_m2m()
            event.users.add(event.owner)
            save_images(EventDocument, form.cleaned_data["documents"], event=event)
            # Redirect to same page to prevent re-submission
            return redirect("calendar")
        else:
            print("Form errors:", form.errors)
    else:
        form = EventForm()
    # ?date=YYYY-MM-DD opens the calendar at that day (used after editing).
    initial_date = parse_date(request.GET.get("date", ""))
    return render(
        request,
        "calendar.html",
        {"event_form": form, "initial_date": initial_date.isoformat() if initial_date else ""},
    )


def get_own_event(request, pk):
    # Only the event's author may change it; for anyone else it doesn't exist.
    return get_object_or_404(Event, pk=pk, owner__user=request.user)


def calendar_at(event):
    day = timezone.localtime(event.event_start_time).date()
    return f"{reverse('calendar')}?date={day.isoformat()}"


@login_required
def event_edit(request, pk):
    event = get_own_event(request, pk)
    if request.method == "POST":
        form = EventEditForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save()
            event.users.add(event.owner)  # the author stays involved, as on create
            for document in form.cleaned_data["remove_documents"]:
                document.delete()
            save_images(EventDocument, form.cleaned_data["documents"], event=event)
            messages.success(request, _("Event saved."))
            return redirect(calendar_at(event))
    else:
        form = EventEditForm(instance=event)
    return render(request, "event_edit.html", {"form": form, "event": event})


@login_required
@require_POST
def event_delete(request, pk):
    event = get_own_event(request, pk)
    url = calendar_at(event)
    event.delete()
    messages.success(request, _("Event deleted."))
    return redirect(url)
