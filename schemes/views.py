"""
Schemes App - Views
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Scheme
from .serializers import SchemeSerializer, SchemeListSerializer, EligibleSchemeSerializer
from .services.eligibility_engine import EligibilityEngine
from core.authentication import get_farmer_from_token


class EligibleSchemesView(APIView):
    """
    GET /api/schemes/eligible/
    
    Get all eligible schemes for the authenticated farmer.
    This is the CORE API for the voice-based scheme discovery.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if profile is complete
        if not farmer.is_profile_complete:
            return Response({
                'success': False,
                'message': 'Please complete your profile first',
                'data': {
                    'profile_complete': False,
                    'missing_fields': self._get_missing_fields(farmer)
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get eligible schemes
        eligible_schemes = EligibilityEngine.get_eligible_schemes(farmer)
        
        # Prepare response with localized names
        response_data = []
        for scheme_data in eligible_schemes:
            response_data.append({
                'scheme_id': scheme_data['scheme_id'],
                'name': scheme_data['name'],
                'name_localized': scheme_data['name_localized'],
                'description': scheme_data['description'],
                'benefit_amount': scheme_data['benefit_amount'],
                'benefit_display': f"₹{scheme_data['benefit_amount']:,.2f}",
                'deadline': scheme_data['deadline'],
                'can_apply': scheme_data['can_apply'],
                'missing_documents': scheme_data['eligibility']['missing_documents']
            })
        
        return Response({
            'success': True,
            'message': f'Found {len(response_data)} eligible schemes',
            'data': {
                'farmer_name': farmer.name,
                'language': farmer.language,
                'eligible_count': len(response_data),
                'schemes': response_data
            }
        })
    
    def _get_missing_fields(self, farmer):
        missing = []
        if not farmer.name:
            missing.append('name')
        if not farmer.state:
            missing.append('state')
        if not farmer.district:
            missing.append('district')
        if farmer.land_size <= 0:
            missing.append('land_size')
        if not farmer.crop_type:
            missing.append('crop_type')
        return missing


class SchemeDetailView(APIView):
    """
    GET /api/schemes/<scheme_id>/
    
    Get detailed information about a specific scheme.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, scheme_id):
        farmer = get_farmer_from_token(request)
        
        try:
            scheme = Scheme.objects.get(id=scheme_id)
        except Scheme.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Scheme not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get eligibility if farmer exists
        eligibility_info = None
        if farmer:
            eligibility_info = EligibilityEngine.check_eligibility(farmer, scheme)
        
        serializer = SchemeSerializer(scheme)
        
        return Response({
            'success': True,
            'data': {
                'scheme': serializer.data,
                'name_localized': scheme.get_localized_name(farmer.language if farmer else 'english'),
                'eligibility': eligibility_info
            }
        })


class AllSchemesView(APIView):
    """
    GET /api/schemes/
    
    Get all active schemes with eligibility status.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        farmer = get_farmer_from_token(request)
        
        schemes = Scheme.objects.filter(is_active=True)
        
        if farmer and farmer.is_profile_complete:
            # Return with eligibility info
            all_schemes = EligibilityEngine.get_all_schemes_with_eligibility(farmer, schemes)
            return Response({
                'success': True,
                'data': {
                    'total_count': len(all_schemes),
                    'schemes': all_schemes
                }
            })
        else:
            # Return basic list without eligibility
            serializer = SchemeListSerializer(schemes, many=True)
            return Response({
                'success': True,
                'data': {
                    'total_count': schemes.count(),
                    'schemes': serializer.data,
                    'note': 'Complete your profile to see eligibility'
                }
            })


class CheckEligibilityView(APIView):
    """
    POST /api/schemes/<scheme_id>/check-eligibility/
    
    Check eligibility for a specific scheme.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, scheme_id):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            scheme = Scheme.objects.get(id=scheme_id)
        except Scheme.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Scheme not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        result = EligibilityEngine.check_eligibility(farmer, scheme)
        
        return Response({
            'success': True,
            'data': {
                'scheme_name': scheme.name,
                'is_eligible': result['eligible'],
                'matched_rules': result['matched_rules'],
                'failed_rules': result['failed_rules'],
                'missing_documents': result['missing_documents'],
                'can_apply': result['eligible'] and result['has_all_documents']
            }
        })
