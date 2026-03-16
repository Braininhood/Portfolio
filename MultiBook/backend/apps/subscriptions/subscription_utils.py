"""
Subscription utilities for automatic appointment generation.
"""
from datetime import datetime, timedelta, date, time
from typing import List, Optional, Tuple
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from apps.appointments.models import Appointment, CustomerAppointment
from apps.appointments.slots_utils import get_available_slots
from apps.customers.models import Customer
from apps.core.utils import can_cancel_or_reschedule
from .models import Subscription, SubscriptionAppointment


def calculate_subscription_dates(
    start_date: date,
    frequency: str,
    duration_months: int
) -> List[date]:
    """
    Calculate all appointment dates for a subscription.
    
    Args:
        start_date: Subscription start date
        frequency: 'weekly', 'biweekly', or 'monthly'
        duration_months: Duration in months
    
    Returns:
        List of appointment dates
    """
    dates = []
    current_date = start_date
    end_date = start_date + relativedelta(months=duration_months)
    
    if frequency == 'weekly':
        # Weekly: every 7 days
        while current_date < end_date:
            dates.append(current_date)
            current_date += timedelta(days=7)
    elif frequency == 'biweekly':
        # Bi-weekly: every 14 days
        while current_date < end_date:
            dates.append(current_date)
            current_date += timedelta(days=14)
    elif frequency == 'monthly':
        # Monthly: same day each month
        while current_date < end_date:
            dates.append(current_date)
            current_date += relativedelta(months=1)
    
    return dates


def find_available_slot_for_date(
    postcode: str,
    service_id: int,
    target_date: date,
    preferred_staff_id: Optional[int] = None,
    preferred_time: Optional[time] = None
) -> Optional[Tuple[time, int]]:
    """
    Find an available time slot for a given date.
    If preferred_time is not available, finds next available slot.
    If no slots available on this date, returns None.
    
    Args:
        postcode: Customer postcode
        service_id: Service ID
        target_date: Target date
        preferred_staff_id: Preferred staff ID (optional)
        preferred_time: Preferred time (optional)
    
    Returns:
        Tuple of (time, staff_id) if available, None otherwise
    """
    slots = get_available_slots(
        postcode=postcode,
        service_id=service_id,
        target_date=target_date,
        staff_id=preferred_staff_id
    )
    
    if not slots:
        return None
    
    # If preferred_time is provided, try to find it first
    if preferred_time:
        preferred_time_str = preferred_time.strftime('%H:%M')
        for slot in slots:
            if slot['time'] == preferred_time_str and slot['available']:
                staff_id = slot['staff_ids'][0] if slot['staff_ids'] else preferred_staff_id
                return (preferred_time, staff_id)
    
    # Find first available slot
    for slot in slots:
        if slot['available'] and slot['staff_ids']:
            slot_time = datetime.strptime(slot['time'], '%H:%M').time()
            staff_id = slot['staff_ids'][0]
            return (slot_time, staff_id)
    
    return None


def find_next_available_date(
    postcode: str,
    service_id: int,
    start_date: date,
    preferred_staff_id: Optional[int] = None,
    preferred_time: Optional[time] = None,
    max_days_ahead: int = 30
) -> Optional[Tuple[date, time, int]]:
    """
    Find the next available date and time slot.
    Checks up to max_days_ahead days from start_date.
    
    Args:
        postcode: Customer postcode
        service_id: Service ID
        start_date: Start date to check from
        preferred_staff_id: Preferred staff ID (optional)
        preferred_time: Preferred time (optional)
        max_days_ahead: Maximum days to look ahead
    
    Returns:
        Tuple of (date, time, staff_id) if available, None otherwise
    """
    current_date = start_date
    end_date = start_date + timedelta(days=max_days_ahead)
    
    while current_date <= end_date:
        slot_result = find_available_slot_for_date(
            postcode=postcode,
            service_id=service_id,
            target_date=current_date,
            preferred_staff_id=preferred_staff_id,
            preferred_time=preferred_time
        )
        
        if slot_result:
            slot_time, staff_id = slot_result
            return (current_date, slot_time, staff_id)
        
        current_date += timedelta(days=1)
    
    return None


