from django.contrib.auth.models import Group
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import GroupProfile
from django.urls import reverse
from django.views.generic import CreateView,UpdateView
from .forms import GroupForm,GroupEditForm


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

class CreateGroupView(CreateView):
    model = GroupProfile
    template_name = 'group_form.html'
    form_class = GroupForm
    
    def form_valid(self, form):
        # 1. Create the base Django Group
        group_name = self.request.POST.get('name')
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
        context['groups'] = GroupProfile.objects.all()
        return context
    def get_success_url(self):
        return reverse('group_detail', kwargs={'pk': self.object.pk})

class EditGroupView(UpdateView):
    model = GroupProfile
    form_class = GroupEditForm
    template_name = 'group_edit.html'
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = GroupProfile.objects.all()
        context['group'] = GroupProfile.objects.get(pk=self.kwargs['pk']).group
        return context
    def get_success_url(self):
        return reverse('group_detail', kwargs={'pk': self.object.pk})
