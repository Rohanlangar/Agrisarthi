"""
Documents App - Views
"""

import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Document
from .serializers import DocumentSerializer, DocumentCreateSerializer, DocumentListSerializer
from core.authentication import get_farmer_from_token
from core.storage import upload_document, delete_document
from farmers.models import Farmer


class DocumentListView(APIView):
    """
    GET /api/documents/
    POST /api/documents/
    
    List farmer's documents or upload new one
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
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

        # Get document type from request
        document_type = request.data.get('document_type')
        if not document_type:
            return Response({
                'success': False,
                'message': 'document_type is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Require file upload
        file = request.FILES.get('file')
        if not file:
            return Response({
                'success': False,
                'message': 'File upload is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate filename using document_type
        file_ext = file.name.split('.')[-1] if '.' in file.name else 'bin'
        filename = f"{document_type}/{document_type}.{file_ext}"

        # Upload to farmer's bucket
        document_url = upload_document(str(farmer.id), file, filename)

        if not document_url:
            return Response({
                'success': False,
                'message': 'Failed to upload file to storage'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Create document record
        document = Document.objects.create(
            farmer=farmer,
            document_type=document_type,
            document_url=document_url
        )

        return Response({
            'success': True,
            'message': 'Document uploaded successfully',
            'data': DocumentSerializer(document).data
        }, status=status.HTTP_201_CREATED)


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

        # Get document type from request
        document_type = request.data.get('document_type')
        if not document_type:
            return Response({
                'success': False,
                'message': 'document_type is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Require file upload
        file = request.FILES.get('file')
        if not file:
            return Response({
                'success': False,
                'message': 'File upload is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate filename using document_type
        file_ext = file.name.split('.')[-1] if '.' in file.name else 'bin'
        filename = f"{document_type}/{document_type}.{file_ext}"

        # Upload to farmer's bucket
        document_url = upload_document(str(target_farmer.id), file, filename)

        if not document_url:
            return Response({
                'success': False,
                'message': 'Failed to upload file to storage'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Create document record
        document = Document.objects.create(
            farmer=target_farmer,
            document_type=document_type,
            document_url=document_url
        )

        return Response({
            'success': True,
            'message': 'Document uploaded successfully',
            'data': DocumentSerializer(document).data
        }, status=status.HTTP_201_CREATED)
