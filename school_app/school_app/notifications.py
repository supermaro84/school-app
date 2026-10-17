"""Navbar counters for the logged-in user.

Red: announcements and message threads not opened yet, and new or updated
galleries. Orange: new comments on announcements and new replies in threads
the user has already opened (or wrote), counted per comment/reply.

Announcements and galleries include what reaches affiliated users (a
guardian's children), as on their pages; message threads are the user's own.
Opening an item marks it as seen (AnnouncementRead, MessageThreadRead,
GalleryView), which lowers the count.
"""

from django.db.models import Case, Count, F, OuterRef, Q, Subquery, When
from django.db.models.functions import Coalesce

from accounts.utils import get_affiliated_users
from announcements.models import Announcement, AnnouncementComment, AnnouncementRead
from media.models import Gallery, GalleryView
from messages.models import Message, MessageThread, MessageThreadRead


def unread_announcement_count(user, people):
    return (
        Announcement.objects.filter(
            Q(users__in=people) | Q(groups__members__in=people) | Q(groups__admins__in=people)
        )
        .exclude(author=user)
        .exclude(reads__user=user)
        .distinct()
        .count()
    )


def new_comment_counts(user, people):
    """{announcement id: new comments by others} for announcements the user has
    opened (since their last visit) or wrote (since publishing, until opened)."""
    visible = Announcement.objects.filter(
        Q(users__in=people) | Q(groups__members__in=people) | Q(groups__admins__in=people) | Q(author=user)
    ).values("pk")
    last_seen = AnnouncementRead.objects.filter(
        announcement=OuterRef("announcement"), user=user
    ).values("last_seen_at")[:1]
    rows = (
        AnnouncementComment.objects.filter(announcement__in=visible)
        .exclude(author=user)
        .annotate(
            seen=Coalesce(
                Subquery(last_seen),
                Case(When(announcement__author=user, then=F("announcement__pub_date"))),
            )
        )
        .filter(seen__isnull=False, comment_date__gt=F("seen"))
        .values("announcement")
        .annotate(n=Count("pk"))
    )
    return {row["announcement"]: row["n"] for row in rows}


def my_thread_ids(user):
    return MessageThread.objects.filter(Q(author=user) | Q(recipients=user)).values("pk")


def unread_thread_ids(user):
    """Threads of ``user`` with messages from others that they never opened."""
    opened = MessageThreadRead.objects.filter(user=user).values("thread")
    return set(
        Message.objects.filter(thread__in=my_thread_ids(user))
        .exclude(sender=user)
        .exclude(thread__in=opened)
        .values_list("thread", flat=True)
        .distinct()
    )


def new_reply_counts(user):
    """{thread id: messages from others since the user last opened the thread}."""
    last_read = MessageThreadRead.objects.filter(thread=OuterRef("thread"), user=user).values("read_at")[:1]
    rows = (
        Message.objects.filter(thread__in=my_thread_ids(user))
        .exclude(sender=user)
        .annotate(seen=Subquery(last_read))
        .filter(seen__isnull=False, pub_date__gt=F("seen"))
        .values("thread")
        .annotate(n=Count("pk"))
    )
    return {row["thread"]: row["n"] for row in rows}


def unseen_gallery_ids(user, people):
    """Visible galleries never opened by ``user`` or updated since they last did."""
    visible = Gallery.objects.filter(
        Q(owner__in=people) | Q(users__in=people) | Q(groups__members__in=people) | Q(groups__admins__in=people)
    ).values("pk")
    last_view = GalleryView.objects.filter(gallery=OuterRef("pk"), user=user).values("viewed_at")[:1]
    return set(
        Gallery.objects.filter(pk__in=visible)
        .annotate(last_view=Subquery(last_view))
        .filter(Q(last_view__isnull=True) | Q(updated_at__gt=F("last_view")))
        .values_list("pk", flat=True)
    )


def badge(count):
    return "99+" if count > 99 else str(count)


def notifications(request):
    """Context processor: ``notify`` with counts (and ids for "New" badges in lists)."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    people = [user, *get_affiliated_users(user)]
    announcements = unread_announcement_count(user, people)
    comment_counts = new_comment_counts(user, people)
    thread_ids = unread_thread_ids(user)
    reply_counts = new_reply_counts(user)
    gallery_ids = unseen_gallery_ids(user, people)
    comments, replies = sum(comment_counts.values()), sum(reply_counts.values())
    return {
        "notify": {
            "announcements": badge(announcements) if announcements else "",
            "announcement_comments": badge(comments) if comments else "",
            "messages": badge(len(thread_ids)) if thread_ids else "",
            "message_replies": badge(replies) if replies else "",
            "galleries": badge(len(gallery_ids)) if gallery_ids else "",
            "thread_ids": thread_ids,
            "comment_counts": comment_counts,
            "reply_counts": reply_counts,
            "gallery_ids": gallery_ids,
        }
    }
