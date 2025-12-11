from django.shortcuts import render
from .models import UserProfile, User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def user_list(request):
    # Get filters from request
    search_term = request.GET.get('q', '')
    role = request.GET.get('role', '')
    
    # Base queryset
    users = User.objects.all()
    
    # Apply search
    if search_term:
        users = users.filter(
            Q(username__icontains=search_term) |
            Q(first_name__icontains=search_term) |
            Q(last_name__icontains=search_term) |
            Q(email__icontains=search_term)
        )
    
    # Apply role filter
    if role:
        users = users.filter(profile__user_role__user_role=role)
    
    # Order results
    users = users.order_by('username')
    
    # Create paginator (15 per page)
    paginator = Paginator(users, 5)
    page_num = request.GET.get('page', 1)
    users_page = paginator.get_page(page_num)
    
    # Get roles for dropdown
    from .models import UserRoles
    all_roles = UserRoles.objects.all()
    
    return render(request, "users.html", {
        "users_page": users_page,
        "search_term": search_term,
        "selected_role": role,
        "all_roles": all_roles
    })


@login_required
def user_detail(request, pk):
    user_profiles_list = UserProfile.objects.all()
    user_list = User.objects.all()
    user_list = sorted(user_list, key=lambda x: x.username, reverse=True)
    user_profile = UserProfile.objects.get(user__pk=pk)
    user_details = User.objects.get(pk=pk)
    return render(
        request,
        "user_detail.html",
        {
            "profile": user_profile,
            "users": user_list,
            "user_profiles": user_profiles_list,
        },
    )
