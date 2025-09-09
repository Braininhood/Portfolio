from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import ExcelFile, Participant, Cohort, ProcessingJob
from .serializers import ExcelFileSerializer, ParticipantSerializer, CohortSerializer, ProcessingJobSerializer
from .services import CohortAnalysisService


class ExcelFileViewSet(viewsets.ModelViewSet):
    queryset = ExcelFile.objects.all()
    serializer_class = ExcelFileSerializer
    
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        file_obj = self.get_object()
        participants = file_obj.participants.all()
        serializer = ParticipantSerializer(participants, many=True)
        return Response(serializer.data)


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


class ProcessingJobViewSet(viewsets.ModelViewSet):
    queryset = ProcessingJob.objects.all()
    serializer_class = ProcessingJobSerializer


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
