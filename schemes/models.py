"""
Schemes App - Scheme Model
"""

import uuid
from django.db import models
from django.utils import timezone


class Scheme(models.Model):
    """
    Government Scheme model with eligibility rules.
    Table exists in Supabase - managed = False
    """
    
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    name = models.CharField(max_length=255, unique=True, db_index=True)
    name_hindi = models.CharField(max_length=255, blank=True, null=True)
    name_marathi = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    description_hindi = models.TextField(blank=True, null=True)
    benefit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Eligibility rules as JSON
    # Example: {"min_land_size": 0.5, "max_land_size": 10, "allowed_states": ["Maharashtra"]}
    eligibility_rules = models.JSONField(default=dict)
    
    # Required documents as JSON array
    # Example: ["aadhaar", "land_certificate", "bank_passbook"]
    required_documents = models.JSONField(default=list)
    
    is_active = models.BooleanField(default=True, db_index=True)
    deadline = models.DateField(null=True, blank=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schemes'
        managed = False  # Table exists in Supabase
        ordering = ['-created_at']
        verbose_name = 'Scheme'
        verbose_name_plural = 'Schemes'
    
    def __str__(self):
        return self.name
    
    def get_localized_name(self, language='english'):
        """Get scheme name in requested language"""
        if language == 'hindi' and self.name_hindi:
            return self.name_hindi
        elif language == 'marathi' and self.name_marathi:
            return self.name_marathi
        return self.name
    
    def get_localized_description(self, language='english'):
        """Get description in requested language"""
        if language == 'hindi' and self.description_hindi:
            return self.description_hindi
        return self.description
    
    @property
    def is_expired(self):
        """Check if scheme deadline has passed"""
        if self.deadline:
            return self.deadline < timezone.now().date()
        return False
    
    @property
    def is_available(self):
        """Check if scheme is available for applications"""
        return self.is_active and not self.is_expired
