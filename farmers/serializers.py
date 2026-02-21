"""
Farmers App - Serializers
Updated with OCR auto-fill fields (crops, date_of_birth, aadhaar_last_four, survey_number)
"""

from rest_framework import serializers
from .models import Farmer


class FarmerSerializer(serializers.ModelSerializer):
    """Full farmer profile serializer"""
    is_profile_complete = serializers.ReadOnlyField()
    calculated_age = serializers.ReadOnlyField()
    
    class Meta:
        model = Farmer
        fields = [
            'id', 'phone', 'name', 'state', 'district', 'village',
            'land_size', 'crop_type', 'crops', 'survey_number',
            'land_type', 'has_irrigation', 'farming_category',
            'social_category', 'gender', 'date_of_birth', 'age',
            'calculated_age', 'aadhaar_last_four',
            'annual_income', 'is_bpl',
            'language', 'is_active',
            'is_profile_complete', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'phone', 'is_active', 'created_at', 'updated_at']


class FarmerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating farmer profile"""
    
    class Meta:
        model = Farmer
        fields = [
            'name', 'state', 'district', 'village',
            'land_size', 'crop_type', 'crops', 'survey_number',
            'land_type', 'has_irrigation', 'farming_category',
            'social_category', 'gender', 'date_of_birth', 'age',
            'aadhaar_last_four', 'annual_income', 'is_bpl',
            'language',
        ]
    
    def validate_land_size(self, value):
        if value < 0:
            raise serializers.ValidationError("Land size cannot be negative.")
        return value
    
    def validate_name(self, value):
        if value and len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value
    
    def validate_crops(self, value):
        if value is not None and not isinstance(value, list):
            raise serializers.ValidationError("Crops must be a list.")
        return value
    
    def validate_aadhaar_last_four(self, value):
        if value and (len(value) != 4 or not value.isdigit()):
            raise serializers.ValidationError("Aadhaar last four must be exactly 4 digits.")
        return value


class FarmerOCRAutoFillSerializer(serializers.Serializer):
    """
    Serializer for auto-filling farmer profile from OCR data.
    Combines Aadhaar + 7/12 extracted data + crop selection.
    """
    # From Aadhaar OCR
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=['male', 'female', 'other'],
        required=False, allow_blank=True
    )
    aadhaar_last_four = serializers.CharField(
        max_length=4, required=False, allow_blank=True
    )
    
    # From 7/12 OCR
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    district = serializers.CharField(max_length=100, required=False, allow_blank=True)
    village = serializers.CharField(max_length=100, required=False, allow_blank=True)
    land_size = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, default=0
    )
    survey_number = serializers.CharField(
        max_length=50, required=False, allow_blank=True
    )
    
    # User-selected
    crops = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=True,
        min_length=1,
    )
    language = serializers.ChoiceField(
        choices=['hindi', 'marathi', 'english'],
        required=False, default='hindi'
    )
    
    def validate_crops(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError("Please select at least one crop.")
        return value


class FarmerMinimalSerializer(serializers.ModelSerializer):
    """Minimal farmer info for listings"""
    
    class Meta:
        model = Farmer
        fields = ['id', 'name', 'phone', 'state', 'district']
