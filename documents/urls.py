"""
Documents App - URL Configuration
Updated with OCR extraction endpoints for onboarding flow
"""

from django.urls import path
from .views import (
    DocumentListView, DocumentDetailView,
    DocumentByFarmerView, OCRAadhaarView, OCRSevenTwelveView
)

urlpatterns = [
    # OCR extraction endpoints (new onboarding flow)
    path('ocr/aadhaar/', OCRAadhaarView.as_view(), name='ocr-aadhaar'),
    path('ocr/seven-twelve/', OCRSevenTwelveView.as_view(), name='ocr-seven-twelve'),
    
    # Document CRUD
    path('', DocumentListView.as_view(), name='document-list'),
    path('farmer/<uuid:farmer_id>/', DocumentByFarmerView.as_view(), name='document-by-farmer'),
    path('document/<uuid:document_id>/', DocumentDetailView.as_view(), name='document-detail'),
]
