from django.urls import path
from app import views

urlpatterns = [
    path('index', views.index, name="index"),
]