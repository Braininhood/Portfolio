"""
Django Storage Backend for Supabase Storage.
Allows Django to use Supabase Storage like local file storage.
"""
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from .supabase_storage import supabase_storage
import os
import requests

class SupabaseStorage(Storage):
    """
    Django storage backend for Supabase Storage.
    Usage in models:
        image = models.ImageField(storage=SupabaseStorage(bucket='images'))
    """
    
    def __init__(self, bucket='default'):
        self.bucket = bucket
    
    def _open(self, name, mode='rb'):
        # For reading, we'll fetch the file content from Supabase
        url = supabase_storage.get_public_url(self.bucket, name)
        if not url:
            raise FileNotFoundError(f"File {name} not found in bucket {self.bucket}")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return ContentFile(response.content)
        except Exception as e:
            raise IOError(f"Failed to read file {name}: {str(e)}")
    
    def _save(self, name, content):
        # Read file content
        content.seek(0)
        file_data = content.read()
        
        # Determine content type
        content_type = getattr(content, 'content_type', None)
        if not content_type:
            # Guess from extension
            ext = os.path.splitext(name)[1].lower()
            content_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.pdf': 'application/pdf',
                '.webp': 'image/webp',
            }
            content_type = content_types.get(ext, 'application/octet-stream')
        
        # Upload to Supabase
        result = supabase_storage.upload_file(
            self.bucket,
            name,
            file_data,
            content_type=content_type,
            upsert=True
        )
        
        if result['success']:
            return name
        else:
            raise IOError(f"Failed to upload file: {result.get('error')}")
    
    def delete(self, name):
        result = supabase_storage.delete_file(self.bucket, name)
        if not result['success']:
            raise IOError(f"Failed to delete file: {result.get('error')}")
    
    def exists(self, name):
        # Check if file exists by trying to get its URL
        try:
            url = supabase_storage.get_public_url(self.bucket, name)
            if not url:
                return False
            # Try to access the URL to check existence
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def url(self, name):
        """Return public URL for the file."""
        return supabase_storage.get_public_url(self.bucket, name)
    
    def size(self, name):
        """Return the size of the file."""
        try:
            url = supabase_storage.get_public_url(self.bucket, name)
            response = requests.head(url, timeout=5)
            return int(response.headers.get('Content-Length', 0))
        except:
            return 0
