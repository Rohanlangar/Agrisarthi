"""
Applications App - Application Model
"""

import uuid
from django.db import models
from django.utils import timezone


class Application(models.Model):
    """
    Farmer scheme application with auto-filled data.
    Table exists in Supabase - managed = False
    """
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Review'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('INCOMPLETE', 'Incomplete Documents'),
    ]
    
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    farmer = models.ForeignKey(
        'farmers.Farmer',
        on_delete=models.CASCADE,
        related_name='applications',
        db_column='farmer_id'
    )
    scheme = models.ForeignKey(
        'schemes.Scheme',
        on_delete=models.CASCADE,
        related_name='applications',
        db_column='scheme_id'
    )
    
    # Auto-filled data from farmer profile
    auto_filled_data = models.JSONField(default=dict)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True
    )
    
    documents_submitted = models.JSONField(default=list)
    missing_documents = models.JSONField(default=list)
    
    admin_notes = models.TextField(blank=True, default='')
    rejection_reason = models.TextField(blank=True, default='')
    
    verified_by = models.CharField(max_length=100, blank=True, null=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applications'
        managed = False  # Table exists in Supabase
        ordering = ['-created_at']
        unique_together = [['farmer', 'scheme']]
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
    
    def __str__(self):
        return f"{self.farmer.name} - {self.scheme.name} ({self.status})"
    
    def approve(self, verified_by=None):
        """Approve the application"""
        self.status = 'APPROVED'
        self.verified_at = timezone.now()
        if verified_by:
            self.verified_by = verified_by
        self.save()
    
    def reject(self, reason, verified_by=None):
        """Reject the application"""
        self.status = 'REJECTED'
        self.rejection_reason = reason
        self.verified_at = timezone.now()
        if verified_by:
            self.verified_by = verified_by
        self.save()
