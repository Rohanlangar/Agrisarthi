"""
Farmers App - URL Configuration
"""

from django.urls import path
from .views import ProfileView, FarmerDetailView, ProfileAutoFillView

urlpatterns = [
    path('profile/<uuid:farmer_id>/', ProfileView.as_view(), name='farmer-profile'),
    path('profile/auto-fill/', ProfileAutoFillView.as_view(), name='farmer-profile-auto-fill'),
    path('<uuid:farmer_id>/', FarmerDetailView.as_view(), name='farmer-detail'),
]
