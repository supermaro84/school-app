from django.shortcuts import render
from .models import UserProfile, User
from django.contrib.auth.decorators import login_required


@login_required
def user_list(request):
    user_profiles_list = UserProfile.objects.all()
    user_list = User.objects.all()
    user_list = sorted(user_list, key=lambda x: x.username, reverse=True)
    return render(request, "users.html", {"users": user_list})


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
