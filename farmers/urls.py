"""
Farmers App - URL Configuration
"""

from django.urls import path
from .views import ProfileView, FarmerDetailView

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='farmer-profile'),
    path('<uuid:farmer_id>/', FarmerDetailView.as_view(), name='farmer-detail'),
]
