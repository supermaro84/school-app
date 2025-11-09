from django.shortcuts import render,redirect

# Create your views here.
from django.http import JsonResponse
from .forms import EventForm
from .models import Event
from django.views.generic import CreateView,UpdateView


def events(request):
    events_list = []
    for event in Event.objects.all():
        events_list.append({
            "id": event.id,
            "title": event.event_name,
            "start": event.event_start_time.isoformat(),
            "end": event.event_end_time.isoformat(),
            "description": event.event_description,
            'status': event.status.value if hasattr(event.status, 'value') else str(event.status),
            "type": event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
        })
    return JsonResponse(events_list, safe=False)


def event_editing(request):
    if request.method == 'POST':
        # Handle form submission
        print("POST received")
        form = EventForm(request.POST)
        if form.is_valid():
            print("Form is valid")
            event = form.save(commit=False)
            event.owner = request.user
            event.save()
            form.save_m2m()
            # Redirect to same page to prevent re-submission
            return redirect('calendar')
        else:
            print("Form errors:", form.errors)
        # If form has errors, fall through to render with errors
    else:
        print("!didnt save??")
        # GET request - show empty form
        form = EventForm()
    return render(request, "calendar.html", {'event_form': form,'events':Event.objects.all()})