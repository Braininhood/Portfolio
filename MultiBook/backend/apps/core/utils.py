"""
Core utility functions.
"""
import secrets
import string
from datetime import datetime, timedelta
from django.utils import timezone


def generate_subscription_number():
    """
    Generate unique subscription number.
    Format: SUB-YYYYMMDD-XXXXXX
    """
    date_str = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"SUB-{date_str}-{random_str}"


def generate_order_number():
    """
    Generate unique order number.
    Format: ORD-YYYYMMDD-XXXXXX
    """
    date_str = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"ORD-{date_str}-{random_str}"


def generate_tracking_token():
    """
    Generate unique tracking token for guest orders/subscriptions.
    Used for guest access via email link.
    """
    return secrets.token_urlsafe(32)


def can_cancel_or_reschedule(appointment_datetime, policy_hours=24):
    """
    Check if appointment/order can be cancelled or rescheduled based on 24-hour policy.
    
    Args:
        appointment_datetime: Datetime of appointment/order
        policy_hours: Cancellation policy hours (default: 24)
    
    Returns:
        Tuple: (can_cancel, can_reschedule, cancellation_deadline)
    """
    now = timezone.now()
    
    # Ensure appointment_datetime is timezone-aware
    if timezone.is_naive(appointment_datetime):
        appointment_datetime = timezone.make_aware(appointment_datetime)
    
    # Calculate cancellation deadline (policy_hours before appointment)
    cancellation_deadline = appointment_datetime - timedelta(hours=policy_hours)
    
    # Check if we're past the cancellation deadline
    can_cancel = now < cancellation_deadline
    can_reschedule = now < cancellation_deadline
    
    return can_cancel, can_reschedule, cancellation_deadline
