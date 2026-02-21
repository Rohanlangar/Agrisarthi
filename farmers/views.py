"""
Farmers App - Views
Updated with OCR auto-fill profile endpoint
"""

from datetime import datetime
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Farmer
from .serializers import (
    FarmerSerializer, FarmerUpdateSerializer,
    FarmerOCRAutoFillSerializer
)
from core.authentication import get_farmer_from_token


class ProfileView(APIView):
    """
    GET /api/farmers/profile/<farmer_id>/
    PUT /api/farmers/profile/<farmer_id>/

    Get or update specific farmer's profile by ID
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, farmer_id):
        try:
            farmer = Farmer.objects.get(id=farmer_id)
            serializer = FarmerSerializer(farmer)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Farmer.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, farmer_id):
        # Only allow updating own profile
        if str(request.user.id) != str(farmer_id):
            return Response({
                'success': False,
                'message': 'You can only update your own profile'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            farmer = Farmer.objects.get(id=farmer_id)
        except Farmer.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = FarmerUpdateSerializer(farmer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'data': FarmerSerializer(farmer).data
            })

        return Response({
            'success': False,
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ProfileAutoFillView(APIView):
    """
    POST /api/farmers/profile/auto-fill/

    Save farmer profile with OCR-extracted data + crop selection.
    This is the main endpoint used in the new onboarding flow:
    1. OCR extracts data from Aadhaar + 7/12
    2. User confirms/edits the data + selects crops
    3. This endpoint saves everything to the farmer profile
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = FarmerOCRAutoFillSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Update farmer fields from OCR + user input
        if data.get('name'):
            farmer.name = data['name']
        if data.get('date_of_birth'):
            farmer.date_of_birth = data['date_of_birth']
            # Calculate and store age
            today = datetime.now().date()
            dob = data['date_of_birth']
            farmer.age = today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day)
            )
        if data.get('gender'):
            farmer.gender = data['gender']
        if data.get('aadhaar_last_four'):
            farmer.aadhaar_last_four = data['aadhaar_last_four']
        
        # 7/12 data
        if data.get('state'):
            farmer.state = data['state']
        if data.get('district'):
            farmer.district = data['district']
        if data.get('village'):
            farmer.village = data['village']
        if data.get('land_size', 0) > 0:
            farmer.land_size = data['land_size']
        if data.get('survey_number'):
            farmer.survey_number = data['survey_number']
        
        # Crops (must be provided)
        farmer.crops = data.get('crops', [])
        # Also set legacy crop_type field to first crop
        if farmer.crops:
            farmer.crop_type = farmer.crops[0]
        
        # Language preference
        if data.get('language'):
            farmer.language = data['language']

        farmer.save()

        return Response({
            'success': True,
            'message': 'Profile auto-filled successfully',
            'data': FarmerSerializer(farmer).data
        })


class FarmerDetailView(APIView):
    """
    GET /api/farmers/<farmer_id>/
    
    Get specific farmer details (admin only in production)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, farmer_id):
        try:
            farmer = Farmer.objects.get(id=farmer_id)
            serializer = FarmerSerializer(farmer)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Farmer.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