def generate_subscription_appointments(
    subscription: Subscription,
    preferred_time: Optional[time] = None
) -> List[SubscriptionAppointment]:
    """
    Generate all appointments for a subscription.
    Intelligently finds available slots, moving to next day if needed.
    
    Args:
        subscription: Subscription instance
        preferred_time: Preferred time for appointments (optional)
    
    Returns:
        List of created SubscriptionAppointment instances
    """
    from apps.services.models import Service
    from apps.staff.models import Staff
    
    # Get subscription details
    service = subscription.service
    staff = subscription.staff
    
    # Get postcode from subscription or customer
    postcode = subscription.postcode
    if not postcode and subscription.customer:
        postcode = subscription.customer.postcode
    
    if not postcode:
        raise ValueError("Postcode is required to generate subscription appointments. Please provide postcode in subscription or customer address.")
    
    # Calculate all appointment dates
    appointment_dates = calculate_subscription_dates(
        start_date=subscription.start_date,
        frequency=subscription.frequency,
        duration_months=subscription.duration_months
    )
    
    created_appointments = []
    preferred_staff_id = staff.id if staff else None
    
    # Track preferred time for consistency (use first appointment's time for subsequent ones)
    current_preferred_time = preferred_time
    
    for sequence, appointment_date in enumerate(appointment_dates, start=1):
        # Find available slot for this date
        slot_result = find_available_slot_for_date(
            postcode=postcode,
            service_id=service.id,
            target_date=appointment_date,
            preferred_staff_id=preferred_staff_id,
            preferred_time=current_preferred_time
        )
        
        # If no slot available on this date, find next available date
        if not slot_result:
            next_available = find_next_available_date(
                postcode=postcode,
                service_id=service.id,
                start_date=appointment_date,
                preferred_staff_id=preferred_staff_id,
                preferred_time=current_preferred_time,
                max_days_ahead=14  # Look up to 2 weeks ahead
            )
            
            if not next_available:
                # Skip this appointment if no slots found within reasonable time
                continue
            
            appointment_date, slot_time, assigned_staff_id = next_available
        else:
            slot_time, assigned_staff_id = slot_result
        
        # Update preferred time for consistency (use first appointment's time)
        if sequence == 1:
            current_preferred_time = slot_time
        
        # Get staff instance
        try:
            assigned_staff = Staff.objects.get(id=assigned_staff_id)
        except Staff.DoesNotExist:
            continue
        
        # Calculate start and end datetime
        start_datetime = timezone.make_aware(
            datetime.combine(appointment_date, slot_time)
        )
        end_datetime = start_datetime + timedelta(minutes=service.duration)
        
        # Create appointment
        appointment = Appointment.objects.create(
            staff=assigned_staff,
            service=service,
            start_time=start_datetime,
            end_time=end_datetime,
            status='pending',
            appointment_type='subscription',
        )
        
        # Create customer appointment if customer exists
        customer_appointment = None
        if subscription.customer:
            customer_appointment = CustomerAppointment.objects.create(
                customer=subscription.customer,
                appointment=appointment,
                number_of_persons=1,
                total_price=subscription.price_per_appointment,
                payment_status='pending',
            )
            
            # Calculate cancellation deadline
            can_cancel_val, can_reschedule_val, deadline = can_cancel_or_reschedule(
                start_datetime,
                subscription.cancellation_policy_hours
            )
            customer_appointment.can_cancel = can_cancel_val
            customer_appointment.can_reschedule = can_reschedule_val
            customer_appointment.cancellation_deadline = deadline
            customer_appointment.save()
        
        # Create subscription appointment
        subscription_appointment = SubscriptionAppointment.objects.create(
            subscription=subscription,
            appointment=appointment,
            sequence_number=sequence,
            scheduled_date=appointment_date,
            status='scheduled',
        )
        
        created_appointments.append(subscription_appointment)
    
    # Update subscription next_appointment_date
    if created_appointments:
        first_appointment = created_appointments[0].appointment
        subscription.next_appointment_date = first_appointment.start_time.date()
        subscription.save(update_fields=['next_appointment_date'])
    
    return created_appointments
