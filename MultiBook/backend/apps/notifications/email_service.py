"""
Email Notification Service

Flexible email service supporting multiple providers:
- Google Gmail (SMTP)
- SendGrid
- Resend
- Generic SMTP
- Console (development)

Designed to be easily extensible for new providers.
"""
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailService:
    """Base email service - can be extended for specific providers."""
    
    @staticmethod
    def send_email(
        subject: str,
        message: str,
        recipient_list: List[str],
        html_message: Optional[str] = None,
        from_email: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Send email using Django's email backend.
        
        Args:
            subject: Email subject
            message: Plain text message
            recipient_list: List of recipient email addresses
            html_message: Optional HTML message
            from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
            **kwargs: Additional email options
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@yourdomain.com')
            
            # Use HTML message if provided
            if html_message:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=message,  # Plain text fallback
                    from_email=from_email,
                    to=recipient_list,
                    **kwargs
                )
                email.attach_alternative(html_message, "text/html")
                email.send()
            else:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=recipient_list,
                    fail_silently=False,
                    **kwargs
                )
            
            logger.info(f"Email sent successfully to {recipient_list}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {recipient_list}: {e}")
            return False
    
    @staticmethod
    def send_templated_email(
        template_name: str,
        context: Dict[str, Any],
        subject: str,
        recipient_list: List[str],
        from_email: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Send email using a template.
        
        Args:
            template_name: Template name (without .html/.txt extension)
            context: Template context variables
            subject: Email subject
            recipient_list: List of recipient email addresses
            from_email: Sender email
            **kwargs: Additional email options
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Render HTML template
            html_message = render_to_string(f'emails/{template_name}.html', context)
            
            # Render plain text template (or strip HTML if no .txt template)
            try:
                plain_message = render_to_string(f'emails/{template_name}.txt', context)
            except:
                plain_message = strip_tags(html_message)
            
            return EmailService.send_email(
                subject=subject,
                message=plain_message,
                recipient_list=recipient_list,
                html_message=html_message,
                from_email=from_email,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Error sending templated email ({template_name}): {e}")
            return False


class BookingConfirmationEmail:
    """Booking confirmation email service."""
    
    @staticmethod
    def send(order, recipient_email: Optional[str] = None) -> bool:
        """
        Send booking confirmation email.
        
        Args:
            order: Order instance
            recipient_email: Email address (defaults to order.customer.email or order.guest_email)
        
        Returns:
            bool: True if sent successfully
        """
        recipient_email = recipient_email or (order.customer.email if order.customer else order.guest_email)
        
        if not recipient_email:
            logger.warning(f"Cannot send confirmation email for order {order.order_number}: no email address")
            return False
        
        # Build context for email template
        customer_name = order.customer.name if order.customer else order.guest_name
        tracking_url = f"{settings.FRONTEND_URL}/booking/track/{order.tracking_token}"
        order_details_url = f"{settings.FRONTEND_URL}/booking/confirmation?order={order.order_number}"
        
        context = {
            'order': order,
            'customer_name': customer_name,
            'order_number': order.order_number,
            'total_price': order.total_price,
            'scheduled_date': order.scheduled_date,
            'scheduled_time': order.scheduled_time,
            'address_line1': order.address_line1,
            'address_line2': order.address_line2,
            'city': order.city,
            'postcode': order.postcode,
            'tracking_url': tracking_url,
            'order_details_url': order_details_url,
            'frontend_url': settings.FRONTEND_URL,
            'items': order.items.all(),
        }
        
        subject = f"Booking Confirmation - Order {order.order_number}"
        
        return EmailService.send_templated_email(
            template_name='booking_confirmation',
            context=context,
            subject=subject,
            recipient_list=[recipient_email],
        )


class BookingReminderEmail:
    """Booking reminder email service."""
    
    @staticmethod
    def send(appointment, recipient_email: Optional[str] = None) -> bool:
        """
        Send booking reminder email (24 hours before appointment).
        
        Args:
            appointment: Appointment instance
            recipient_email: Email address
        
        Returns:
            bool: True if sent successfully
        """
        # Get recipient email from appointment/order
        if not recipient_email:
            if appointment.order:
                recipient_email = appointment.order.customer.email if appointment.order.customer else appointment.order.guest_email
            # TODO: Handle single appointments (from customer_appointment)
        
        if not recipient_email:
            logger.warning(f"Cannot send reminder email for appointment {appointment.id}: no email address")
            return False
        
        context = {
            'appointment': appointment,
            'service_name': appointment.service.name,
            'staff_name': appointment.staff.name if appointment.staff else 'Staff',
            'start_time': appointment.start_time,
            'end_time': appointment.end_time,
            'address': None,  # TODO: Get address from appointment/order
        }
        
        # Add order context if available
        if appointment.order:
            context['order'] = appointment.order
            context['address'] = {
                'line1': appointment.order.address_line1 or '',
                'line2': appointment.order.address_line2 or '',
                'city': appointment.order.city or '',
                'postcode': appointment.order.postcode or '',
            }
        
        subject = f"Reminder: Your {appointment.service.name} appointment is tomorrow"
        
        return EmailService.send_templated_email(
            template_name='booking_reminder',
            context=context,
            subject=subject,
            recipient_list=[recipient_email],
        )


class BookingCancellationEmail:
    """Booking cancellation email service."""
    
    @staticmethod
    def send(order, recipient_email: Optional[str] = None, cancellation_reason: Optional[str] = None) -> bool:
        """
        Send booking cancellation email.
        
        Args:
            order: Order instance
            recipient_email: Email address
            cancellation_reason: Optional cancellation reason
        
        Returns:
            bool: True if sent successfully
        """
        recipient_email = recipient_email or (order.customer.email if order.customer else order.guest_email)
        
        if not recipient_email:
            logger.warning(f"Cannot send cancellation email for order {order.order_number}: no email address")
            return False
        
        customer_name = order.customer.name if order.customer else order.guest_name
        
        context = {
            'order': order,
            'customer_name': customer_name,
            'order_number': order.order_number,
            'cancellation_reason': cancellation_reason,
            'frontend_url': settings.FRONTEND_URL,
        }
        
        subject = f"Booking Cancelled - Order {order.order_number}"
        
        return EmailService.send_templated_email(
            template_name='booking_cancellation',
            context=context,
            subject=subject,
            recipient_list=[recipient_email],
        )


# Convenience functions for easy use
def send_booking_confirmation(order) -> bool:
    """Send booking confirmation email for an order."""
    return BookingConfirmationEmail.send(order)


def send_booking_reminder(appointment) -> bool:
    """Send booking reminder email for an appointment."""
    return BookingReminderEmail.send(appointment)


def send_booking_cancellation(order, cancellation_reason: Optional[str] = None) -> bool:
    """Send booking cancellation email for an order."""
    return BookingCancellationEmail.send(order, cancellation_reason=cancellation_reason)


class CleaningCompleteEmail:
    """Email sent when a cleaning appointment is marked complete (staff completes job)."""

    @staticmethod
    def send(appointment, recipient_email: Optional[str] = None) -> bool:
        recipient_email = recipient_email or (
            appointment.order.customer.email if appointment.order and appointment.order.customer
            else (appointment.order.guest_email if appointment.order else None)
        )
        if not recipient_email:
            logger.warning(f"Cannot send cleaning complete email for appointment {appointment.id}: no email")
            return False
        customer_name = (
            appointment.order.customer.name if appointment.order and appointment.order.customer
            else (appointment.order.guest_name if appointment.order else None)
        ) or 'Customer'
        context = {
            'appointment': appointment,
            'customer_name': customer_name,
            'service_name': appointment.service.name if appointment.service else 'Cleaning',
            'order_number': appointment.order.order_number if appointment.order else '',
            'start_time': appointment.start_time,
            'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
        }
        subject = f"Cleaning Complete – {appointment.service.name if appointment.service else 'Your appointment'}"
        return EmailService.send_templated_email(
            template_name='cleaning_complete',
            context=context,
            subject=subject,
            recipient_list=[recipient_email],
        )


def send_cleaning_complete(appointment) -> bool:
    """Send cleaning complete email when staff marks appointment as completed."""
    return CleaningCompleteEmail.send(appointment)


def send_welcome_email(user, customer_name: Optional[str] = None) -> bool:
    """Send welcome email after sign up (optional – call from RegisterView if desired)."""
    recipient = user.email
    if not recipient:
        return False
    context = {
        'customer_name': customer_name or getattr(user, 'first_name', None) or user.email,
        'customer_email': user.email,
        'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
    }
    return EmailService.send_templated_email(
        template_name='welcome',
        context=context,
        subject='Welcome to MultiBook!',
        recipient_list=[recipient],
    )


def send_change_request_submitted(change_request) -> bool:
    """Notify manager/admin when a customer submits an order change request."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admin_emails = list(
        User.objects.filter(role__in=['admin', 'manager'], is_active=True)
        .exclude(email='')
        .values_list('email', flat=True)
        .distinct()
    )
    if not admin_emails:
        logger.warning('No admin/manager emails for change request notification')
        return False
    order = change_request.order
    requested_time_str = change_request.requested_time.strftime('%H:%M') if change_request.requested_time else None
    admin_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000').rstrip('/') + '/ad/'
    context = {
        'order_number': order.order_number,
        'requested_date': str(change_request.requested_date),
        'requested_time': requested_time_str,
        'reason': change_request.reason or '',
        'admin_url': admin_url,
    }
    return EmailService.send_templated_email(
        template_name='change_request_submitted',
        context=context,
        subject=f'Change request submitted – Order {order.order_number}',
        recipient_list=admin_emails,
    )


def send_change_request_approved(change_request) -> bool:
    """Notify customer when their order change request is approved."""
    order = change_request.order
    recipient = (order.customer.email if order.customer else None) or order.guest_email
    if not recipient:
        logger.warning(f'No email for change request approved notification (order {order.order_number})')
        return False
    customer_name = (order.customer.name if order.customer else None) or order.guest_name or 'Customer'
    requested_time_str = change_request.requested_time.strftime('%H:%M') if change_request.requested_time else None
    tracking_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000').rstrip('/') + f'/booking/track/{order.tracking_token}'
    context = {
        'customer_name': customer_name,
        'order_number': order.order_number,
        'requested_date': str(change_request.requested_date),
        'requested_time': requested_time_str,
        'tracking_url': tracking_url,
    }
    return EmailService.send_templated_email(
        template_name='change_request_approved',
        context=context,
        subject=f'Your change request has been approved – Order {order.order_number}',
        recipient_list=[recipient],
    )


def send_change_request_rejected(change_request) -> bool:
    """Notify customer when their order change request is rejected."""
    order = change_request.order
    recipient = (order.customer.email if order.customer else None) or order.guest_email
    if not recipient:
        logger.warning(f'No email for change request rejected notification (order {order.order_number})')
        return False
    customer_name = (order.customer.name if order.customer else None) or order.guest_name or 'Customer'
    requested_time_str = change_request.requested_time.strftime('%H:%M') if change_request.requested_time else None
    context = {
        'customer_name': customer_name,
        'order_number': order.order_number,
        'requested_date': str(change_request.requested_date),
        'requested_time': requested_time_str,
        'review_notes': change_request.review_notes or '',
    }
    return EmailService.send_templated_email(
        template_name='change_request_rejected',
        context=context,
        subject=f'Your change request – Order {order.order_number}',
        recipient_list=[recipient],
    )


def send_subscription_visit_change_request_submitted(change_request) -> bool:
    """Notify manager/admin when a customer submits a subscription visit change request."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admin_emails = list(
        User.objects.filter(role__in=['admin', 'manager'], is_active=True)
        .exclude(email='')
        .values_list('email', flat=True)
        .distinct()
    )
    if not admin_emails:
        logger.warning('No admin/manager emails for subscription visit change request notification')
        return False
    sub_appt = change_request.subscription_appointment
    sub = sub_appt.subscription
    requested_time_str = change_request.requested_time.strftime('%H:%M') if change_request.requested_time else None
    admin_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000').rstrip('/') + '/ad/'
    context = {
        'subscription_number': sub.subscription_number,
        'visit_number': sub_appt.sequence_number,
        'requested_date': str(change_request.requested_date),
        'requested_time': requested_time_str,
        'reason': change_request.reason or '',
        'admin_url': admin_url,
    }
    return EmailService.send_templated_email(
        template_name='subscription_visit_change_request_submitted',
        context=context,
        subject=f'Subscription visit change request – {sub.subscription_number} (Visit #{sub_appt.sequence_number})',
        recipient_list=admin_emails,
    )
