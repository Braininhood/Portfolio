from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .supabase_storage import supabase_storage

# Core views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file(request):
    """
    Upload file to Supabase Storage.
    POST /api/core/upload/
    
    Body (multipart/form-data):
    - file: File to upload
    - bucket: Storage bucket name (default: 'default')
    - folder: Optional folder path within bucket
    """
    if 'file' not in request.FILES:
        return Response({
            'success': False,
            'error': {'message': 'No file provided'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    file = request.FILES['file']
    bucket = request.data.get('bucket', 'default')
    folder = request.data.get('folder', '')
    
    # Generate file path
    import os
    from django.utils import timezone
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{file.name}"
    file_path = f"{folder}/{filename}" if folder else filename
    
    # Read file data
    file_data = file.read()
    
    # Upload to Supabase
    result = supabase_storage.upload_file(
        bucket=bucket,
        file_path=file_path,
        file_data=file_data,
        content_type=file.content_type,
        upsert=True
    )
    
    if result['success']:
        return Response({
            'success': True,
            'data': {
                'url': result['url'],
                'path': result['path']
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'error': {'message': result.get('error', 'Upload failed')}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
