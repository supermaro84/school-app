from django.shortcuts import render, redirect

# Create your views here.
from django.http import JsonResponse
from .forms import EventForm
from .models import Event
from django.views.generic import CreateView, UpdateView
from accounts.models import UserProfile
from groups.models import GroupProfile
from datetime import datetime, time
from django.db.models import Prefetch, Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime


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
                    }
                )
    return JsonResponse(events_list, safe=False)


def event_editing(request):
    if request.method == "POST":
        # Handle form submission
        print("POST received")
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.owner = UserProfile.objects.get(user=request.user)
            event.save()        
            form.save_m2m()
            event.users.add(event.owner)
            # Redirect to same page to prevent re-submission
            return redirect("calendar")
        else:
            print("Form errors:", form.errors)
    else:
        form = EventForm()
    return render(
        request, "calendar.html", {"event_form": form, "events": Event.objects.all()}
    )
