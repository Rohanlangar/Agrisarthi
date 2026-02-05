"""
Farmers App - Farmer Model
"""

import uuid
from django.db import models


class Farmer(models.Model):
    """
    Farmer profile model with all required fields.
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

    
    LANGUAGE_CHOICES = [
        ('hindi', 'Hindi'),
        ('marathi', 'Marathi'),
        ('english', 'English'),
    ]
    
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
    state = models.CharField(max_length=100, blank=True, default='')
    district = models.CharField(max_length=100, blank=True, default='')
    village = models.CharField(max_length=100, blank=True, default='')
    land_size = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Land size in acres"
    )
    crop_type = models.CharField(max_length=255, blank=True, default='')
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
    def is_profile_complete(self):
        """Check if minimum profile info is filled"""
        return all([
            self.name,
            self.state,
            self.district,
            self.land_size > 0,
            self.crop_type
        ])
    
    def to_application_data(self):
        """Convert farmer profile to application auto-fill data"""
        return {
            'farmer_name': self.name,
            'phone': self.phone,
            'state': self.state,
            'district': self.district,
            'village': self.village,
            'land_size': float(self.land_size),
            'crop_type': self.crop_type,
            'language': self.language
        }
