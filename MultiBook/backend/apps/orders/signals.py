"""
Order signals.

Handles order status changes and triggers appointment creation, calendar sync, and email notifications.
"""
import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta, time as time_obj
from .models import Order, OrderItem

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Order)
def on_order_status_changed(sender, instance, **kwargs):
    """
    When order status changes to 'confirmed', create appointments for order items.
    This happens BEFORE save, so we can create appointments that reference the order.
    """
    if not instance.pk:
        # New order - don't process yet
        return
    
    try:
        # Get the old order from database
        old_order = Order.objects.get(pk=instance.pk)
        
        # Check if status changed from something to 'confirmed'
        if old_order.status != 'confirmed' and instance.status == 'confirmed':
            logger.info(f"Order {instance.order_number} status changed to 'confirmed' - creating appointments")
            
            # Create appointments for each order item
            create_appointments_for_order(instance)
            
            # Send confirmation email
            send_confirmation_email(instance)
            
    except Order.DoesNotExist:
        # Order doesn't exist yet (first save)
        pass
    except Exception as e:
        logger.error(f"Error in on_order_status_changed for order {instance.order_number}: {e}")


def create_appointments_for_order(order):
    """
    Create Appointment records for each OrderItem when order is confirmed.
    Also creates CustomerAppointment for each so they appear in customer My Bookings.
    
    Args:
        order: Order instance that was just confirmed
    """
    from apps.appointments.models import Appointment, CustomerAppointment
    from apps.core.utils import can_cancel_or_reschedule
    
    if not order.scheduled_date:
        logger.warning(f"Order {order.order_number} has no scheduled_date - cannot create appointments")
        return
    
    # Use scheduled_time or default to 9:00 AM
    scheduled_time = order.scheduled_time or time_obj(9, 0)
    
    # Calculate start datetime
    start_datetime = timezone.make_aware(
        datetime.combine(order.scheduled_date, scheduled_time)
    )
    
    # Track current time offset for multiple items
    current_start = start_datetime
    
    for item in order.items.all():
        # Skip if appointment already exists
        if item.appointment:
            logger.info(f"OrderItem {item.id} already has appointment {item.appointment.id}")
            continue
        
        # Ensure staff is assigned (required for appointment)
        if not item.staff:
            logger.warning(f"OrderItem {item.id} has no staff assigned - skipping appointment creation")
            continue
        
        # Calculate end time from service duration
        duration_minutes = item.service.duration
        end_datetime = current_start + timedelta(minutes=duration_minutes)
        
        # Create appointment (pending - admin/manager will confirm later)
        appointment = Appointment.objects.create(
            staff=item.staff,
            service=item.service,
            start_time=current_start,
            end_time=end_datetime,
            status='pending',
            appointment_type='order_item',
            order=order,  # Link to order
        )
        
        # Link appointment to order item
        item.appointment = appointment
        item.save()
        
        # Create CustomerAppointment so customer sees this in My Bookings (/cus/appointments/)
        if order.customer:
            policy_hours = getattr(order, 'cancellation_policy_hours', 24) or 24
            can_cancel_val, can_reschedule_val, deadline = can_cancel_or_reschedule(
                appointment.start_time, policy_hours
            )
            CustomerAppointment.objects.create(
                customer=order.customer,
                appointment=appointment,
                number_of_persons=1,
                total_price=item.total_price,
                payment_status=order.payment_status or 'pending',
                cancellation_policy_hours=policy_hours,
                can_cancel=can_cancel_val,
                can_reschedule=can_reschedule_val,
                cancellation_deadline=deadline,
            )
            logger.info(f"Created CustomerAppointment for appointment {appointment.id} (Order {order.order_number})")
        
        logger.info(f"Created appointment {appointment.id} for OrderItem {item.id} (Order {order.order_number})")
        
        # Move to next time slot (account for padding time)
        padding_minutes = item.service.padding_time or 0
        current_start = end_datetime + timedelta(minutes=padding_minutes)
    
    # After all appointments are created, sync to calendars
    sync_order_to_calendars(order)


