from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from media.tests import IN_MEMORY_STORAGES, image_upload
from messages.models import Message, MessageThread


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class MessageImageTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teacher", password="pw")
        self.parent = User.objects.create_user(username="parent", password="pw")
        self.client.force_login(self.teacher)

    def test_new_thread_with_images(self):
        response = self.client.post(
            reverse("message_create"),
            {
                "title": "Trip",
                "recipients": [self.parent.pk],
                "text": "Photos from today",
                "images": [image_upload("a.png"), image_upload("b.png")],
            },
        )
        thread = MessageThread.objects.get(title="Trip")
        self.assertRedirects(response, reverse("message_thread_detail", args=[thread.pk]))
        message = thread.messages.get()
        self.assertEqual(
            sorted(img.file.name for img in message.images.all()),
            [f"messages/teacher/{thread.pk}/a.jpg", f"messages/teacher/{thread.pk}/b.jpg"],
        )

    def test_reply_with_image_is_shown_in_thread(self):
        thread = MessageThread.objects.create(title="Trip", author=self.teacher)
        thread.recipients.add(self.parent)
        Message.objects.create(thread=thread, sender=self.teacher, text="Hello")
        self.client.force_login(self.parent)

        self.client.post(
            reverse("reply_message", args=[thread.pk]),
            {"text": "Here is the form", "images": [image_upload("form.png")]},
        )
        reply = thread.messages.get(text="Here is the form")
        self.assertEqual(reply.images.get().file.name, f"messages/parent/{thread.pk}/form.jpg")

        response = self.client.get(reverse("message_thread_detail", args=[thread.pk]))
        self.assertContains(response, 'class="img-thumbnail', count=1)

    def test_reply_page_shows_the_thread(self):
        thread = MessageThread.objects.create(title="Trip", author=self.teacher)
        Message.objects.create(thread=thread, sender=self.teacher, text="Hello there")
        response = self.client.get(reverse("reply_message", args=[thread.pk]))
        self.assertContains(response, "Hello there")
        self.assertContains(response, 'enctype="multipart/form-data"')
