"""
Applications App - Views
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Application
from .serializers import (
    ApplicationSerializer, ApplicationListSerializer,
    ApplicationCreateSerializer
)
from .services.autofill_service import AutoFillService
from schemes.models import Scheme
from schemes.services.eligibility_engine import EligibilityEngine
from core.authentication import get_farmer_from_token


class ApplicationListView(APIView):
    """
    GET /api/applications/
    
    List all applications for the authenticated farmer.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        applications = Application.objects.filter(farmer=farmer).select_related('scheme')
        serializer = ApplicationListSerializer(applications, many=True)
        
        # Group by status
        status_counts = {
            'total': applications.count(),
            'pending': applications.filter(status='PENDING').count(),
            'approved': applications.filter(status='APPROVED').count(),
            'rejected': applications.filter(status='REJECTED').count(),
        }
        
        return Response({
            'success': True,
            'data': {
                'applications': serializer.data,
                'status_counts': status_counts
            }
        })


class ApplySchemeView(APIView):
    """
    POST /api/applications/apply/
    
    Apply for a scheme with auto-filled data.
    This is the core application endpoint.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate input
        serializer = ApplicationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        scheme_id = serializer.validated_data['scheme_id']
        
        # Get scheme
        try:
            scheme = Scheme.objects.get(id=scheme_id)
        except Scheme.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Scheme not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check eligibility
        eligibility = EligibilityEngine.check_eligibility(farmer, scheme)
        if not eligibility['eligible']:
            return Response({
                'success': False,
                'message': 'You are not eligible for this scheme',
                'data': {
                    'failed_rules': eligibility['failed_rules']
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create application with auto-fill
        application, created = AutoFillService.create_application(farmer, scheme)
        
        if not created and application:
            return Response({
                'success': False,
                'message': 'You have already applied for this scheme',
                'data': {
                    'application_id': str(application.id),
                    'status': application.status
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not application:
            return Response({
                'success': False,
                'message': 'Could not create application'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'message': 'Application submitted successfully',
            'data': {
                'application_id': str(application.id),
                'scheme_name': scheme.name,
                'scheme_name_localized': scheme.get_localized_name(farmer.language),
                'status': application.status,
                'auto_filled_data': application.auto_filled_data,
                'missing_documents': application.missing_documents
            }
        }, status=status.HTTP_201_CREATED)


class ApplicationPreviewView(APIView):
    """
    POST /api/applications/preview/
    
    Get a preview of the auto-filled form before submitting.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        scheme_id = request.data.get('scheme_id')
        if not scheme_id:
            return Response({
                'success': False,
                'message': 'scheme_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            scheme = Scheme.objects.get(id=scheme_id)
        except Scheme.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Scheme not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        preview = AutoFillService.get_form_preview(farmer, scheme)
        
        return Response({
            'success': True,
            'data': preview
        })


class ApplicationStatusView(APIView):
    """
    GET /api/applications/<application_id>/status/
    
    Check status of a specific application.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, application_id):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            application = Application.objects.select_related('scheme').get(
                id=application_id,
                farmer=farmer
            )
        except Application.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Application not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'data': {
                'application_id': str(application.id),
                'scheme_name': application.scheme.name,
                'scheme_name_localized': application.scheme.get_localized_name(farmer.language),
                'benefit_amount': float(application.scheme.benefit_amount),
                'status': application.status,
                'status_display': application.get_status_display(),
                'applied_on': application.created_at.isoformat(),
                'last_updated': application.updated_at.isoformat(),
                'rejection_reason': application.rejection_reason if application.status == 'REJECTED' else None,
                'missing_documents': application.missing_documents
            }
        })


class ApplicationDetailView(APIView):
    """
    GET /api/applications/<application_id>/
    
    Get full application details.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, application_id):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            application = Application.objects.select_related('scheme', 'farmer').get(
                id=application_id,
                farmer=farmer
            )
        except Application.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Application not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ApplicationSerializer(application)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
