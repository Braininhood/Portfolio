"""
Supabase Storage Service
Handles file uploads to Supabase Storage buckets.
"""
from supabase import create_client, Client
from django.conf import settings
from typing import Optional, BinaryIO
import logging

logger = logging.getLogger(__name__)

class SupabaseStorageService:
    """Service for Supabase Storage operations."""
    
    def __init__(self):
        self.url = getattr(settings, 'SUPABASE_URL', '')
        self.key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', '')
        
        if not self.url or not self.key:
            logger.warning("Supabase credentials not configured. Storage operations will fail.")
            self.client = None
        else:
            self.client: Client = create_client(self.url, self.key)
    
    def upload_file(
        self,
        bucket: str,
        file_path: str,
        file_data: bytes,
        content_type: Optional[str] = None,
        upsert: bool = False
    ) -> dict:
        """
        Upload a file to Supabase Storage.
        
        Args:
            bucket: Storage bucket name (e.g., 'avatars', 'services', 'staff')
            file_path: Path within bucket (e.g., 'user_123/avatar.jpg')
            file_data: File data as bytes
            content_type: MIME type (e.g., 'image/jpeg')
            upsert: If True, overwrite existing file
        
        Returns:
            Dict with success status and file URL
        """
        if not self.client:
            return {"success": False, "error": "Supabase client not initialized"}
        
        try:
            response = self.client.storage.from_(bucket).upload(
                file_path,
                file_data,
                file_options={
                    "content-type": content_type or "application/octet-stream",
                    "upsert": upsert
                }
            )
            
            # Get public URL
            public_url = self.client.storage.from_(bucket).get_public_url(file_path)
            
            return {
                "success": True,
                "path": file_path,
                "url": public_url,
                "data": response
            }
        except Exception as e:
            logger.error(f"Supabase storage upload error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_file(self, bucket: str, file_path: str) -> dict:
        """Delete a file from Supabase Storage."""
        if not self.client:
            return {"success": False, "error": "Supabase client not initialized"}
        
        try:
            response = self.client.storage.from_(bucket).remove([file_path])
            return {
                "success": True,
                "data": response
            }
        except Exception as e:
            logger.error(f"Supabase storage delete error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_public_url(self, bucket: str, file_path: str) -> str:
        """Get public URL for a file."""
        if not self.client:
            return ""
        
        try:
            return self.client.storage.from_(bucket).get_public_url(file_path)
        except Exception as e:
            logger.error(f"Supabase storage get public URL error: {str(e)}")
            return ""
    
    def get_signed_url(self, bucket: str, file_path: str, expires_in: int = 3600) -> str:
        """Get signed URL for private file (expires in seconds)."""
        if not self.client:
            return ""
        
        try:
            response = self.client.storage.from_(bucket).create_signed_url(
                file_path,
                expires_in
            )
            return response.get('signedURL', '')
        except Exception as e:
            logger.error(f"Supabase storage signed URL error: {str(e)}")
            return ''


# Singleton instance
supabase_storage = SupabaseStorageService()
