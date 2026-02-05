"""
Applications App - URL Configuration
"""

from django.urls import path
from .views import (
    ApplicationListView, ApplySchemeView, ApplicationPreviewView,
    ApplicationStatusView, ApplicationDetailView
)

urlpatterns = [
    path('', ApplicationListView.as_view(), name='application-list'),
    path('apply/', ApplySchemeView.as_view(), name='apply-scheme'),
    path('preview/', ApplicationPreviewView.as_view(), name='application-preview'),
    path('<uuid:application_id>/', ApplicationDetailView.as_view(), name='application-detail'),
    path('<uuid:application_id>/status/', ApplicationStatusView.as_view(), name='application-status'),
]
