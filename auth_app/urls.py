"""
Auth App - URL Configuration
"""

from django.urls import path
from .views import LoginView, VerifyOTPView, RefreshTokenView, LogoutView

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('verify/', VerifyOTPView.as_view(), name='auth-verify'),
    path('refresh/', RefreshTokenView.as_view(), name='auth-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
]
