from rest_framework import serializers
from .models import EmailTemplate, EmailCampaign, EmailRecipient, EmailLog


class EmailTemplateSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'template_type', 'subject', 'body',
            'created_by', 'created_by_username', 'created_at',
            'updated_at', 'is_active'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EmailRecipientSerializer(serializers.ModelSerializer):
    participant_name = serializers.CharField(source='participant.full_name', read_only=True)
    
    class Meta:
        model = EmailRecipient
        fields = [
            'id', 'campaign', 'participant', 'participant_name',
            'email', 'name', 'status', 'sent_at', 'error_message'
        ]
        read_only_fields = ['sent_at']


class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = [
            'id', 'recipient', 'log_type', 'message',
            'timestamp', 'ip_address', 'user_agent'
        ]
        read_only_fields = ['timestamp']


class EmailCampaignSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    cohort_name = serializers.CharField(source='cohort.name', read_only=True)
    recipient_count = serializers.IntegerField(read_only=True)
    sent_count = serializers.IntegerField(read_only=True)
    failed_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = EmailCampaign
        fields = [
            'id', 'name', 'template', 'template_name', 'cohort', 'cohort_name',
            'status', 'created_by', 'created_by_username', 'created_at',
            'scheduled_at', 'sent_at', 'sender_email', 'sender_name',
            'send_to_valid_emails_only', 'max_recipients',
            'recipient_count', 'sent_count', 'failed_count'
        ]
        read_only_fields = ['created_at', 'sent_at']
