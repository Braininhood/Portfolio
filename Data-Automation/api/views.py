from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.http import FileResponse
import os
import pandas as pd
from datetime import datetime

from data_processing.models import ExcelFile, Participant, Cohort
from data_processing.serializers import ExcelFileSerializer, ParticipantSerializer, CohortSerializer
from data_processing.services import DataProcessingService, CohortAnalysisService, BPAService
from data_processing.utils import validate_email, validate_date


class FileViewSet(viewsets.ModelViewSet):
    queryset = ExcelFile.objects.all()
    serializer_class = ExcelFileSerializer
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        file_obj = self.get_object()
        file_path = file_obj.file.path
        if os.path.exists(file_path):
            return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=file_obj.name)
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        file_obj = self.get_object()
        service = DataProcessingService()
        result = service.validate_file(file_obj.file.path)
        return Response(result)


class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer
    
    @action(detail=False, methods=['get'])
    def by_cohort(self, request):
        cohort_id = request.query_params.get('cohort_id')
        if cohort_id:
            participants = Participant.objects.filter(cohorts__id=cohort_id)
        else:
            participants = Participant.objects.all()
        serializer = self.get_serializer(participants, many=True)
        return Response(serializer.data)


class CohortViewSet(viewsets.ModelViewSet):
    queryset = Cohort.objects.all()
    serializer_class = CohortSerializer
    
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        cohort = self.get_object()
        participants = cohort.participants.all()
        serializer = ParticipantSerializer(participants, many=True)
        return Response(serializer.data)


class FileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, format=None):
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        if not file.name.endswith(('.xlsx', '.xls')):
            return Response({'error': 'File must be an Excel file'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save file
        excel_file = ExcelFile.objects.create(
            name=file.name,
            file=file,
            uploaded_by=request.user if request.user.is_authenticated else None
        )
        
        # Process file
        service = DataProcessingService()
        try:
            result = service.process_excel_file(excel_file.file.path)
            excel_file.status = 'processed'
            excel_file.participant_count = result.get('participant_count', 0)
            excel_file.save()
            
            return Response({
                'message': 'File uploaded and processed successfully',
                'file_id': excel_file.id,
                'participant_count': result.get('participant_count', 0),
                'details': result
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            excel_file.status = 'error'
            excel_file.error_message = str(e)
            excel_file.save()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MicrosoftFormsImportView(APIView):
    def post(self, request):
        forms_url = request.data.get('forms_url')
        if not forms_url:
            return Response({'error': 'Microsoft Forms URL required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate URL format
        if not forms_url.startswith('https://forms.office.com/'):
            return Response({'error': 'Invalid Microsoft Forms URL'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # In a real implementation, you would:
            # 1. Authenticate with Microsoft Graph API
            # 2. Fetch the form responses
            # 3. Convert to Excel format
            # 4. Process the data
            
            # For now, we'll simulate the import
            import uuid
            mock_file_name = f"forms_import_{uuid.uuid4().hex[:8]}.xlsx"
            
            # Create a mock ExcelFile entry
            excel_file = ExcelFile.objects.create(
                name=mock_file_name,
                file=None,  # In real implementation, this would be the downloaded file
                uploaded_by=request.user if request.user.is_authenticated else None,
                status='processed',
                participant_count=25  # Mock data
            )
            
            return Response({
                'message': 'Successfully imported from Microsoft Forms',
                'file_id': excel_file.id,
                'participant_count': 25,
                'source': 'microsoft_forms',
                'forms_url': forms_url
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': f'Failed to import from Microsoft Forms: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class ProcessDataView(APIView):
    def post(self, request):
        file_ids = request.data.get('file_ids', [])
        if not file_ids:
            return Response({'error': 'No files specified'}, status=status.HTTP_400_BAD_REQUEST)
        
        service = DataProcessingService()
        try:
            result = service.process_multiple_files(file_ids)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AnalyzeDataView(APIView):
    def post(self, request):
        file_ids = request.data.get('file_ids', [])
        if not file_ids:
            return Response({'error': 'No files specified'}, status=status.HTTP_400_BAD_REQUEST)
        
        service = DataProcessingService()
        try:
            result = service.analyze_data(file_ids)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CreateCohortsView(APIView):
    def post(self, request):
        file_ids = request.data.get('file_ids', [])
        if not file_ids:
            return Response({'error': 'No files specified'}, status=status.HTTP_400_BAD_REQUEST)
        
        service = CohortAnalysisService()
        try:
            result = service.create_cohorts_from_files(file_ids)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BPAProcessView(APIView):
    def post(self, request):
        cohort_ids = request.data.get('cohort_ids', [])
        if not cohort_ids:
            return Response({'error': 'No cohorts specified'}, status=status.HTTP_400_BAD_REQUEST)
        
        service = BPAService()
        try:
            result = service.process_cohorts(cohort_ids)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BPADemoView(APIView):
    def get(self, request):
        service = BPAService()
        try:
            result = service.run_demo()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DashboardStatsView(APIView):
    def get(self, request):
        try:
            stats = {
                'total_files': ExcelFile.objects.count(),
                'total_participants': Participant.objects.count(),
                'total_cohorts': Cohort.objects.count(),
                'emails_sent': 0,  # This would come from email system
                'recent_files': ExcelFile.objects.order_by('-uploaded_at')[:5].values(
                    'id', 'name', 'participant_count', 'status', 'uploaded_at'
                )
            }
            return Response(stats, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)