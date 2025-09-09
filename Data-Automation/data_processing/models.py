from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ExcelFile(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('error', 'Error'),
    ]
    
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='excel_files/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    participant_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.name


class Participant(models.Model):
    COHORT_TYPES = [
        ('primary', 'Primary Cohort'),
        ('alternative', 'Alternative Cohort'),
        ('need_software', 'Need Software Setup'),
        ('software_ready', 'Software Ready'),
        ('high_support', 'High Support'),
        ('standard_support', 'Standard Support'),
        ('moodle_ready', 'Moodle Ready'),
        ('email_correction', 'Email Correction Needed'),
        ('ready_to_start', 'Ready to Start'),
        ('need_setup', 'Need Setup'),
        ('need_followup', 'Need Follow-up'),
    ]
    
    # Basic information
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    email_valid = models.BooleanField(default=False)
    
    # Course information
    attending = models.CharField(max_length=50, blank=True)
    alternative_dates = models.CharField(max_length=255, blank=True)
    need_365 = models.CharField(max_length=50, blank=True)
    postcode = models.CharField(max_length=20, blank=True)
    
    # Status information
    refugee_status = models.CharField(max_length=50, blank=True)
    disabled_status = models.CharField(max_length=50, blank=True)
    
    # Cohort assignments
    main_cohort = models.CharField(max_length=50, choices=COHORT_TYPES, blank=True)
    tech_cohort = models.CharField(max_length=50, choices=COHORT_TYPES, blank=True)
    support_cohort = models.CharField(max_length=50, choices=COHORT_TYPES, blank=True)
    communication_cohort = models.CharField(max_length=50, choices=COHORT_TYPES, blank=True)
    readiness_status = models.CharField(max_length=50, choices=COHORT_TYPES, blank=True)
    
    # BPA processing
    bpa_cohort = models.CharField(max_length=50, blank=True)
    bpa_processing_notes = models.TextField(blank=True)
    
    # Metadata
    source_file = models.ForeignKey(ExcelFile, on_delete=models.CASCADE, related_name='participants')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['full_name']
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Cohort(models.Model):
    COHORT_TYPES = [
        ('primary', 'Primary Cohort'),
        ('alternative', 'Alternative Cohort'),
        ('need_software', 'Need Software Setup'),
        ('software_ready', 'Software Ready'),
        ('high_support', 'High Support'),
        ('standard_support', 'Standard Support'),
        ('moodle_ready', 'Moodle Ready'),
        ('email_correction', 'Email Correction Needed'),
        ('ready_to_start', 'Ready to Start'),
        ('need_setup', 'Need Setup'),
        ('need_followup', 'Need Follow-up'),
    ]
    
    name = models.CharField(max_length=100)
    cohort_type = models.CharField(max_length=50, choices=COHORT_TYPES)
    description = models.TextField(blank=True)
    participants = models.ManyToManyField(Participant, related_name='cohorts')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_cohort_type_display()})"
    
    @property
    def participant_count(self):
        return self.participants.count()


class ProcessingJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    JOB_TYPES = [
        ('file_upload', 'File Upload'),
        ('data_analysis', 'Data Analysis'),
        ('cohort_creation', 'Cohort Creation'),
        ('bpa_processing', 'BPA Processing'),
        ('email_sending', 'Email Sending'),
    ]
    
    job_type = models.CharField(max_length=50, choices=JOB_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_job_type_display()} - {self.status}"
