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
from announcements.views import show_announcement_by_id,CreateAnnouncementView,EditAnnouncementView,AnnouncementDetailView,announcements_page
from events.views import events,event_editing
from groups import views as group_views
from messages.views import messages_page,CreateMessageView,show_message_thread_by_id,ReplyMessageView
from media.views import images_list,CreateImageView
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
    path("announcements/", announcements_page, name="announcements_page"),
    path("announcements/<int:pk>/", AnnouncementDetailView.as_view(), name="announcement_detail"),
    path("announcements/create/", CreateAnnouncementView.as_view(), name="announcement_create"),
    path("announcements/<int:pk>/edit/", EditAnnouncementView.as_view(), name="announcement_edit"),

    # Events URLs
    path('api/events/', events, name='events'),
    path('calendar/', event_editing, name='calendar'),

    #Groups URLs
    path('groups/', group_views.group_list, name='groups'),
    path("groups/<int:pk>/", group_views.group_detail, name="group_detail"),
    path("groups/create/", group_views.CreateGroupView.as_view(), name="group_create"),
    path("groups/<int:pk>/edit/", group_views.EditGroupView.as_view(), name="group_edit"),
    
    #Message URLs
    path("messages/", messages_page, name="messages_page"),
    path("messages/create/", CreateMessageView.as_view(), name="message_create"),
    path("messages/<int:pk>/", show_message_thread_by_id, name="message_thread_detail"),
    path("messages/<int:pk>/reply/", ReplyMessageView.as_view(), name="reply_message"),

    #Media URLs
    path("media/images/", CreateImageView.as_view(), name="images_list"),
]
