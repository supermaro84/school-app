from django.contrib.auth.models import Group
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
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


class CreateGroupView(CreateView):
    model = GroupProfile
    template_name = "group_form.html"
    form_class = GroupForm

    def form_valid(self, form):
        # 1. Create the base Django Group
        group_name = self.request.POST.get("name")
        if not group_name:
            form.add_error(None, "Group name is required.")
            return self.form_invalid(form)

        group = Group.objects.create(name=group_name)

        # 2. Assign it to the GroupProfile
        form.instance.group = group

        # 3. Optionally, add the creator as admin/member
        form.instance.save()
        form.instance.admins.add(self.request.user)
        form.instance.members.add(self.request.user)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(group_list_context(self.request))
        return context

    def get_success_url(self):
        return reverse("group_detail", kwargs={"pk": self.object.pk})


class EditGroupView(UpdateView):
    model = GroupProfile
    form_class = GroupEditForm
    template_name = "group_edit.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(group_list_context(self.request))
        context["group"] = GroupProfile.objects.get(pk=self.kwargs["pk"]).group
        return context

    def get_success_url(self):
        return reverse("group_detail", kwargs={"pk": self.object.pk})
