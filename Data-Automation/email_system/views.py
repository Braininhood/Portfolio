from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import EmailTemplate, EmailCampaign, EmailRecipient, EmailLog
from .serializers import EmailTemplateSerializer, EmailCampaignSerializer, EmailRecipientSerializer, EmailLogSerializer
from .services import EmailService
from .template_generator import EmailTemplateGenerator


class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        template = self.get_object()
        participant_data = request.data.get('participant_data', {})
        
        service = EmailService()
        preview_data = service.preview_template(template, participant_data)
        
        return Response(preview_data)


class EmailCampaignViewSet(viewsets.ModelViewSet):
    queryset = EmailCampaign.objects.all()
    serializer_class = EmailCampaignSerializer
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        campaign = self.get_object()
        service = EmailService()
        
        try:
            result = service.send_campaign(campaign)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def recipients(self, request, pk=None):
        campaign = self.get_object()
        recipients = campaign.recipients.all()
        serializer = EmailRecipientSerializer(recipients, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        campaign = self.get_object()
        recipients = campaign.recipients.all()
        
        stats = {
            'total_recipients': recipients.count(),
            'sent': recipients.filter(status='sent').count(),
            'failed': recipients.filter(status='failed').count(),
            'pending': recipients.filter(status='pending').count(),
            'bounced': recipients.filter(status='bounced').count(),
        }
        
        if stats['total_recipients'] > 0:
            stats['success_rate'] = (stats['sent'] / stats['total_recipients']) * 100
        else:
            stats['success_rate'] = 0
        
        return Response(stats)


class EmailRecipientViewSet(viewsets.ModelViewSet):
    queryset = EmailRecipient.objects.all()
    serializer_class = EmailRecipientSerializer
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        recipient = self.get_object()
        logs = recipient.logs.all()
        serializer = EmailLogSerializer(logs, many=True)
        return Response(serializer.data)


class SendEmailView(APIView):
    def post(self, request):
        template_id = request.data.get('template_id')
        cohort_id = request.data.get('cohort_id')
        sender_email = request.data.get('sender_email')
        sender_password = request.data.get('sender_password')
        custom_subject = request.data.get('custom_subject')
        custom_body = request.data.get('custom_body')
        recipient_ids = request.data.get('recipient_ids')
        delay_between_emails = request.data.get('delay_between_emails', 1)
        
        if not all([template_id, cohort_id, sender_email, sender_password]):
            return Response(
                {'error': 'Missing required fields'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = EmailService()
        try:
            result = service.send_emails_to_cohort(
                template_id, cohort_id, sender_email, sender_password,
                custom_subject, custom_body, recipient_ids, delay_between_emails
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PreviewEmailView(APIView):
    def post(self, request):
        template_id = request.data.get('template_id')
        participant_data = request.data.get('participant_data', {})
        
        if not template_id:
            return Response(
                {'error': 'Template ID required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        template = get_object_or_404(EmailTemplate, id=template_id)
        service = EmailService()
        
        try:
            result = service.preview_template(template, participant_data)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TestEmailConnectionView(APIView):
    def post(self, request):
        sender_email = request.data.get('sender_email')
        sender_password = request.data.get('sender_password')
        
        if not all([sender_email, sender_password]):
            return Response(
                {'error': 'Email and password required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = EmailService()
        try:
            result = service.test_connection(sender_email, sender_password)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GenerateTemplatesView(APIView):
    def post(self, request):
        cohort_ids = request.data.get('cohort_ids', [])
        
        generator = EmailTemplateGenerator()
        
        if cohort_ids:
            result = generator.generate_templates_for_cohorts(cohort_ids)
        else:
            result = generator.generate_all_templates()
        
        return Response(result, status=status.HTTP_200_OK)


class GetEmailConfigView(APIView):
    def get(self, request):
        """Get the last successful email configuration for auto-filling"""
        try:
            # Get the most recent successful campaign
            last_campaign = EmailCampaign.objects.filter(
                status='sent',
                sender_email__isnull=False
            ).order_by('-created_at').first()
            
            if last_campaign:
                return Response({
                    'sender_email': last_campaign.sender_email,
                    'last_used': last_campaign.created_at.isoformat()
                })
            else:
                return Response({
                    'sender_email': None,
                    'message': 'No previous email configuration found'
                })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
