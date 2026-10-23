"""Remembered sort order for list pages (announcements, messages)."""

SORTS = ("newest", "activity", "title")


def get_sort(request, key, default):
    """Sort chosen with ?sort=..., remembered in the session under ``key``."""
    sort = request.GET.get("sort")
    if sort in SORTS:
        request.session[key] = sort
        return sort
    saved = request.session.get(key)
    return saved if saved in SORTS else default
