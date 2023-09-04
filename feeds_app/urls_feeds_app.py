from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('text_story/', views.get_text_story),
    path('photo_story/', views.get_photo_story),
    path('public_post/', views.get_worldwide_post),
    path('private_post/', views.get_private_post),
    path('feed_likes/', views.get_post_likes),
    path('feed_comments/', views.get_post_likes),
    path('post_like/', views.post_feed_likes),
    path('post_comment/', views.post_feed_comments),
    path('club_post/', views.get_user_club_post),
]
