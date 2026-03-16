"""
Available slots calculation utilities.
"""
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.db.models import Q
from apps.staff.models import Staff, StaffSchedule, StaffService
from apps.appointments.models import Appointment
from apps.services.models import Service


def get_available_slots(
    postcode: str,
    service_id: int,
    target_date: date,
    staff_id: Optional[int] = None
) -> List[Dict]:
    """
    Calculate available time slots for a service on a given date.
    
    Args:
        postcode: Customer postcode (for filtering available staff)
        service_id: Service ID
        target_date: Target date for appointment
        staff_id: Optional specific staff ID (if customer selected a staff member)
    
    Returns:
        List of available time slots: [
            {'time': '09:00', 'available': True, 'staff_ids': [1, 2]},
            {'time': '10:00', 'available': False, 'reason': 'No staff available'},
            ...
        ]
    """
    from apps.core.postcode_utils import get_staff_for_postcode
    
    # Get service
    try:
        service = Service.objects.get(id=service_id, is_active=True)
    except Service.DoesNotExist:
        return []
    
    # Get service duration (including padding time)
    service_duration = service.duration
    if service.padding_time:
        service_duration += service.padding_time
    
    # Get available staff for this postcode and service
    if staff_id:
        # Specific staff selected
        try:
            available_staff = Staff.objects.filter(id=staff_id, is_active=True)
        except Staff.DoesNotExist:
            return []
    else:
        # Get staff who can service this postcode for this service (per-service or global areas)
        available_staff = get_staff_for_postcode(postcode, service_id=service_id)
        # Filter to only staff who provide this service
        available_staff = available_staff.filter(
            staff_services__service_id=service_id,
            staff_services__is_active=True
        ).distinct()
    
    if not available_staff.exists():
        return []
    
    # Get day of week (0=Monday, 6=Sunday)
    day_of_week = target_date.weekday()
    
    # Get all schedules for available staff on this day
    schedules = StaffSchedule.objects.filter(
        staff__in=available_staff,
        day_of_week=day_of_week,
        is_active=True
    ).select_related('staff')
    
    if not schedules.exists():
        return []
    
    # Get existing appointments for this date
    start_of_day = timezone.make_aware(datetime.combine(target_date, time.min))
    end_of_day = timezone.make_aware(datetime.combine(target_date, time.max))
    
    existing_appointments = Appointment.objects.filter(
        start_time__gte=start_of_day,
        start_time__lt=end_of_day + timedelta(days=1),
        status__in=['pending', 'confirmed', 'in_progress']
    ).select_related('staff', 'service')
    
    # Generate time slots at 30-minute intervals. Overlap check uses full service_duration
    # so back-to-back bookings are only offered when the slot does not overlap an existing
    # appointment (e.g. 1h service at 09:00 blocks 09:00-10:00; next offered slot is 10:00).
    slots = []
    slot_interval_minutes = 30
    
    # Combine all working hours from all schedules
    all_start_times = []
    all_end_times = []
    all_breaks = []
    staff_schedule_map = {}
    
    for schedule in schedules:
        staff_id = schedule.staff.id
        staff_schedule_map[staff_id] = {
            'start': schedule.start_time,
            'end': schedule.end_time,
            'breaks': schedule.breaks or [],
        }
        all_start_times.append(schedule.start_time)
        all_end_times.append(schedule.end_time)
        all_breaks.extend(schedule.breaks or [])
    
    if not all_start_times:
        return []
    
    # Use earliest start time and latest end time
    earliest_start = min(all_start_times)
    latest_end = max(all_end_times)
    
    # Generate slots from earliest_start to latest_end
    current_time = earliest_start
    slot_time = datetime.combine(target_date, current_time)
    
    while True:
        # Check if this slot would end after latest_end
        slot_end = slot_time + timedelta(minutes=service_duration)
        slot_end_time = slot_end.time()
        
        if slot_end_time > latest_end:
            break
        
        # Check if slot time is within any staff's working hours
        slot_available = False
        available_staff_ids = []
        
        for staff_id, schedule_info in staff_schedule_map.items():
            slot_start_time = slot_time.time()
            
            # Check if slot is within working hours
            if slot_start_time < schedule_info['start'] or slot_end_time > schedule_info['end']:
                continue
            
            # Check if slot conflicts with breaks
            in_break = False
            for break_period in schedule_info['breaks']:
                break_start = datetime.strptime(break_period.get('start', '00:00'), '%H:%M').time()
                break_end = datetime.strptime(break_period.get('end', '00:00'), '%H:%M').time()
                
                # Check if slot overlaps with break
                if (slot_start_time < break_end and slot_end_time > break_start):
                    in_break = True
                    break
            
            if in_break:
                continue
            
            # Check if slot conflicts with existing appointments for this staff
            slot_start_datetime = timezone.make_aware(slot_time)
            slot_end_datetime = timezone.make_aware(slot_end)
            
            conflicting_appointment = existing_appointments.filter(
                staff_id=staff_id
            ).filter(
                Q(start_time__lt=slot_end_datetime, end_time__gt=slot_start_datetime)
            ).exists()
            
            if conflicting_appointment:
                continue
            
            # Slot is available for this staff
            slot_available = True
            available_staff_ids.append(staff_id)
        
        # Add slot to results (unavailable = blocked by existing booking or outside hours)
        slot_dict = {
            'time': slot_time.strftime('%H:%M'),
            'available': slot_available,
            'staff_ids': available_staff_ids if slot_available else [],
        }
        
        if not slot_available:
            slot_dict['reason'] = 'Booked or unavailable'
        
        slots.append(slot_dict)
        
        # Move to next slot
        slot_time += timedelta(minutes=slot_interval_minutes)
        current_time = slot_time.time()
        
        # Safety check to avoid infinite loop
        if slot_time.date() > target_date:
            break
    
    return slots


