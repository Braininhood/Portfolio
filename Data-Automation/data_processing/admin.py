from django.contrib import admin
from .models import ExcelFile, Participant, Cohort, ProcessingJob


@admin.register(ExcelFile)
class ExcelFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'participant_count', 'uploaded_by', 'uploaded_at']
    list_filter = ['status', 'uploaded_at']
    search_fields = ['name', 'uploaded_by__username']
    readonly_fields = ['uploaded_at', 'participant_count']


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'email_valid', 'main_cohort', 'source_file']
    list_filter = ['email_valid', 'main_cohort', 'source_file']
    search_fields = ['full_name', 'email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = ['name', 'cohort_type', 'participant_count', 'created_at']
    list_filter = ['cohort_type', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ['job_type', 'status', 'created_by', 'created_at']
    list_filter = ['job_type', 'status', 'created_at']
    search_fields = ['created_by__username']
    readonly_fields = ['created_at', 'started_at', 'completed_at']
