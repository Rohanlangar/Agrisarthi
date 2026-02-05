"""
Documents App - URL Configuration
"""

from django.urls import path
from .views import DocumentListView, DocumentDetailView

urlpatterns = [
    path('', DocumentListView.as_view(), name='document-list'),
    path('<uuid:document_id>/', DocumentDetailView.as_view(), name='document-detail'),
]
