"""
Farmers App - Views
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Farmer
from .serializers import FarmerSerializer, FarmerUpdateSerializer
from core.authentication import get_farmer_from_token


class ProfileView(APIView):
    """
    GET /api/farmers/profile/
    PUT /api/farmers/profile/
    
    Get or update current farmer's profile
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Farmer is already authenticated via FarmerAuthentication
        farmer = request.user
        
        serializer = FarmerSerializer(farmer)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request):
        # Farmer is already authenticated via FarmerAuthentication
        farmer = request.user
        
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
