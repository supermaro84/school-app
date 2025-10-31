"""
URL configuration for school_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from landing import views
from landing.views import CustomLoginView, CustomLogoutView, SignUpView
from announcements.views import show_announcement_by_id,CreateAnnouncementView,EditAnnouncementView

urlpatterns = [
    path("", views.index, name="landing"),
    path("admin/", admin.site.urls),
    
    # Authentication URLs
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("signup/", SignUpView.as_view(), name="signup"),
    
    # Password reset URLs
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

    # Announcement URLs
    path("announcements/<int:pk>/", show_announcement_by_id, name="announcement_detail"),
    path("announcements/create/", CreateAnnouncementView.as_view(), name="announcement_create"),
    path("announcements/<int:pk>/edit/", EditAnnouncementView.as_view(), name="announcement_edit"),
]
