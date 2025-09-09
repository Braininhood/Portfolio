from rest_framework import serializers
from .models import ExcelFile, Participant, Cohort, ProcessingJob


class ExcelFileSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = ExcelFile
        fields = [
            'id', 'name', 'file', 'uploaded_by', 'uploaded_by_username',
            'uploaded_at', 'status', 'participant_count', 'error_message'
        ]
        read_only_fields = ['uploaded_at', 'participant_count']


class ParticipantSerializer(serializers.ModelSerializer):
    source_file_name = serializers.CharField(source='source_file.name', read_only=True)
    
    class Meta:
        model = Participant
        fields = [
            'id', 'full_name', 'email', 'email_valid', 'attending',
            'alternative_dates', 'need_365', 'postcode', 'refugee_status',
            'disabled_status', 'main_cohort', 'tech_cohort', 'support_cohort',
            'communication_cohort', 'readiness_status', 'bpa_cohort',
            'bpa_processing_notes', 'source_file', 'source_file_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CohortSerializer(serializers.ModelSerializer):
    participant_count = serializers.IntegerField(read_only=True)
    participants = ParticipantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Cohort
        fields = [
            'id', 'name', 'cohort_type', 'description', 'participants',
            'participant_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProcessingJobSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ProcessingJob
        fields = [
            'id', 'job_type', 'status', 'created_by', 'created_by_username',
            'created_at', 'started_at', 'completed_at', 'result_data', 'error_message'
        ]
        read_only_fields = ['created_at', 'started_at', 'completed_at']
