"""
Supabase Storage Service
Handles document fetching from farmer storage buckets
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decouple import config

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None


class SupabaseStorageService:
    """
    Service to interact with Supabase Storage.
    Each farmer has their own bucket: farmer-{farmer_id}
    Documents are stored with standard naming: {document_type}.pdf/jpg
    """
    
    _client: Optional[Client] = None
    
    # Standard document types matching scheme requirements
    DOCUMENT_TYPES = {
        'aadhaar': ['aadhaar.pdf', 'aadhaar.jpg', 'aadhaar.png'],
        'land_certificate': ['land_certificate.pdf', 'land_record.pdf', '7_12_extract.pdf'],
        'bank_passbook': ['bank_passbook.pdf', 'bank_passbook.jpg', 'passbook.pdf'],
        'caste_certificate': ['caste_certificate.pdf', 'caste_cert.pdf'],
        'income_certificate': ['income_certificate.pdf', 'income_cert.pdf'],
        'pan_card': ['pan_card.pdf', 'pan_card.jpg', 'pan.pdf'],
        'voter_id': ['voter_id.pdf', 'voter_id.jpg', 'voter.pdf'],
        'ration_card': ['ration_card.pdf', 'ration_card.jpg'],
        'photo': ['photo.jpg', 'photo.png', 'passport_photo.jpg'],
        'soil_health_card': ['soil_health_card.pdf', 'soil_health.pdf'],
        'kisan_credit_card': ['kcc.pdf', 'kisan_credit_card.pdf'],
    }
    
    @classmethod
    def get_client(cls) -> Optional[Client]:
        """Get or create Supabase client"""
        if cls._client is None:
            supabase_url = config('SUPABASE_URL', default='')
            supabase_key = config('SUPABASE_SERVICE_KEY', default='') or config('SUPABASE_KEY', default='')
            
            if supabase_url and supabase_key and create_client:
                cls._client = create_client(supabase_url, supabase_key)
        
        return cls._client
    
    @classmethod
    def get_farmer_bucket_name(cls, farmer_id: str) -> str:
        """Generate bucket name for a farmer"""
        return f"farmer-{farmer_id}"
    
    @classmethod
    def list_farmer_documents(cls, farmer_id: str) -> List[Dict[str, Any]]:
        """
        List all documents in a farmer's bucket.
        
        Returns:
            List of document info dicts with type, filename, and size
        """
        client = cls.get_client()
        if not client:
            return []
        
        bucket_name = cls.get_farmer_bucket_name(farmer_id)
        
        try:
            # List all files in the bucket
            files = client.storage.from_(bucket_name).list()
            
            documents = []
            for file in files:
                if file.get('name'):
                    doc_type = cls._identify_document_type(file['name'])
                    documents.append({
                        'filename': file['name'],
                        'document_type': doc_type,
                        'size': file.get('metadata', {}).get('size', 0),
                        'created_at': file.get('created_at'),
                        'updated_at': file.get('updated_at'),
                    })
            
            return documents
        except Exception as e:
            print(f"Error listing documents for farmer {farmer_id}: {e}")
            return []
    
    @classmethod
    def _identify_document_type(cls, filename: str) -> str:
        """Identify document type from filename"""
        filename_lower = filename.lower()
        
        for doc_type, patterns in cls.DOCUMENT_TYPES.items():
            for pattern in patterns:
                if pattern.lower() in filename_lower or filename_lower.startswith(doc_type):
                    return doc_type
        
        # Default: use filename without extension as type
        return filename.rsplit('.', 1)[0] if '.' in filename else filename
    
    @classmethod
    def get_document_signed_url(cls, farmer_id: str, filename: str, expires_in: int = 3600) -> Optional[str]:
        """
        Get a signed URL for a document.
        
        Args:
            farmer_id: The farmer's UUID
            filename: The document filename
            expires_in: URL expiry time in seconds (default 1 hour)
        
        Returns:
            Signed URL or None if error
        """
        client = cls.get_client()
        if not client:
            return None
        
        bucket_name = cls.get_farmer_bucket_name(farmer_id)
        
        try:
            response = client.storage.from_(bucket_name).create_signed_url(
                filename, 
                expires_in
            )
            return response.get('signedURL') or response.get('signedUrl')
        except Exception as e:
            print(f"Error getting signed URL for {filename}: {e}")
            return None
    
    @classmethod
    def fetch_required_documents(cls, farmer_id: str, required_docs: List[str]) -> Dict[str, Any]:
        """
        Fetch required documents from farmer's bucket.
        Matches scheme requirements with available documents.
        
        Args:
            farmer_id: The farmer's UUID
            required_docs: List of required document types (e.g., ['aadhaar', 'land_certificate'])
        
        Returns:
            Dict with found documents, missing documents, and signed URLs
        """
        # Get all documents in farmer's bucket
        available_docs = cls.list_farmer_documents(farmer_id)
        
        # Create lookup by document type
        docs_by_type = {}
        for doc in available_docs:
            doc_type = doc['document_type']
            if doc_type not in docs_by_type:
                docs_by_type[doc_type] = doc
        
        # Match required documents
        found_documents = []
        missing_documents = []
        
        for required_doc in required_docs:
            if required_doc in docs_by_type:
                doc = docs_by_type[required_doc]
                # Get signed URL
                signed_url = cls.get_document_signed_url(farmer_id, doc['filename'])
                
                found_documents.append({
                    'document_type': required_doc,
                    'filename': doc['filename'],
                    'signed_url': signed_url,
                    'verified': True,  # Assume verified if exists
                    'status': 'attached'
                })
            else:
                missing_documents.append({
                    'document_type': required_doc,
                    'status': 'missing',
                    'message': f'{required_doc} not found in your documents'
                })
        
        return {
            'found': found_documents,
            'missing': missing_documents,
            'all_found': len(missing_documents) == 0,
            'total_required': len(required_docs),
            'total_found': len(found_documents)
        }
    
    @classmethod
    def ensure_farmer_bucket_exists(cls, farmer_id: str) -> bool:
        """
        Ensure a farmer's storage bucket exists.
        Creates it if it doesn't exist.
        
        Returns:
            True if bucket exists or was created
        """
        client = cls.get_client()
        if not client:
            return False
        
        bucket_name = cls.get_farmer_bucket_name(farmer_id)
        
        try:
            # Try to get bucket info
            client.storage.get_bucket(bucket_name)
            return True
        except Exception:
            # Bucket doesn't exist, create it
            try:
                client.storage.create_bucket(bucket_name, {'public': False})
                return True
            except Exception as e:
                print(f"Error creating bucket for farmer {farmer_id}: {e}")
                return False
