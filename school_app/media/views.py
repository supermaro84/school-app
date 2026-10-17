from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView

from announcements.models import AnnouncementImage
from messages.models import MessageImage

from .models import DocumentFile, ImageFile
from .utils import compress_image


def owned_images(source, user):
    """Images of one source ("gallery", "announcement" or "message") posted by ``user``."""
    if source == "gallery":
        return ImageFile.objects.filter(owner=user)
    if source == "announcement":
        return AnnouncementImage.objects.filter(announcement__author=user).select_related("announcement")
    if source == "message":
        return MessageImage.objects.filter(message__sender=user).select_related("message__thread")
    raise Http404


def my_images(user):
    """All images ``user`` posted, newest first, each with where it is posted."""
    items = [{"image": image, "source": "gallery"} for image in owned_images("gallery", user)]
    items += [
        {"image": image, "source": "announcement", "post": image.announcement}
        for image in owned_images("announcement", user)
    ]
    items += [
        {"image": image, "source": "message", "post": image.message.thread}
        for image in owned_images("message", user)
    ]
    return sorted(items, key=lambda item: item["image"].uploaded_at, reverse=True)


class CreateImageView(LoginRequiredMixin, CreateView):
    model = ImageFile
    template_name = "images_list.html"
    success_url = "/media/images/"
    fields = ["file"]

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.file = compress_image(form.cleaned_data["file"])
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["my_images"] = my_images(self.request.user)
        context["documents"] = DocumentFile.objects.all()
        return context


@login_required
@require_POST
def delete_image(request, source, pk):
    # Only the poster's own images are found; anything else is a 404.
    image = get_object_or_404(owned_images(source, request.user), pk=pk)
    image.delete()  # post_delete also removes the file from storage
    messages.success(request, _("Image deleted."))
    return redirect("images_list")
