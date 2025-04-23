from django.urls import path
from . import views

urlpatterns = [
    path('api/check_analysis_status/<int:preprocessed_image_id>/', views.check_analysis_status, name='check_analysis_status'),
    path('api/feedback/', views.submit_feedback, name='feedback'),
    path('api/review-items/', views.get_review_items, name='get_review_items'),
    path('api/review-items/<int:feedback_id>/', views.get_review_detail, name='get_review_detail'),
    path('api/review-items/<int:feedback_id>/submit', views.submit_review, name='submit_review'),
    path('api/image/<int:image_id>/', views.get_image, name='get_image'),
]
