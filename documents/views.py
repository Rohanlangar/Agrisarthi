"""
Documents App - Views
Updated with OCR extraction endpoints for Aadhaar and 7/12 documents.

New onboarding flow:
1. Upload Aadhaar → OCR extracts name, DOB, gender
2. Upload 7/12 → OCR extracts land size, village, district  
3. User confirms data + selects crops → Profile auto-filled
"""

import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Document
from .serializers import DocumentSerializer, DocumentCreateSerializer, DocumentListSerializer
from .ocr_service import OCRService
from core.authentication import get_farmer_from_token
from core.storage import upload_document, delete_document
from farmers.models import Farmer


class OCRAadhaarView(APIView):
    """
    POST /api/documents/ocr/aadhaar/
    
    Upload Aadhaar card image and extract data using OCR.
    Returns extracted data (name, DOB, gender, masked Aadhaar number).
    Also uploads the document to farmer's storage bucket.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate file is provided
        if 'file' not in request.FILES:
            return Response({
                'success': False,
                'message': 'No file provided. Please upload an Aadhaar card image.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
        if file.content_type not in allowed_types:
            return Response({
                'success': False,
                'message': f'Invalid file type: {file.content_type}. Allowed: JPEG, PNG, WebP, PDF'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Run OCR
        ocr_service = OCRService()
        result = ocr_service.extract_from_aadhaar(file)
        
        # Upload document to storage
        file.seek(0)
        file_ext = file.name.split('.')[-1] if '.' in file.name else 'jpg'
        filename = f"aadhaar.{file_ext}"
        document_url = upload_document(str(farmer.id), file, filename)
        
        # Save document record
        if document_url:
            # Delete any existing Aadhaar document for this farmer
            Document.objects.filter(farmer=farmer, document_type='aadhaar').delete()
            
            Document.objects.create(
                farmer=farmer,
                document_type='aadhaar',
                document_url=document_url,
            )
        
        return Response({
            'success': result.success,
            'message': 'Aadhaar card processed successfully' if result.success else 'OCR extraction had issues',
            'data': {
                'extracted': result.data,
                'confidence': result.confidence,
                'document_uploaded': bool(document_url),
            },
            'errors': result.errors,
        }, status=status.HTTP_200_OK)


class OCRSevenTwelveView(APIView):
    """
    POST /api/documents/ocr/seven-twelve/
    
    Upload 7/12 Extract image and extract data using OCR.
    Returns extracted data (land size, village, district, state, survey number).
    Also uploads the document to farmer's storage bucket.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate file is provided
        if 'file' not in request.FILES:
            return Response({
                'success': False,
                'message': 'No file provided. Please upload a 7/12 Extract image.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
        if file.content_type not in allowed_types:
            return Response({
                'success': False,
                'message': f'Invalid file type: {file.content_type}. Allowed: JPEG, PNG, WebP, PDF'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Run OCR
        ocr_service = OCRService()
        result = ocr_service.extract_from_seven_twelve(file)
        
        # Upload document to storage
        file.seek(0)
        file_ext = file.name.split('.')[-1] if '.' in file.name else 'jpg'
        filename = f"seven_twelve.{file_ext}"
        document_url = upload_document(str(farmer.id), file, filename)
        
        # Save document record
        if document_url:
            # Delete any existing 7/12 document for this farmer
            Document.objects.filter(farmer=farmer, document_type='seven_twelve').delete()
            
            Document.objects.create(
                farmer=farmer,
                document_type='seven_twelve',
                document_url=document_url,
            )
        
        return Response({
            'success': result.success,
            'message': '7/12 Extract processed successfully' if result.success else 'OCR extraction had issues',
            'data': {
                'extracted': result.data,
                'confidence': result.confidence,
                'document_uploaded': bool(document_url),
            },
            'errors': result.errors,
        }, status=status.HTTP_200_OK)


class DocumentListView(APIView):
    """
    GET /api/documents/
    POST /api/documents/
    
    List farmer's documents or upload new one.
    In the new flow, only Aadhaar + 7/12 are required.
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
        """Upload documents - now requires only Aadhaar + 7/12"""
        farmer = get_farmer_from_token(request)
        if not farmer:
            return Response({
                'success': False,
                'message': 'Farmer not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # New required document types (only 2)
        required_types = ['aadhaar', 'seven_twelve']

        # Check if required documents are provided
        missing_types = [doc_type for doc_type in required_types if doc_type not in request.FILES]
        if missing_types:
            return Response({
                'success': False,
                'message': f'Missing required documents: {", ".join(missing_types)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        uploaded_documents = []

        # Upload each document
        for document_type in required_types:
            file = request.FILES[document_type]

            # Generate filename using document_type
            file_ext = file.name.split('.')[-1] if '.' in file.name else 'bin'
            filename = f"{document_type}.{file_ext}"

            # Upload to farmer's bucket
            document_url = upload_document(str(farmer.id), file, filename)

            if not document_url:
                return Response({
                    'success': False,
                    'message': f'Failed to upload {document_type} to storage'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Delete existing document of same type
            Document.objects.filter(farmer=farmer, document_type=document_type).delete()

            # Create document record
            document = Document.objects.create(
                farmer=farmer,
                document_type=document_type,
                document_url=document_url
            )
            uploaded_documents.append(document)

        # Serialize all uploaded documents
        serializer = DocumentSerializer(uploaded_documents, many=True)

        return Response({
            'success': True,
            'message': 'All documents uploaded successfully',
            'data': {
                'documents': serializer.data,
                'count': len(uploaded_documents)
            }
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
    GET /api/documents/farmer/<farmer_id>/

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
