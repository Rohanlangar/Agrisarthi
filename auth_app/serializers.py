"""
Auth App - Serializers
"""

from rest_framework import serializers
import re


class PhoneLoginSerializer(serializers.Serializer):
    """Serializer for phone number login request"""
    phone = serializers.CharField(max_length=15, required=True)
    
    def validate_phone(self, value):
        """Validate phone number format"""
        # Remove any spaces or dashes
        phone = re.sub(r'[\s\-]', '', value)
        
        # Check if it's a valid Indian phone number (10 digits, optionally with +91)
        if phone.startswith('+91'):
            phone = phone[3:]
        elif phone.startswith('91') and len(phone) == 12:
            phone = phone[2:]
        
        if not phone.isdigit() or len(phone) != 10:
            raise serializers.ValidationError("Invalid phone number. Please enter a 10-digit Indian phone number.")
        
        return phone


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    phone = serializers.CharField(max_length=15, required=True)
    otp = serializers.CharField(max_length=6, min_length=4, required=True)
    
    def validate_phone(self, value):
        """Validate phone number format"""
        phone = re.sub(r'[\s\-]', '', value)
        if phone.startswith('+91'):
            phone = phone[3:]
        elif phone.startswith('91') and len(phone) == 12:
            phone = phone[2:]
        return phone
    
    def validate_otp(self, value):
        """Validate OTP format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response"""
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    farmer_id = serializers.UUIDField()
    is_new_user = serializers.BooleanField()
