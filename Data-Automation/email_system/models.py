from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class EmailTemplate(models.Model):
    TEMPLATE_TYPES = [
        ('primary_cohort', 'Primary Cohort'),
        ('alternative_cohort', 'Alternative Cohort'),
        ('need_software_setup', 'Need Software Setup'),
        ('high_support', 'High Support'),
        ('email_correction_needed', 'Email Correction Needed'),
        ('admin_cohort_summary', 'Admin Cohort Summary'),
        ('custom', 'Custom Template'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class EmailCampaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    name = models.CharField(max_length=200)
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
    cohort = models.ForeignKey('data_processing.Cohort', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Email settings
    sender_email = models.EmailField()
    sender_name = models.CharField(max_length=100, default='Data Automation System')
    
    # Campaign settings
    send_to_valid_emails_only = models.BooleanField(default=True)
    max_recipients = models.IntegerField(default=1000)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"


class EmailRecipient(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='recipients')
    participant = models.ForeignKey('data_processing.Participant', on_delete=models.CASCADE)
    email = models.EmailField()
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['campaign', 'participant']
        ordering = ['email']
    
    def __str__(self):
        return f"{self.name} ({self.email}) - {self.get_status_display()}"


class EmailLog(models.Model):
    LOG_TYPES = [
        ('sent', 'Email Sent'),
        ('failed', 'Email Failed'),
        ('bounced', 'Email Bounced'),
        ('opened', 'Email Opened'),
        ('clicked', 'Link Clicked'),
    ]
    
    recipient = models.ForeignKey(EmailRecipient, on_delete=models.CASCADE, related_name='logs')
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.recipient.email} - {self.get_log_type_display()} at {self.timestamp}"
