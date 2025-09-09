import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any
from django.conf import settings
from django.utils import timezone

from .models import EmailTemplate, EmailCampaign, EmailRecipient, EmailLog
from data_processing.models import Cohort, Participant


class EmailService:
    """Service for handling email operations"""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    def test_connection(self, sender_email: str, sender_password: str) -> Dict[str, Any]:
        """Test email connection with provided credentials"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.quit()
            
            return {
                'success': True,
                'message': 'Connection successful'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}'
            }
    
    def preview_template(self, template: EmailTemplate, participant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Preview email template with sample data"""
        try:
            # Format subject and body with participant data
            subject = self._format_template(template.subject, participant_data)
            body = self._format_template(template.body, participant_data)
            
            return {
                'subject': subject,
                'body': body,
                'template_name': template.name,
                'template_type': template.template_type
            }
        except Exception as e:
            raise Exception(f"Error previewing template: {str(e)}")
    
    def send_emails_to_cohort(self, template_id: int, cohort_id: int, 
                            sender_email: str, sender_password: str, 
                            custom_subject: str = None, custom_body: str = None,
                            recipient_ids: List[int] = None, 
                            delay_between_emails: int = 1) -> Dict[str, Any]:
        """Send emails to all participants in a cohort"""
        try:
            template = EmailTemplate.objects.get(id=template_id)
            cohort = Cohort.objects.get(id=cohort_id)
            
            # Create campaign
            campaign = EmailCampaign.objects.create(
                name=f"Campaign for {cohort.name}",
                template=template,
                cohort=cohort,
                sender_email=sender_email,
                created_by_id=1  # TODO: Get from request user
            )
            
            # Get participants
            all_participants = cohort.participants.all()
            
            # If specific recipient IDs are provided, filter to those
            if recipient_ids:
                all_participants = all_participants.filter(id__in=recipient_ids)
            
            # Separate valid and invalid emails
            valid_participants = all_participants.filter(email_valid=True)
            invalid_participants = all_participants.filter(email_valid=False)
            
            # Create recipients only for valid emails
            recipients = []
            for participant in valid_participants:
                recipient = EmailRecipient.objects.create(
                    campaign=campaign,
                    participant=participant,
                    email=participant.email,
                    name=participant.full_name
                )
                recipients.append(recipient)
            
            # Track invalid emails for reporting
            invalid_emails = []
            for participant in invalid_participants:
                invalid_emails.append({
                    'name': participant.full_name,
                    'email': participant.email,
                    'reason': 'Invalid email address'
                })
            
            # Send emails with timing control
            sent_count = 0
            failed_count = 0
            import time
            
            for i, recipient in enumerate(recipients):
                try:
                    success = self._send_single_email(
                        template, recipient, sender_email, sender_password,
                        custom_subject, custom_body
                    )
                    if success:
                        recipient.status = 'sent'
                        recipient.sent_at = timezone.now()
                        sent_count += 1
                    else:
                        recipient.status = 'failed'
                        recipient.error_message = 'Send function returned False'
                        failed_count += 1
                except Exception as e:
                    recipient.status = 'failed'
                    recipient.error_message = str(e)
                    failed_count += 1
                
                recipient.save()
                
                # Add delay between emails for anti-spam protection
                if i < len(recipients) - 1:  # Don't delay after the last email
                    time.sleep(delay_between_emails)
            
            # Update campaign status
            campaign.status = 'sent'
            campaign.sent_at = timezone.now()
            campaign.save()
            
            return {
                'campaign_id': campaign.id,
                'total_recipients': len(recipients),
                'sent_count': sent_count,
                'failed_count': failed_count,
                'invalid_emails': invalid_emails,
                'invalid_count': len(invalid_emails),
                'success_rate': (sent_count / len(recipients)) * 100 if recipients else 0,
                'total_attempted': len(all_participants),
                'skipped_invalid': len(invalid_emails)
            }
            
        except Exception as e:
            raise Exception(f"Error sending emails: {str(e)}")
    
    def send_campaign(self, campaign: EmailCampaign) -> Dict[str, Any]:
        """Send a specific campaign"""
        # This would be implemented for scheduled campaigns
        # For now, just return the campaign details
        return {
            'campaign_id': campaign.id,
            'status': campaign.status,
            'message': 'Campaign processing not implemented yet'
        }
    
    def _send_single_email(self, template: EmailTemplate, recipient: EmailRecipient, 
                          sender_email: str, sender_password: str,
                          custom_subject: str = None, custom_body: str = None) -> bool:
        """Send a single email to a recipient"""
        try:
            # Prepare participant data
            participant_data = {
                'name': recipient.name,
                'email': recipient.email,
                'software_status': self._get_software_status(recipient.participant),
                'cohort_type': recipient.participant.main_cohort or 'Course Participant',
                'alternative_dates': recipient.participant.alternative_dates or 'Not specified',
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Format email content - use custom content if provided, otherwise use template
            subject = self._format_template(custom_subject or template.subject, participant_data)
            body = self._format_template(custom_body or template.body, participant_data)
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient.email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            
            text = msg.as_string()
            server.sendmail(sender_email, recipient.email, text)
            server.quit()
            
            # Log success
            EmailLog.objects.create(
                recipient=recipient,
                log_type='sent',
                message='Email sent successfully'
            )
            
            return True
            
        except Exception as e:
            # Log failure
            EmailLog.objects.create(
                recipient=recipient,
                log_type='failed',
                message=f'Email failed: {str(e)}'
            )
            return False
    
    def _format_template(self, template_text: str, data: Dict[str, Any]) -> str:
        """Format template text with participant data"""
        try:
            return template_text.format(**data)
        except KeyError as e:
            # Replace missing keys with placeholder
            return template_text.format(**{k: f'{{{k}}}' for k in data.keys()})
    
    def _get_software_status(self, participant: Participant) -> str:
        """Get software status for email template"""
        if participant.need_365 and 'yes' in participant.need_365.lower():
            return "MS Office 365 required"
        elif participant.tech_cohort == 'need_software':
            return "MS Office 365 required"
        else:
            return "Software ready"
