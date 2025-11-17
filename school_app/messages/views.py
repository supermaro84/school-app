from typing import Any
from django.shortcuts import render
from .models import MessageThread, Message
import datetime
from zoneinfo import ZoneInfo
from school_app.settings import TIME_ZONE
from django.views.generic import CreateView,UpdateView
from .forms import MessageThreadForm
from django.urls import reverse


def messages_page(request):
    message_threads = MessageThread.objects.all()
    return render(request, "messages_page.html", {"message_threads": message_threads})
# Create your views here.
def show_message_thread_by_id(request, pk):
    message_thread = MessageThread.objects.get(pk=pk)
    messages = message_thread.messages.all().order_by('pub_date')
    message_threads = MessageThread.objects.all()
    # Logic to retrieve and display announcements
    return render(request, "message_thread_detail.html", {"message_threads": message_threads, "thread": message_thread, "messages": messages})

class CreateMessageView(CreateView):
    model = MessageThread
    template_name = 'message_create.html'
    form_class = MessageThreadForm
    def form_valid(self, form):
        form.instance.author = self.request.user
        thread = form.save()
        message = Message.objects.create(
            thread=thread,
            sender=self.request.user,
            text=form.cleaned_data['text']
        )
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = Message.objects.all().order_by('-pub_date')
        context['message_threads'] = MessageThread.objects.all()
        return context
    def get_success_url(self):
        return reverse('message_thread_detail', kwargs={'pk': self.object.pk})

class ReplyMessageView(CreateView):
    model = Message
    template_name = 'message_thread_reply.html'
    fields = ['text']
    def form_valid(self, form):
        thread_id = self.kwargs['pk']
        form.instance.thread = MessageThread.objects.get(pk=thread_id)
        form.instance.sender = self.request.user
        return super().form_valid(form)
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context=super().get_context_data(**kwargs)
        context['message_threads'] = MessageThread.objects.all()
        return context

    def get_success_url(self):
        return reverse('message_thread_detail', kwargs={'pk': self.object.thread.pk})