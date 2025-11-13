from django.contrib.auth.models import Group
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import GroupProfile


@login_required
def group_list(request):
    """Show all groups and basic info."""
    groups = GroupProfile.objects.select_related("group").all()
    return render(request, "groups.html", {"groups": groups})

@login_required
def group_detail(request, pk):
    """Show detailed info for one group."""
    groups = GroupProfile.objects.select_related("group").all()
    group_profile = get_object_or_404(GroupProfile, pk=pk)
    return render(request, "group_detail.html", {
        "groups": groups,
        "group_profile": group_profile,
        "is_admin": request.user in group_profile.admins.all(),
        "is_member": request.user in group_profile.members.all(),
    })