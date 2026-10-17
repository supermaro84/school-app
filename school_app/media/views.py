from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

import os

from django.urls import reverse
from django.utils import timezone

from accounts.utils import get_affiliated_users
from announcements.models import AnnouncementDocument, AnnouncementImage
from announcements.views import get_announcements_for_user_and_affiliates
from events.models import Event, EventDocument
from groups.models import GroupProfile
from messages.models import MessageDocument, MessageImage
from messages.views import get_users_messages

from .forms import GalleryForm, GalleryUploadForm, save_images
from .models import DocumentFile, Gallery, GalleryImage, ImageFile


def owned_images(source, user):
    """Images of one source that ``user`` may delete.

    Sources: "upload" (loose uploads), "announcement", "message" and "gallery";
    gallery images can be deleted by their uploader and the gallery's owner.
    """
    if source == "upload":
        return ImageFile.objects.filter(owner=user)
    if source == "announcement":
        return AnnouncementImage.objects.filter(announcement__author=user).select_related("announcement")
    if source == "message":
        return MessageImage.objects.filter(message__sender=user).select_related("message__thread")
    if source == "gallery":
        return GalleryImage.objects.filter(Q(uploaded_by=user) | Q(gallery__owner=user)).select_related("gallery")
    raise Http404


def my_images(user):
    """All images ``user`` posted, newest first, each with where it is posted."""
    items = [{"image": image, "source": "upload"} for image in owned_images("upload", user)]
    items += [
        {"image": image, "source": "announcement", "post": image.announcement}
        for image in owned_images("announcement", user)
    ]
    items += [
        {"image": image, "source": "message", "post": image.message.thread}
        for image in owned_images("message", user)
    ]
    items += [
        {"image": image, "source": "gallery", "post": image.gallery}
        for image in GalleryImage.objects.filter(uploaded_by=user).select_related("gallery")
    ]
    return sorted(items, key=lambda item: item["image"].uploaded_at, reverse=True)


def visible_galleries(user, pk=None):
    """Galleries reaching ``user`` or their affiliated users (e.g. a guardian's children).

    Each gallery gets ``connected_users``: which of those people it reaches.
    ``pk`` limits the result to that one gallery.
    """
    people = [user] + list(get_affiliated_users(user))
    galleries = (
        Gallery.objects.filter(
            Q(owner__in=people)
            | Q(users__in=people)
            | Q(groups__members__in=people)
            | Q(groups__admins__in=people)
        )
        .filter(**({"pk": pk} if pk is not None else {}))
        .distinct()
        .select_related("owner")
        .prefetch_related(
            "users",
            Prefetch("groups", queryset=GroupProfile.objects.select_related("group").prefetch_related("admins", "members")),
            "images",
        )
    )
    galleries = list(galleries)
    for gallery in galleries:
        reached = gallery.recipients | {gallery.owner}
        gallery.connected_users = [person for person in people if person in reached]
    return galleries


def get_visible_gallery(user, pk):
    galleries = visible_galleries(user, pk)
    if not galleries:
        raise Http404
    return galleries[0]


@login_required
def media_page(request):
    show = request.GET.get("show", "all")
    galleries = visible_galleries(request.user)
    if show == "mine":
        galleries = [g for g in galleries if g.owner == request.user]
    elif show == "shared":
        galleries = [g for g in galleries if g.owner != request.user]
    else:
        show = "all"
    return render(
        request,
        "images_list.html",
        {
            "galleries": galleries,
            "show": show,
            "my_images": my_images(request.user),
        },
    )


@login_required
def gallery_create(request):
    form = GalleryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.instance.owner = request.user
        gallery = form.save()
        messages.success(request, _("Gallery created."))
        return redirect("gallery_detail", pk=gallery.pk)
    return render(request, "gallery_form.html", {"form": form})


@login_required
def gallery_edit(request, pk):
    gallery = get_object_or_404(Gallery, pk=pk, owner=request.user)
    form = GalleryForm(request.POST or None, instance=gallery)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Gallery saved."))
        return redirect("gallery_detail", pk=gallery.pk)
    return render(request, "gallery_form.html", {"form": form, "gallery": gallery})


