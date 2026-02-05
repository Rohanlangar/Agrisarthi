"""
Schemes App - Eligibility Engine (CRITICAL SERVICE)
Rule-based matching of farmer profiles against scheme eligibility criteria
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal


class EligibilityEngine:
    """
    Rule-based eligibility matching engine.
    Matches farmer profile against scheme eligibility rules.
    """
    
    @classmethod
    def check_eligibility(cls, farmer, scheme) -> Dict[str, Any]:
        """
        Check if a farmer is eligible for a specific scheme.
        
        Args:
            farmer: Farmer model instance
            scheme: Scheme model instance
        
        Returns:
            Dict with structure:
            {
                'eligible': bool,
                'matched_rules': list,
                'failed_rules': list,
                'missing_documents': list
            }
        """
        rules = scheme.eligibility_rules or {}
        required_docs = scheme.required_documents or []
        
        matched_rules = []
        failed_rules = []
        
        # Rule: Minimum land size
        if 'min_land_size' in rules:
            min_size = Decimal(str(rules['min_land_size']))
            if farmer.land_size >= min_size:
                matched_rules.append({
                    'rule': 'min_land_size',
                    'message': f'Land size {farmer.land_size} acres meets minimum {min_size} acres'
                })
            else:
                failed_rules.append({
                    'rule': 'min_land_size',
                    'message': f'Land size {farmer.land_size} acres is less than required {min_size} acres'
                })
        
        # Rule: Maximum land size
        if 'max_land_size' in rules:
            max_size = Decimal(str(rules['max_land_size']))
            if farmer.land_size <= max_size:
                matched_rules.append({
                    'rule': 'max_land_size',
                    'message': f'Land size {farmer.land_size} acres is within maximum {max_size} acres'
                })
            else:
                failed_rules.append({
                    'rule': 'max_land_size',
                    'message': f'Land size {farmer.land_size} acres exceeds maximum {max_size} acres'
                })
        
        # Rule: Allowed states
        if 'allowed_states' in rules and rules['allowed_states']:
            allowed_states = [s.lower() for s in rules['allowed_states']]
            if farmer.state.lower() in allowed_states:
                matched_rules.append({
                    'rule': 'allowed_states',
                    'message': f'State {farmer.state} is eligible'
                })
            else:
                failed_rules.append({
                    'rule': 'allowed_states',
                    'message': f'State {farmer.state} is not in eligible states: {rules["allowed_states"]}'
                })
        
        # Rule: Allowed districts
        if 'allowed_districts' in rules and rules['allowed_districts']:
            allowed_districts = [d.lower() for d in rules['allowed_districts']]
            if farmer.district.lower() in allowed_districts:
                matched_rules.append({
                    'rule': 'allowed_districts',
                    'message': f'District {farmer.district} is eligible'
                })
            else:
                failed_rules.append({
                    'rule': 'allowed_districts',
                    'message': f'District {farmer.district} is not in eligible districts'
                })
        
        # Rule: Allowed crop types
        if 'allowed_crop_types' in rules and rules['allowed_crop_types']:
            allowed_crops = [c.lower() for c in rules['allowed_crop_types']]
            if farmer.crop_type.lower() in allowed_crops:
                matched_rules.append({
                    'rule': 'allowed_crop_types',
                    'message': f'Crop type {farmer.crop_type} is eligible'
                })
            else:
                failed_rules.append({
                    'rule': 'allowed_crop_types',
                    'message': f'Crop type {farmer.crop_type} is not in eligible crops: {rules["allowed_crop_types"]}'
                })
        
        # Check documents
        from documents.models import Document
        farmer_docs = Document.get_farmer_document_types(farmer)
        missing_docs = [doc for doc in required_docs if doc not in farmer_docs]
        
        # Eligible if no rules failed
        is_eligible = len(failed_rules) == 0
        
        return {
            'eligible': is_eligible,
            'matched_rules': matched_rules,
            'failed_rules': failed_rules,
            'missing_documents': missing_docs,
            'has_all_documents': len(missing_docs) == 0
        }
    
    @classmethod
    def get_eligible_schemes(cls, farmer, schemes=None) -> List[Dict[str, Any]]:
        """
        Get all eligible schemes for a farmer.
        
        Args:
            farmer: Farmer model instance
            schemes: Optional queryset of schemes to check (defaults to all active)
        
        Returns:
            List of dicts with scheme info and eligibility details
        """
        from .models import Scheme
        
        if schemes is None:
            schemes = Scheme.objects.filter(is_active=True)
        
        eligible_schemes = []
        
        for scheme in schemes:
            # Skip expired schemes
            if scheme.is_expired:
                continue
            
            result = cls.check_eligibility(farmer, scheme)
            
            if result['eligible']:
                eligible_schemes.append({
                    'scheme': scheme,
                    'scheme_id': str(scheme.id),
                    'name': scheme.name,
                    'name_localized': scheme.get_localized_name(farmer.language),
                    'description': scheme.get_localized_description(farmer.language),
                    'benefit_amount': float(scheme.benefit_amount),
                    'deadline': str(scheme.deadline) if scheme.deadline else None,
                    'eligibility': result,
                    'can_apply': result['has_all_documents']
                })
        
        return eligible_schemes
    
    @classmethod
    def get_all_schemes_with_eligibility(cls, farmer, schemes=None) -> List[Dict[str, Any]]:
        """
        Get all schemes with eligibility status for a farmer.
        Returns both eligible and ineligible schemes.
        """
        from .models import Scheme
        
        if schemes is None:
            schemes = Scheme.objects.filter(is_active=True)
        
        all_schemes = []
        
        for scheme in schemes:
            result = cls.check_eligibility(farmer, scheme)
            
            all_schemes.append({
                'scheme_id': str(scheme.id),
                'name': scheme.name,
                'name_localized': scheme.get_localized_name(farmer.language),
                'description': scheme.get_localized_description(farmer.language),
                'benefit_amount': float(scheme.benefit_amount),
                'deadline': str(scheme.deadline) if scheme.deadline else None,
                'is_eligible': result['eligible'],
                'eligibility_details': result,
                'is_expired': scheme.is_expired
            })
        
        return all_schemes
