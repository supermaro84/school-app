from django.contrib.auth.models import Group
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from accounts.utils import get_affiliated_users
from .models import GroupProfile
from django.urls import reverse
from django.views.generic import CreateView, UpdateView
from .forms import GroupForm, GroupEditForm


def group_list_context(request):
    """Groups for the sidebar list.

    By default only groups of the user and their affiliated users are listed;
    ?show=all lists every group. Each group gets ``connected_users``: the user
    and affiliates who are admins or members of it.
    """
    show_all = request.GET.get("show") == "all"
    if not request.user.is_authenticated:
        return {"groups": [], "show_all": show_all}

    people = [request.user] + list(get_affiliated_users(request.user))
    groups = (
        GroupProfile.objects.select_related("group")
        .prefetch_related("admins", "members")
        .order_by("group__name")
    )
    if not show_all:
        groups = groups.filter(
            Q(admins__in=people) | Q(members__in=people)
        ).distinct()

    groups = list(groups)
    for group in groups:
        in_group = set(group.admins.all()) | set(group.members.all())
        group.connected_users = [person for person in people if person in in_group]
    return {"groups": groups, "show_all": show_all}


@login_required
def group_list(request):
    """Show all groups and basic info."""
    return render(request, "groups.html", group_list_context(request))


@login_required
def group_detail(request, pk):
    """Show detailed info for one group."""
    group_profile = get_object_or_404(GroupProfile, pk=pk)
    return render(
        request,
        "group_detail.html",
        {
            **group_list_context(request),
            "group_profile": group_profile,
            "is_admin": request.user in group_profile.admins.all(),
            "is_member": request.user in group_profile.members.all(),
        },
    )


class CreateGroupView(LoginRequiredMixin, CreateView):
    model = GroupProfile
    template_name = "group_form.html"
    form_class = GroupForm

    def form_valid(self, form):
        form.instance.group = Group.objects.create(name=form.cleaned_data["name"])
        response = super().form_valid(form)  # saves description, admins, members
        group = self.object
        # The creator always manages the group; members also come from the
        # chosen groups; admins are never plain members as well.
        group.admins.add(self.request.user)
        group.members.set(form.new_members())
        group.drop_admins_from_members()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(group_list_context(self.request))
        return context

    def get_success_url(self):
        return reverse("group_detail", kwargs={"pk": self.object.pk})


class EditGroupView(LoginRequiredMixin, UpdateView):
    """Change a group's description, admins and members; group admins only."""

    model = GroupProfile
    form_class = GroupEditForm
    template_name = "group_edit.html"

    def get_object(self, queryset=None):
        group = super().get_object(queryset)
        if not group.admins.filter(pk=self.request.user.pk).exists():
            raise PermissionDenied
        return group

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.drop_admins_from_members()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(group_list_context(self.request))
        context["group"] = GroupProfile.objects.get(pk=self.kwargs["pk"]).group
        return context

    def get_success_url(self):
        return reverse("group_detail", kwargs={"pk": self.object.pk})
