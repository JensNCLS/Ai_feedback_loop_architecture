from django.urls import path
from . import views

urlpatterns = [
    path('api/check_analysis_status/<int:preprocessed_image_id>/', views.check_analysis_status, name='check_analysis_status'),
]