def is_staff_available_for_slot(
    staff_id: int,
    start_dt: datetime,
    end_dt: datetime,
    exclude_appointment_id: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Check if a staff member is available for a given datetime range (for admin/manager edit validation).
    Returns (True, None) if available, (False, reason_string) if not.
    Excludes the appointment with exclude_appointment_id from conflict check (for editing existing).
    """
    from django.utils import timezone as tz
    if start_dt.tzinfo is None:
        start_dt = tz.make_aware(start_dt)
    if end_dt.tzinfo is None:
        end_dt = tz.make_aware(end_dt)
    target_date = start_dt.date()
    day_of_week = target_date.weekday()
    start_time = start_dt.time()
    end_time = end_dt.time()

    try:
        staff = Staff.objects.get(id=staff_id, is_active=True)
    except Staff.DoesNotExist:
        return False, 'Staff not found or inactive'

    schedule = StaffSchedule.objects.filter(
        staff=staff,
        day_of_week=day_of_week,
        is_active=True
    ).first()
    if not schedule:
        return False, 'Staff has no schedule for this day'
    if start_time < schedule.start_time or end_time > schedule.end_time:
        return False, 'Outside staff working hours'
    for break_period in (schedule.breaks or []):
        break_start = datetime.strptime(break_period.get('start', '00:00'), '%H:%M').time()
        break_end = datetime.strptime(break_period.get('end', '00:00'), '%H:%M').time()
        if (start_time < break_end and end_time > break_start):
            return False, 'Overlaps staff break'

    conflicting = Appointment.objects.filter(
        staff_id=staff_id,
        start_time__lt=end_dt,
        end_time__gt=start_dt,
        status__in=['pending', 'confirmed', 'in_progress']
    )
    if exclude_appointment_id:
        conflicting = conflicting.exclude(id=exclude_appointment_id)
    if conflicting.exists():
        return False, 'Staff has another appointment at this time'
    return True, None


def format_time_slot(time_str: str) -> str:
    """Format time slot for display (e.g., '09:00' -> '9:00 AM')."""
    try:
        hour, minute = map(int, time_str.split(':'))
        period = 'AM' if hour < 12 else 'PM'
        hour_12 = hour if hour <= 12 else hour - 12
        if hour_12 == 0:
            hour_12 = 12
        return f"{hour_12}:{minute:02d} {period}"
    except:
        return time_str
