from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('details/', views.get_admin_details),
    path('update/', views.put_admin_count),
]
