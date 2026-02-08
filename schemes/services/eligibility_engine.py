"""
Schemes App - Enhanced Eligibility Engine
Robust rule-based matching with comprehensive farmer profile fields
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal


class EligibilityEngine:
    """
    Enhanced rule-based eligibility matching engine.
    Matches farmer profile against scheme eligibility rules.
    
    Supported Rules:
    - min_land_size / max_land_size
    - allowed_states / allowed_districts
    - allowed_crop_types
    - allowed_farming_categories (NEW)
    - allowed_social_categories (NEW)
    - allowed_genders (NEW)
    - min_age / max_age (NEW)
    - max_annual_income (NEW)
    - requires_irrigation (NEW)
    - requires_bpl (NEW)
    - allowed_land_types (NEW)
    """
    
    @classmethod
    def check_eligibility(cls, farmer, scheme) -> Dict[str, Any]:
        """
        Check if a farmer is eligible for a specific scheme.
        
        Args:
            farmer: Farmer model instance
            scheme: Scheme model instance
        
        Returns:
            Dict with eligibility result and details
        """
        rules = scheme.eligibility_rules or {}
        required_docs = scheme.required_documents or []
        
        matched_rules = []
        failed_rules = []
        
        # ==========================================
        # FARMING CATEGORY RULES (Most Important!)
        # ==========================================
        if 'allowed_farming_categories' in rules and rules['allowed_farming_categories']:
            allowed_categories = [c.lower() for c in rules['allowed_farming_categories']]
            farmer_category = getattr(farmer, 'farming_category', 'crop_farming') or 'crop_farming'
            
            if farmer_category.lower() in allowed_categories:
                matched_rules.append({
                    'rule': 'allowed_farming_categories',
                    'message': f'Farming category {farmer_category} is eligible'
                })
            else:
                failed_rules.append({
                    'rule': 'allowed_farming_categories',
                    'message': f'This scheme is for {", ".join(rules["allowed_farming_categories"])} only'
                })
        
        # ==========================================
        # LAND SIZE RULES
        # ==========================================
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
        
        # ==========================================
        # LOCATION RULES
        # ==========================================
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
                    'message': f'State {farmer.state} is not in eligible states'
                })
        
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
        
        # ==========================================
        # CROP TYPE RULES
        # ==========================================
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
                    'message': f'Crop type {farmer.crop_type} is not eligible for this scheme'
                })
        
        # ==========================================
        # SOCIAL CATEGORY RULES (NEW)
        # ==========================================
        if 'allowed_social_categories' in rules and rules['allowed_social_categories']:
            allowed_categories = [c.lower() for c in rules['allowed_social_categories']]
            farmer_social = getattr(farmer, 'social_category', 'general') or 'general'
            
            if farmer_social.lower() in allowed_categories:
                matched_rules.append({
                    'rule': 'allowed_social_categories',
                    'message': f'Social category {farmer_social.upper()} is eligible'
                })
            else:
                failed_rules.append({
                    'rule': 'allowed_social_categories',
                    'message': f'This scheme is for {", ".join([c.upper() for c in rules["allowed_social_categories"]])} categories only'
                })
        
        # ==========================================
        # GENDER RULES (NEW)
        # ==========================================
        if 'allowed_genders' in rules and rules['allowed_genders']:
            allowed_genders = [g.lower() for g in rules['allowed_genders']]
            farmer_gender = getattr(farmer, 'gender', 'male') or 'male'
            
            if farmer_gender.lower() in allowed_genders:
                matched_rules.append({
                    'rule': 'allowed_genders',
                    'message': f'Gender requirement met'
                })
            else:
                failed_rules.append({
                    'rule': 'allowed_genders',
                    'message': f'This scheme is for {", ".join(rules["allowed_genders"])} farmers only'
                })
        
        # ==========================================
        # AGE RULES (NEW)
        # ==========================================
        farmer_age = getattr(farmer, 'age', 30) or 30
        
        if 'min_age' in rules:
            min_age = int(rules['min_age'])
            if farmer_age >= min_age:
                matched_rules.append({
                    'rule': 'min_age',
                    'message': f'Age {farmer_age} meets minimum {min_age} years'
                })
            else:
                failed_rules.append({
                    'rule': 'min_age',
                    'message': f'Minimum age requirement is {min_age} years'
                })
        
        if 'max_age' in rules:
            max_age = int(rules['max_age'])
            if farmer_age <= max_age:
                matched_rules.append({
                    'rule': 'max_age',
                    'message': f'Age {farmer_age} is within maximum {max_age} years'
                })
            else:
                failed_rules.append({
                    'rule': 'max_age',
                    'message': f'Maximum age limit is {max_age} years'
                })
        
        # ==========================================
        # INCOME RULES (NEW)
        # ==========================================
        if 'max_annual_income' in rules:
            max_income = Decimal(str(rules['max_annual_income']))
            farmer_income = getattr(farmer, 'annual_income', 0) or 0
            
            if Decimal(str(farmer_income)) <= max_income:
                matched_rules.append({
                    'rule': 'max_annual_income',
                    'message': f'Income within eligible limit'
                })
            else:
                failed_rules.append({
                    'rule': 'max_annual_income',
                    'message': f'Annual income exceeds maximum ₹{max_income:,.0f}'
                })
        
        # ==========================================
        # BPL REQUIREMENT (NEW)
        # ==========================================
        if 'requires_bpl' in rules and rules['requires_bpl']:
            farmer_bpl = getattr(farmer, 'is_bpl', False)
            
            if farmer_bpl:
                matched_rules.append({
                    'rule': 'requires_bpl',
                    'message': 'BPL requirement met'
                })
            else:
                failed_rules.append({
                    'rule': 'requires_bpl',
                    'message': 'This scheme is for BPL families only'
                })
        
        # ==========================================
        # IRRIGATION REQUIREMENT (NEW)
        # ==========================================
        if 'requires_irrigation' in rules and rules['requires_irrigation']:
            has_irrigation = getattr(farmer, 'has_irrigation', False)
            
            if has_irrigation:
                matched_rules.append({
                    'rule': 'requires_irrigation',
                    'message': 'Irrigation facility available'
                })
            else:
                failed_rules.append({
                    'rule': 'requires_irrigation',
                    'message': 'This scheme requires irrigation facility'
                })
        
        # ==========================================
        # LAND TYPE RULES (NEW)
        # ==========================================
        if 'allowed_land_types' in rules and rules['allowed_land_types']:
            allowed_types = [t.lower() for t in rules['allowed_land_types']]
            farmer_land_type = getattr(farmer, 'land_type', 'rainfed') or 'rainfed'
            
            if farmer_land_type.lower() in allowed_types:
                matched_rules.append({
                    'rule': 'allowed_land_types',
                    'message': f'Land type {farmer_land_type} is eligible'
                })
            else:
                failed_rules.append({
                    'rule': 'allowed_land_types',
                    'message': f'This scheme is for {", ".join(rules["allowed_land_types"])} land only'
                })
        
        # ==========================================
        # DOCUMENT CHECK
        # ==========================================
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
        """
        from schemes.models import Scheme
        
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
        """
        from schemes.models import Scheme
        
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
