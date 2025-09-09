from django.contrib import admin
from .models import EmailTemplate, EmailCampaign, EmailRecipient, EmailLog


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'created_by', 'created_at']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'subject']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'template', 'cohort', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'template__name', 'cohort__name']
    readonly_fields = ['created_at', 'sent_at']


@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'status', 'campaign', 'sent_at']
    list_filter = ['status', 'campaign', 'sent_at']
    search_fields = ['name', 'email', 'campaign__name']
    readonly_fields = ['sent_at']


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'log_type', 'timestamp']
    list_filter = ['log_type', 'timestamp']
    search_fields = ['recipient__name', 'recipient__email']
    readonly_fields = ['timestamp']
