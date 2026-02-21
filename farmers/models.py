"""
Farmers App - Enhanced Farmer Model
With additional fields for robust eligibility matching.
Supports OCR auto-fill from Aadhaar and 7/12 documents.
"""

import uuid
from datetime import date
from django.db import models


class Farmer(models.Model):
    """
    Farmer profile model with comprehensive fields for eligibility matching.
    Table exists in Supabase - managed = False
    """
    
    # Auth properties to mimic Django User
    @property
    def is_authenticated(self):
        """Always return True for active farmers"""
        return True

    @property
    def is_anonymous(self):
        """Always return False for active farmers"""
        return False
    
    # Choice fields
    LANGUAGE_CHOICES = [
        ('hindi', 'Hindi'),
        ('marathi', 'Marathi'),
        ('english', 'English'),
    ]
    
    FARMING_CATEGORY_CHOICES = [
        ('crop_farming', 'Crop Farming'),
        ('livestock', 'Livestock/Animal Husbandry'),
        ('fisheries', 'Fisheries'),
        ('horticulture', 'Horticulture'),
        ('mixed', 'Mixed Farming'),
        ('poultry', 'Poultry'),
        ('dairy', 'Dairy'),
    ]
    
    SOCIAL_CATEGORY_CHOICES = [
        ('general', 'General'),
        ('obc', 'OBC'),
        ('sc', 'SC'),
        ('st', 'ST'),
        ('nt', 'NT'),
        ('vjnt', 'VJNT'),
        ('sbc', 'SBC'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    LAND_TYPE_CHOICES = [
        ('irrigated', 'Irrigated'),
        ('rainfed', 'Rainfed'),
        ('mixed', 'Mixed'),
    ]
    
    # Primary fields
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    phone = models.CharField(
        max_length=15, 
        unique=True, 
        db_index=True
    )
    name = models.CharField(max_length=255, blank=True, default='')
    
    # Location fields
    state = models.CharField(max_length=100, blank=True, default='')
    district = models.CharField(max_length=100, blank=True, default='')
    village = models.CharField(max_length=100, blank=True, default='')
    
    # Farm details
    land_size = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Land size in acres"
    )
    crop_type = models.CharField(
        max_length=255, blank=True, default='',
        help_text="Legacy single crop field (deprecated, use crops instead)"
    )
    crops = models.JSONField(
        default=list,
        blank=True,
        help_text="List of crops grown by the farmer, e.g. ['onion', 'wheat', 'bajra']"
    )
    land_type = models.CharField(
        max_length=20,
        choices=LAND_TYPE_CHOICES,
        default='rainfed'
    )
    survey_number = models.CharField(
        max_length=50, blank=True, default='',
        help_text="Survey/Gut number from 7/12 extract"
    )
    has_irrigation = models.BooleanField(default=False)
    
    # NEW: Farming category for eligibility filtering
    farming_category = models.CharField(
        max_length=50,
        choices=FARMING_CATEGORY_CHOICES,
        default='crop_farming',
        help_text="Type of farming activity"
    )
    
    # NEW: Demographic fields for eligibility
    social_category = models.CharField(
        max_length=20,
        choices=SOCIAL_CATEGORY_CHOICES,
        default='general',
        help_text="Social category (General/OBC/SC/ST/NT/VJNT)"
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default='male'
    )
    date_of_birth = models.DateField(
        null=True, blank=True,
        help_text="Extracted from Aadhaar card OCR"
    )
    age = models.IntegerField(default=30)
    
    # Aadhaar (only last 4 digits stored for privacy)
    aadhaar_last_four = models.CharField(
        max_length=4, blank=True, default='',
        help_text="Last 4 digits of Aadhaar number"
    )
    
    # NEW: Economic fields
    annual_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Annual income in INR"
    )
    is_bpl = models.BooleanField(
        default=False,
        help_text="Below Poverty Line"
    )
    
    # Preference and status
    language = models.CharField(
        max_length=50, 
        choices=LANGUAGE_CHOICES,
        default='hindi'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'farmers'
        managed = False  # Table exists in Supabase
        ordering = ['-created_at']
        verbose_name = 'Farmer'
        verbose_name_plural = 'Farmers'
    
    def __str__(self):
        return f"{self.name or 'Unnamed'} - {self.phone}"
    
    @property
    def calculated_age(self):
        """Calculate age from date_of_birth, fallback to stored age"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return self.age
    
    @property
    def is_profile_complete(self):
        """Check if minimum profile info is filled (from Aadhaar + 7/12 + crops)"""
        return all([
            self.name,
            self.state,
            self.district,
            self.land_size > 0,
            self.crops,  # Must have at least one crop selected
        ])
    
    def to_application_data(self):
        """Convert farmer profile to application auto-fill data"""
        return {
            'farmer_id': str(self.id),
            'farmer_name': self.name,
            'phone': self.phone,
            'state': self.state,
            'district': self.district,
            'village': self.village,
            'land_size': float(self.land_size),
            'land_type': self.land_type,
            'crop_type': self.crop_type,  # Legacy
            'crops': self.crops,
            'farming_category': self.farming_category,
            'social_category': self.social_category,
            'gender': self.gender,
            'age': self.calculated_age,
            'date_of_birth': str(self.date_of_birth) if self.date_of_birth else '',
            'annual_income': float(self.annual_income),
            'is_bpl': self.is_bpl,
            'has_irrigation': self.has_irrigation,
            'language': self.language,
            'survey_number': self.survey_number,
        }
