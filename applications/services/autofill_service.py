"""
Applications App - Auto-Fill Service
Generates auto-filled application data from farmer profile
"""

from typing import Dict, Any
from datetime import datetime


class AutoFillService:
    """
    Service for auto-filling application data from farmer profile.
    This is a key feature that reduces friction for farmers.
    """
    
    @classmethod
    def generate_application_data(cls, farmer, scheme) -> Dict[str, Any]:
        """
        Generate auto-filled application data from farmer profile.
        
        Args:
            farmer: Farmer model instance
            scheme: Scheme model instance
        
        Returns:
            Dict containing all auto-filled application fields
        """
        # Get farmer's documents
        from documents.models import Document
        farmer_docs = list(
            Document.objects.filter(farmer=farmer)
            .values('document_type', 'document_url', 'is_verified')
        )
        
        # Generate auto-filled data
        auto_filled = {
            # Farmer Details
            'applicant': {
                'farmer_id': str(farmer.id),
                'name': farmer.name,
                'phone': farmer.phone,
            },
            
            # Location Details
            'location': {
                'state': farmer.state,
                'district': farmer.district,
                'village': farmer.village,
            },
            
            # Farm Details
            'farm': {
                'land_size': float(farmer.land_size),
                'land_size_unit': 'acres',
                'crop_type': farmer.crop_type,
            },
            
            # Scheme Details
            'scheme': {
                'scheme_id': str(scheme.id),
                'scheme_name': scheme.name,
                'benefit_amount': float(scheme.benefit_amount),
            },
            
            # Documents
            'documents': farmer_docs,
            
            # Metadata
            'metadata': {
                'auto_filled_at': datetime.now().isoformat(),
                'language': farmer.language,
            }
        }
        
        return auto_filled
    
    @classmethod
    def create_application(cls, farmer, scheme):
        """
        Create an application with auto-filled data.
        
        Args:
            farmer: Farmer model instance
            scheme: Scheme model instance
        
        Returns:
            Application instance or None if already exists
        """
        from .models import Application
        from schemes.services.eligibility_engine import EligibilityEngine
        from documents.models import Document
        
        # Check if application already exists
        existing = Application.objects.filter(farmer=farmer, scheme=scheme).first()
        if existing:
            return existing, False  # Return existing, not created
        
        # Check eligibility first
        eligibility = EligibilityEngine.check_eligibility(farmer, scheme)
        if not eligibility['eligible']:
            return None, False
        
        # Generate auto-filled data
        auto_data = cls.generate_application_data(farmer, scheme)
        
        # Get documents info
        farmer_docs = Document.get_farmer_document_types(farmer)
        required_docs = scheme.required_documents or []
        missing_docs = [doc for doc in required_docs if doc not in farmer_docs]
        
        # Create application
        application = Application.objects.create(
            farmer=farmer,
            scheme=scheme,
            auto_filled_data=auto_data,
            status='PENDING' if not missing_docs else 'INCOMPLETE',
            documents_submitted=farmer_docs,
            missing_documents=missing_docs
        )
        
        return application, True  # Created new
    
    @classmethod
    def get_form_preview(cls, farmer, scheme) -> Dict[str, Any]:
        """
        Get a preview of the auto-filled form without creating application.
        Useful for confirmation screen.
        """
        auto_data = cls.generate_application_data(farmer, scheme)
        
        # Format for display
        preview = {
            'title': f'Application for {scheme.get_localized_name(farmer.language)}',
            'benefit': f'₹{scheme.benefit_amount:,.2f}',
            'fields': [
                {'label': 'Applicant Name', 'value': farmer.name, 'editable': False},
                {'label': 'Phone', 'value': farmer.phone, 'editable': False},
                {'label': 'State', 'value': farmer.state, 'editable': False},
                {'label': 'District', 'value': farmer.district, 'editable': False},
                {'label': 'Village', 'value': farmer.village, 'editable': True},
                {'label': 'Land Size', 'value': f'{farmer.land_size} acres', 'editable': False},
                {'label': 'Crop Type', 'value': farmer.crop_type, 'editable': False},
            ],
            'auto_filled_data': auto_data
        }
        
        return preview
