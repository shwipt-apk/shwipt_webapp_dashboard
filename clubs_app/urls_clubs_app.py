from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('user_clubs/', views.get_user_club),
    path('joined_clubs/', views.get_joined_club),
    path('explore_clubs/', views.get_explore_club),
    path('join_clubs/', views.post_join_club),
]
