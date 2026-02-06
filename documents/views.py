"""
Documents App - Views
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Document
from .serializers import DocumentSerializer, DocumentCreateSerializer, DocumentListSerializer
from core.authentication import get_farmer_from_token
from farmers.models import Farmer


class DocumentListView(APIView):
    """
    GET /api/documents/
    POST /api/documents/
    
    List farmer's documents or upload new one
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        documents = Document.objects.filter(farmer=farmer)
        serializer = DocumentListSerializer(documents, many=True)
        
        return Response({
            'success': True,
            'data': {
                'documents': serializer.data,
                'count': documents.count()
            }
        })
    
    def post(self, request):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DocumentCreateSerializer(data=request.data)
        if serializer.is_valid():
            document = Document.objects.create(
                farmer=farmer,
                **serializer.validated_data
            )
            return Response({
                'success': True,
                'message': 'Document uploaded successfully',
                'data': DocumentSerializer(document).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DocumentDetailView(APIView):
    """
    GET /api/documents/<document_id>/
    DELETE /api/documents/<document_id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, document_id):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            document = Document.objects.get(id=document_id, farmer=farmer)
            serializer = DocumentSerializer(document)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Document.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Document not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, document_id):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            document = Document.objects.get(id=document_id, farmer=farmer)
            document.delete()
            return Response({
                'success': True,
                'message': 'Document deleted successfully'
            })
        except Document.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Document not found'
            }, status=status.HTTP_404_NOT_FOUND)


class DocumentByFarmerView(APIView):
    """
    GET /api/documents/<farmer_id>/

    List documents for a specific farmer by farmer ID
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, farmer_id):
        authenticated_farmer = get_farmer_from_token(request)
        if not authenticated_farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            target_farmer = Farmer.objects.get(id=farmer_id)
        except Farmer.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # For now, allow access only if the authenticated farmer is the same as the target farmer
        # This can be adjusted based on requirements (e.g., admin access)
        if authenticated_farmer.id != target_farmer.id:
            return Response({
                'success': False,
                'message': 'Unauthorized to access this farmer\'s documents'
            }, status=status.HTTP_403_FORBIDDEN)

        documents = Document.objects.filter(farmer=target_farmer)
        serializer = DocumentListSerializer(documents, many=True)

        return Response({
            'success': True,
            'data': {
                'documents': serializer.data,
                'count': documents.count()
            }
        })

    def post(self, request, farmer_id):
        authenticated_farmer = get_farmer_from_token(request)
        if not authenticated_farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            target_farmer = Farmer.objects.get(id=farmer_id)
        except Farmer.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = DocumentCreateSerializer(data=request.data)
        if serializer.is_valid():
            document = Document.objects.create(
                farmer=target_farmer,
                **serializer.validated_data
            )
            return Response({
                'success': True,
                'message': 'Document uploaded successfully',
                'data': DocumentSerializer(document).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
