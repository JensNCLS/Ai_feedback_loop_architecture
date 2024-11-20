# api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('api/upload/', views.upload_image, name='upload_image'),
]