@login_required
@require_POST
def gallery_delete(request, pk):
    gallery = get_object_or_404(Gallery, pk=pk, owner=request.user)
    gallery.delete()  # its images and their files go with it
    messages.success(request, _("Gallery deleted."))
    return redirect("images_list")


@login_required
def gallery_detail(request, pk):
    gallery = get_visible_gallery(request.user, pk)
    can_upload = gallery.can_upload(request.user)
    form = GalleryUploadForm()
    if request.method == "POST":
        if not can_upload:
            raise PermissionDenied
        form = GalleryUploadForm(request.POST, request.FILES)
        if form.is_valid():
            save_images(GalleryImage, form.cleaned_data["images"], gallery=gallery, uploaded_by=request.user)
            messages.success(request, _("Images added."))
            return redirect("gallery_detail", pk=gallery.pk)
    images = gallery.images.select_related("uploaded_by")
    for image in images:
        image.can_delete = request.user in (image.uploaded_by, gallery.owner)
    return render(
        request,
        "gallery_detail.html",
        {"gallery": gallery, "images": images, "can_upload": can_upload, "form": form},
    )


@login_required
@require_POST
def delete_image(request, source, pk):
    # Only images the user may delete are found; anything else is a 404.
    image = get_object_or_404(owned_images(source, request.user), pk=pk)
    image.delete()  # post_delete also removes the file from storage
    messages.success(request, _("Image deleted."))
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("images_list")


def owned_documents(source, user):
    """Documents of one source that ``user`` added and so may delete."""
    if source == "announcement":
        return AnnouncementDocument.objects.filter(announcement__author=user)
    if source == "message":
        return MessageDocument.objects.filter(message__sender=user)
    if source == "event":
        return EventDocument.objects.filter(event__owner__user=user)
    if source == "upload":
        return DocumentFile.objects.filter(owner=user)
    raise Http404


def visible_documents(user):
    """Documents attached to everything ``user`` can see, newest first.

    Announcements and events include what reaches affiliated users (a
    guardian's children); message threads are the user's own, as on the
    messages page. Documents uploaded in the admin (DocumentFile) are listed
    for their owner only.
    """
    people = [user] + list(get_affiliated_users(user))
    items = []
    announcements = get_announcements_for_user_and_affiliates(user)
    for doc in AnnouncementDocument.objects.filter(announcement__in=announcements).select_related("announcement__author"):
        post = doc.announcement
        items.append({"document": doc, "source": "announcement", "title": post.title,
                      "url": reverse("announcement_detail", args=[post.pk]), "uploader": post.author})
    threads = get_users_messages(user)
    for doc in MessageDocument.objects.filter(message__thread__in=threads).select_related("message__thread", "message__sender"):
        thread = doc.message.thread
        items.append({"document": doc, "source": "message", "title": thread.title,
                      "url": reverse("message_thread_detail", args=[thread.pk]), "uploader": doc.message.sender})
    events = Event.objects.filter(
        Q(users__user__in=people) | Q(groups__admins__in=people) | Q(groups__members__in=people)
    ).values("pk")
    for doc in EventDocument.objects.filter(event__in=events).select_related("event__owner__user"):
        event = doc.event
        day = timezone.localtime(event.event_start_time).date().isoformat()
        items.append({"document": doc, "source": "event", "title": event.event_name,
                      "url": f"{reverse('calendar')}?date={day}", "uploader": event.owner.user})
    for doc in DocumentFile.objects.filter(owner=user):
        doc.extension = os.path.splitext(doc.file.name)[1].lower().lstrip(".")
        doc.file_size = None
        items.append({"document": doc, "source": "upload", "title": "", "url": "", "uploader": user})
    for item in items:
        item["can_delete"] = item["uploader"] == user
    return sorted(items, key=lambda item: item["document"].uploaded_at, reverse=True)


@login_required
def documents_page(request):
    show = request.GET.get("show", "all")
    documents = visible_documents(request.user)
    if show == "mine":
        documents = [item for item in documents if item["can_delete"]]
    else:
        show = "all"
    return render(request, "documents.html", {"documents": documents, "show": show})


@login_required
@require_POST
def delete_document(request, source, pk):
    document = get_object_or_404(owned_documents(source, request.user), pk=pk)
    document.delete()  # post_delete also removes the file from storage
    messages.success(request, _("Document deleted."))
    return redirect("documents_page")

