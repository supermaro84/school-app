from typing import Any
from django.shortcuts import render,get_object_or_404,redirect
from .models import MessageThread, Message, MessageDocument, MessageImage, MessageThreadRead
from django.utils import timezone
from django.db.models import Max, Min
from school_app.sorting import get_sort
import datetime
from zoneinfo import ZoneInfo
from school_app.settings import TIME_ZONE
from django.views.generic import CreateView, UpdateView
from .forms import MessageReplyForm, MessageThreadForm
from media.forms import save_images
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.contrib import messages as django_messages
from django.utils.translation import gettext as _


def get_users_messages(user):
    message_threads = MessageThread.objects.all()
    user_threads = [message for message in message_threads if user in message.all_recipients]
    return user_threads

def sorted_threads(request):
    """The user's threads in the remembered order: "activity" (latest message,
    default), "newest" (first message) or "title" (A-Z)."""
    sort = get_sort(request, "message_sort", default="activity")
    threads = get_users_messages(request.user)
    if sort == "title":
        return sorted(threads, key=lambda t: t.title.casefold()), sort
    dates = {
        row["thread"]: row
        for row in Message.objects.filter(thread__in=threads)
        .values("thread")
        .annotate(first=Min("pub_date"), last=Max("pub_date"))
    }
    field = "last" if sort == "activity" else "first"
    # Threads without messages go last
    return sorted(threads, key=lambda t: (t.pk in dates, dates.get(t.pk, {}).get(field)), reverse=True), sort


def mark_thread_read(thread, user):
    # Messages from others after this moment count as new (navbar counter)
    MessageThreadRead.objects.update_or_create(thread=thread, user=user, defaults={"read_at": timezone.now()})


def messages_page(request):
    message_threads, sort = sorted_threads(request)
    return render(request, "messages_page.html", {"message_threads": message_threads, "sort": sort})


# Create your views here.
def show_message_thread_by_id(request, pk):
    message_thread = MessageThread.objects.get(pk=pk)
    messages = message_thread.messages.prefetch_related("images", "documents").order_by("pub_date")
    message_threads, sort = sorted_threads(request)
    # Logic to retrieve and display announcements
    if request.user not in message_thread.all_recipients:
        return redirect('messages_page')
    mark_thread_read(message_thread, request.user)
    return render(
        request,
        "message_thread_detail.html",
        {
            "message_threads": message_threads,
            "sort": sort,
            "thread": message_thread,
            "thread_messages": messages,
        },
    )


class CreateMessageView(CreateView):
    model = MessageThread
    template_name = "message_create.html"
    form_class = MessageThreadForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        thread = form.save()
        message = Message.objects.create(
            thread=thread, sender=self.request.user, text=form.cleaned_data["text"]
        )
        save_images(MessageImage, form.cleaned_data["images"], message=message)
        save_images(MessageDocument, form.cleaned_data["documents"], message=message)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message_threads"], context["sort"] = sorted_threads(self.request)
        return context

    def get_success_url(self):
        return reverse("message_thread_detail", kwargs={"pk": self.object.pk})


class ReplyMessageView(CreateView):
    model = Message
    template_name = "message_thread_reply.html"
    form_class = MessageReplyForm

    def dispatch(self, request, *args, **kwargs):
        thread_id = self.kwargs["pk"]
        thread = get_object_or_404(MessageThread, pk=thread_id)
        
        if request.user not in thread.all_recipients:
            django_messages.error(request, _("You don't have permission to reply to this message thread."))
            return redirect('messages_page')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        thread_id = self.kwargs["pk"]
        form.instance.thread = MessageThread.objects.get(pk=thread_id)
        form.instance.sender = self.request.user
        response = super().form_valid(form)
        save_images(MessageImage, form.cleaned_data["images"], message=self.object)
        save_images(MessageDocument, form.cleaned_data["documents"], message=self.object)
        return response

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["message_threads"], context["sort"] = sorted_threads(self.request)
        # The reply form sits under the thread, so show its messages too.
        thread = get_object_or_404(MessageThread, pk=self.kwargs["pk"])
        mark_thread_read(thread, self.request.user)
        context["thread"] = thread
        context["thread_messages"] = thread.messages.prefetch_related("images", "documents").order_by("pub_date")
        return context

    def get_success_url(self):
        return reverse("message_thread_detail", kwargs={"pk": self.object.thread.pk})