def sync_order_to_calendars(order):
    """
    Sync order appointments to calendars of relevant users.
    
    This syncs to:
    - Customer calendar (if has account + calendar sync enabled)
    - Staff calendar (if calendar sync enabled)
    - Manager calendar (if manager of staff + calendar sync enabled)
    
    Args:
        order: Order instance
    """
    from apps.calendar_sync.services import (
        CalendarSyncService,
        build_customer_event_data,
        build_staff_event_data,
        build_manager_event_data
    )
    from apps.appointments.models import Appointment
    
    # Get all appointments for this order
    appointments = order.appointments.all()
    
    if not appointments.exists():
        logger.info(f"No appointments found for order {order.order_number} - skipping calendar sync")
        return
    
    for appointment in appointments:
        # 1. Sync to CUSTOMER calendar (if has account + sync enabled)
        if order.customer and order.customer.user:
            customer_profile = order.customer.user.profile
            if customer_profile.calendar_sync_enabled and customer_profile.calendar_provider != 'none':
                try:
                    event_data = build_customer_event_data(order, appointment)
                    event_id = CalendarSyncService.create_event(appointment, customer_profile, event_data)
                    
                    if event_id:
                        # Update appointment.calendar_event_id
                        appointment.calendar_event_id = appointment.calendar_event_id or {}
                        appointment.calendar_event_id[customer_profile.calendar_provider] = event_id
                        
                        # Update appointment.calendar_synced_to
                        synced_to = appointment.calendar_synced_to or []
                        if customer_profile.calendar_provider not in synced_to:
                            synced_to.append(customer_profile.calendar_provider)
                        appointment.calendar_synced_to = synced_to
                        appointment.save()
                        
                        logger.info(f"Synced appointment {appointment.id} to customer {order.customer.user.email} calendar ({customer_profile.calendar_provider})")
                except Exception as e:
                    logger.error(f"Error syncing appointment {appointment.id} to customer calendar: {e}")
        
        # 2. Sync to STAFF calendar (if sync enabled)
        if appointment.staff and appointment.staff.user:
            staff_profile = appointment.staff.user.profile
            if staff_profile.calendar_sync_enabled and staff_profile.calendar_provider != 'none':
                try:
                    event_data = build_staff_event_data(order, appointment)
                    event_id = CalendarSyncService.create_event(appointment, staff_profile, event_data)
                    
                    if event_id:
                        # Update appointment.calendar_event_id
                        appointment.calendar_event_id = appointment.calendar_event_id or {}
                        appointment.calendar_event_id[staff_profile.calendar_provider] = event_id
                        
                        # Update appointment.calendar_synced_to
                        synced_to = appointment.calendar_synced_to or []
                        if staff_profile.calendar_provider not in synced_to:
                            synced_to.append(staff_profile.calendar_provider)
                        appointment.calendar_synced_to = synced_to
                        appointment.save()
                        
                        logger.info(f"Synced appointment {appointment.id} to staff {appointment.staff.user.email} calendar ({staff_profile.calendar_provider})")
                except Exception as e:
                    logger.error(f"Error syncing appointment {appointment.id} to staff calendar: {e}")
        
        # 3. Sync to MANAGER calendar (if manager exists + sync enabled)
        # Note: Staff model doesn't have a manager field yet, so this is a placeholder
        # When manager relationship is added, uncomment this:
        # if appointment.staff.manager and appointment.staff.manager.user:
        #     manager_profile = appointment.staff.manager.user.profile
        #     if manager_profile.calendar_sync_enabled and manager_profile.calendar_provider != 'none':
        #         try:
        #             event_data = build_manager_event_data(order, appointment)
        #             event_id = CalendarSyncService.create_event(appointment, manager_profile, event_data)
        #             # ... update appointment.calendar_event_id ...
        #         except Exception as e:
        #             logger.error(f"Error syncing appointment {appointment.id} to manager calendar: {e}")


def send_confirmation_email(order):
    """Send booking confirmation email when order is confirmed."""
    try:
        from apps.notifications.email_service import send_booking_confirmation
        
        # Send confirmation email
        success = send_booking_confirmation(order)
        
        if success:
            logger.info(f"Confirmation email sent for order {order.order_number}")
        else:
            logger.warning(f"Failed to send confirmation email for order {order.order_number}")
            
    except Exception as e:
        logger.error(f"Error sending confirmation email for order {order.order_number}: {e}")
        # Don't raise exception - email failure shouldn't break order confirmation
