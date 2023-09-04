from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('users_info/', views.get_user),
    path('edit_profile/', views.put_edit_userProfile),
    path('active_users/', views.get_active_user),
    path('active_friends/', views.get_active_friends),
    path('alltime_popular/', views.get_alltime_popular),
    path('weekly_popular/', views.get_weekly_popular),
    path('create_user/', views.post_create_user),
    path('user_exists/', views.get_user_existence),
]
