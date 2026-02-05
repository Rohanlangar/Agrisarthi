"""
Voice App - URL Configuration
"""

from django.urls import path
from .views import VoiceProcessView, VoiceConfirmView

urlpatterns = [
    path('process/', VoiceProcessView.as_view(), name='voice-process'),
    path('confirm/', VoiceConfirmView.as_view(), name='voice-confirm'),
]
