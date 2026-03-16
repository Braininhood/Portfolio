"""
Calendar Sync Service

Handles calendar integration with Google Calendar, Microsoft Outlook, and Apple Calendar.
Provides functions to create, update, and delete calendar events.
"""
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

# Import OAuth libraries (optional - will handle gracefully if not installed)
try:
    from google.oauth2.credentials import Credentials as GoogleCredentials
    from google.auth.transport.requests import Request as GoogleRequest
    from googleapiclient.discovery import build as google_build
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False
    logger.warning("Google Calendar API libraries not installed. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")

try:
    from msal import ConfidentialClientApplication
    OUTLOOK_AVAILABLE = True
except ImportError:
    OUTLOOK_AVAILABLE = False
    logger.warning("Microsoft Graph API libraries not installed. Install with: pip install msal msgraph-sdk")


def _get_appointments_for_user(user):
    """Get appointments relevant to user for calendar sync (future and non-cancelled)."""
    from django.utils import timezone
    from apps.appointments.models import Appointment
    from apps.orders.models import Order
    from apps.staff.models import Staff

    now = timezone.now()
    provider = (user.profile.calendar_provider or 'none') if hasattr(user, 'profile') else 'none'
    synced_key = 'calendar_synced_to'  # appointment field

    if user.role == 'staff':
        try:
            staff = Staff.objects.get(user=user)
            # Staff can only sync confirmed appointments (not pending)
            qs = Appointment.objects.filter(
                staff=staff,
                start_time__gte=now,
                status__in=['confirmed'],
            )
        except Staff.DoesNotExist:
            return []
    elif user.role == 'customer':
        from apps.customers.models import Customer
        try:
            customer = Customer.objects.get(user=user)
            order_ids = Order.objects.filter(customer=customer).values_list('id', flat=True)
            qs = Appointment.objects.filter(
                order_id__in=order_ids,
                start_time__gte=now,
                status__in=['pending', 'confirmed'],
            )
        except Customer.DoesNotExist:
            return []
    else:
        # admin/manager: sync all future appointments (optional; for bulk sync we pass user_ids)
        return []

    out = []
    for apt in qs:
        synced_to = getattr(apt, synced_key, None) or []
        if provider != 'none' and provider not in synced_to:
            out.append(apt)
    return out


def sync_user_appointments_to_calendar(user):
    """
    Sync current user's appointments to their connected calendar.
    Returns (synced_count: int, error_message: Optional[str]).
    """
    from apps.accounts.models import Profile
    from apps.appointments.models import Appointment

    profile, _ = Profile.objects.get_or_create(user=user)

    if not profile.calendar_sync_enabled or profile.calendar_provider in ('none', None, ''):
        return 0, 'Calendar not connected'

    appointments = _get_appointments_for_user(user)
    synced_count = 0
    last_error = None

    for appointment in appointments:
        if not appointment.order:
            continue
        order = appointment.order
        if user.role == 'staff':
            event_data = build_staff_event_data(order, appointment)
        elif user.role == 'customer':
            event_data = build_customer_event_data(order, appointment)
        else:
            event_data = build_manager_event_data(order, appointment)

        event_id = CalendarSyncService.create_event(appointment, profile, event_data)
        if event_id:
            synced_count += 1
            appointment.calendar_event_id = appointment.calendar_event_id or {}
            appointment.calendar_event_id[profile.calendar_provider] = event_id
            appointment.calendar_synced_to = list(set((appointment.calendar_synced_to or []) + [profile.calendar_provider]))
            appointment.save()
        else:
            last_error = 'Failed to create one or more events'

    settings_json = profile.calendar_sync_settings or {}
    settings_json['last_sync_at'] = timezone.now().isoformat()
    # Error recovery: when nothing synced but we had appointments, suggest reconnecting
    if last_error and synced_count == 0 and appointments:
        last_error = 'Sync failed. Try syncing again or reconnect your calendar in settings.'
    settings_json['last_sync_error'] = last_error
    profile.calendar_sync_settings = settings_json
    profile.save()

    return synced_count, last_error


class CalendarSyncService:
    """Base calendar sync service."""

    @staticmethod
    def create_event(appointment, profile, event_data: Dict[str, Any]) -> Optional[str]:
        """
        Create calendar event for an appointment.
        
        Args:
            appointment: Appointment instance
            profile: Profile instance with calendar sync enabled
            event_data: Event data dictionary with summary, description, location, start, end
            
        Returns:
            Event ID from calendar provider, or None if failed
        """
        provider = profile.calendar_provider
        
        if provider == 'google':
            return GoogleCalendarService.create_event(appointment, profile, event_data)
        elif provider == 'outlook':
            return OutlookCalendarService.create_event(appointment, profile, event_data)
        elif provider == 'apple':
            # Apple Calendar uses .ics files (not API sync)
            return AppleCalendarService.create_event(appointment, profile, event_data)
        else:
            logger.warning(f"Unknown calendar provider: {provider}")
            return None
    
    @staticmethod
    def update_event(appointment, profile, event_data: Dict[str, Any]) -> bool:
        """Update existing calendar event."""
        provider = profile.calendar_provider
        
        if provider == 'google':
            return GoogleCalendarService.update_event(appointment, profile, event_data)
        elif provider == 'outlook':
            return OutlookCalendarService.update_event(appointment, profile, event_data)
        elif provider == 'apple':
            # Apple Calendar events can't be updated via API
            return False
        else:
            return False
    
    @staticmethod
    def delete_event(appointment, profile) -> bool:
        """Delete calendar event."""
        provider = profile.calendar_provider
        
        if provider == 'google':
            return GoogleCalendarService.delete_event(appointment, profile)
        elif provider == 'outlook':
            return OutlookCalendarService.delete_event(appointment, profile)
        elif provider == 'apple':
            # Apple Calendar events can't be deleted via API
            return False
        else:
            return False

    @staticmethod
    def create_custom_event(profile, event_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a standalone calendar event (not linked to an appointment).
        event_data: summary, start (ISO), end (ISO), description?, location?
        Returns event ID or None.
        """
        provider = profile.calendar_provider
        if provider == 'google':
            return GoogleCalendarService.create_standalone_event(profile, event_data)
        elif provider == 'outlook':
            return OutlookCalendarService.create_standalone_event(profile, event_data)
        elif provider == 'apple':
            # Apple: return placeholder; frontend can offer .ics download
            return f"custom_ics_{int(timezone.now().timestamp())}"
        return None


class GoogleCalendarService:
    """Google Calendar API integration."""
    
    @staticmethod
    def _get_credentials(profile):
        """Get Google Calendar credentials from profile, refreshing if needed."""
        try:
            if not GOOGLE_CALENDAR_AVAILABLE:
                return None
            
            if not profile.calendar_access_token:
                return None
            
            # Use calendar-specific credentials (separate from login OAuth)
            client_id = getattr(settings, 'GOOGLE_CALENDAR_CLIENT_ID', None) or getattr(settings, 'GOOGLE_CLIENT_ID', None)
            client_secret = getattr(settings, 'GOOGLE_CALENDAR_CLIENT_SECRET', None) or getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
            
            credentials = GoogleCredentials(
                token=profile.calendar_access_token,
                refresh_token=profile.calendar_refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                token_uri='https://oauth2.googleapis.com/token'
            )
            
            # Refresh token if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(GoogleRequest())
                # Save refreshed token
                profile.calendar_access_token = credentials.token
                profile.save()
            
            return credentials
        except Exception as e:
            logger.error(f"Error getting Google Calendar credentials: {e}")
            return None
    
    @staticmethod
    def create_event(appointment, profile, event_data: Dict[str, Any]) -> Optional[str]:
        """Create event in Google Calendar."""
        try:
            if not GOOGLE_CALENDAR_AVAILABLE:
                logger.warning("Google Calendar API libraries not installed")
                return None
            
            credentials = GoogleCalendarService._get_credentials(profile)
            if not credentials:
                logger.error(f"Could not get credentials for profile {profile.id}")
                return None
            
            # Build Google Calendar API service
            if not GOOGLE_CALENDAR_AVAILABLE:
                return None
            service = google_build('calendar', 'v3', credentials=credentials)
            
            # Convert event data to Google Calendar format
            start_datetime = datetime.fromisoformat(event_data['start'].replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(event_data['end'].replace('Z', '+00:00'))
            
            google_event = {
                'summary': event_data.get('summary', 'Appointment'),
                'description': event_data.get('description', ''),
                'location': event_data.get('location', ''),
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Europe/London',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Europe/London',
                },
            }
            
            # Create event
            calendar_id = profile.calendar_calendar_id or 'primary'
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=google_event
            ).execute()
            
            event_id = created_event.get('id')
            logger.info(f"Created Google Calendar event {event_id} for appointment {appointment.id}")
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {e}")
            return None

    @staticmethod
    def create_standalone_event(profile, event_data: Dict[str, Any]) -> Optional[str]:
        """Create a standalone event (no appointment)."""
        try:
            if not GOOGLE_CALENDAR_AVAILABLE:
                return None
            credentials = GoogleCalendarService._get_credentials(profile)
            if not credentials:
                return None
            service = google_build('calendar', 'v3', credentials=credentials)
            start_datetime = datetime.fromisoformat(event_data['start'].replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(event_data['end'].replace('Z', '+00:00'))
            google_event = {
                'summary': event_data.get('summary', 'Event'),
                'description': event_data.get('description', ''),
                'location': event_data.get('location', ''),
                'start': {'dateTime': start_datetime.isoformat(), 'timeZone': 'Europe/London'},
                'end': {'dateTime': end_datetime.isoformat(), 'timeZone': 'Europe/London'},
            }
            calendar_id = profile.calendar_calendar_id or 'primary'
            created = service.events().insert(calendarId=calendar_id, body=google_event).execute()
            return created.get('id')
        except Exception as e:
            logger.error(f"Error creating standalone Google event: {e}")
            return None
    
    @staticmethod
    def update_event(appointment, profile, event_data: Dict[str, Any]) -> bool:
        """Update event in Google Calendar."""
        try:
            if not GOOGLE_CALENDAR_AVAILABLE:
                return False
            
            event_id = appointment.calendar_event_id.get('google')
            if not event_id:
                return False
            
            credentials = GoogleCalendarService._get_credentials(profile)
            if not credentials:
                return False
            
            if not GOOGLE_CALENDAR_AVAILABLE:
                return False
            service = google_build('calendar', 'v3', credentials=credentials)
            
            # Get existing event
            calendar_id = profile.calendar_calendar_id or 'primary'
            existing_event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Update event data
            start_datetime = datetime.fromisoformat(event_data['start'].replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(event_data['end'].replace('Z', '+00:00'))
            
            existing_event['summary'] = event_data.get('summary', existing_event.get('summary'))
            existing_event['description'] = event_data.get('description', existing_event.get('description', ''))
            existing_event['location'] = event_data.get('location', existing_event.get('location', ''))
            existing_event['start'] = {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'Europe/London',
            }
            existing_event['end'] = {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Europe/London',
            }
            
            # Update event
            service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=existing_event
            ).execute()
            
            logger.info(f"Updated Google Calendar event {event_id} for appointment {appointment.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating Google Calendar event: {e}")
            return False
    
    @staticmethod
    def delete_event(appointment, profile) -> bool:
        """Delete event from Google Calendar."""
        try:
            if not GOOGLE_CALENDAR_AVAILABLE:
                return False
            
            event_id = appointment.calendar_event_id.get('google')
            if not event_id:
                return False
            
            credentials = GoogleCalendarService._get_credentials(profile)
            if not credentials:
                return False
            
            if not GOOGLE_CALENDAR_AVAILABLE:
                return False
            service = google_build('calendar', 'v3', credentials=credentials)
            calendar_id = profile.calendar_calendar_id or 'primary'
            
            # Delete event
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Remove from appointment.calendar_event_id
            appointment.calendar_event_id = appointment.calendar_event_id or {}
            appointment.calendar_event_id.pop('google', None)
            synced_to = appointment.calendar_synced_to or []
            if 'google' in synced_to:
                synced_to.remove('google')
            appointment.calendar_synced_to = synced_to
            appointment.save()
            
            logger.info(f"Deleted Google Calendar event {event_id} for appointment {appointment.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting Google Calendar event: {e}")
            return False


class OutlookCalendarService:
    """Microsoft Outlook/Graph API integration."""
    
    @staticmethod
    def _get_access_token(profile):
        """Get Microsoft Graph access token from profile, refreshing if needed."""
        try:
            if not profile.calendar_access_token:
                return None
            
            # For now, return stored token (token refresh logic can be added later)
            # Microsoft Graph tokens typically last 1 hour
            return profile.calendar_access_token
        except Exception as e:
            logger.error(f"Error getting Outlook access token: {e}")
            return None
    
    @staticmethod
    def create_event(appointment, profile, event_data: Dict[str, Any]) -> Optional[str]:
        """Create event in Outlook Calendar via Microsoft Graph API."""
        try:
            if not OUTLOOK_AVAILABLE:
                logger.warning("Microsoft Graph API libraries not installed")
                return None
            
            access_token = OutlookCalendarService._get_access_token(profile)
            if not access_token:
                logger.error(f"Could not get access token for profile {profile.id}")
                return None
            
            # Build Microsoft Graph API request
            import requests
            
            calendar_id = profile.calendar_calendar_id or 'calendar'
            graph_endpoint = f'https://graph.microsoft.com/v1.0/me/calendars/{calendar_id}/events'
            
            # Convert event data to Microsoft Graph format
            start_datetime = datetime.fromisoformat(event_data['start'].replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(event_data['end'].replace('Z', '+00:00'))
            
            graph_event = {
                'subject': event_data.get('summary', 'Appointment'),
                'body': {
                    'contentType': 'text',
                    'content': event_data.get('description', '')
                },
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Europe/London'
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Europe/London'
                },
                'location': {
                    'displayName': event_data.get('location', '')
                }
            }
            
            # Create event via Microsoft Graph API
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(graph_endpoint, json=graph_event, headers=headers)
            
            if response.status_code == 201:
                created_event = response.json()
                event_id = created_event.get('id')
                logger.info(f"Created Outlook Calendar event {event_id} for appointment {appointment.id}")
                return event_id
            else:
                logger.error(f"Error creating Outlook Calendar event: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            logger.error(f"Error creating Outlook Calendar event: {e}")
            return None

    @staticmethod
    def create_standalone_event(profile, event_data: Dict[str, Any]) -> Optional[str]:
        """Create a standalone event (no appointment)."""
        try:
            if not OUTLOOK_AVAILABLE:
                return None
            access_token = OutlookCalendarService._get_access_token(profile)
            if not access_token:
                return None
            start_datetime = datetime.fromisoformat(event_data['start'].replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(event_data['end'].replace('Z', '+00:00'))
            graph_event = {
                'subject': event_data.get('summary', 'Event'),
                'body': {'contentType': 'text', 'content': event_data.get('description', '')},
                'start': {'dateTime': start_datetime.isoformat(), 'timeZone': 'Europe/London'},
                'end': {'dateTime': end_datetime.isoformat(), 'timeZone': 'Europe/London'},
                'location': {'displayName': event_data.get('location', '')},
            }
            calendar_id = profile.calendar_calendar_id or 'calendar'
            url = f'https://graph.microsoft.com/v1.0/me/calendars/{calendar_id}/events'
            resp = requests.post(url, json=graph_event, headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'})
            if resp.status_code in (200, 201):
                return resp.json().get('id')
            return None
        except Exception as e:
            logger.error(f"Error creating standalone Outlook event: {e}")
            return None
    
    @staticmethod
    def update_event(appointment, profile, event_data: Dict[str, Any]) -> bool:
        """Update event in Outlook Calendar."""
        try:
            if not OUTLOOK_AVAILABLE:
                return False
            
            event_id = appointment.calendar_event_id.get('outlook')
            if not event_id:
                return False
            
            access_token = OutlookCalendarService._get_access_token(profile)
            if not access_token:
                return False
            
            # Build Microsoft Graph API request
            calendar_id = profile.calendar_calendar_id or 'calendar'
            graph_endpoint = f'https://graph.microsoft.com/v1.0/me/calendars/{calendar_id}/events/{event_id}'
            
            # Convert event data to Microsoft Graph format
            start_datetime = datetime.fromisoformat(event_data['start'].replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(event_data['end'].replace('Z', '+00:00'))
            
            graph_event = {
                'subject': event_data.get('summary', 'Appointment'),
                'body': {
                    'contentType': 'text',
                    'content': event_data.get('description', '')
                },
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Europe/London'
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Europe/London'
                },
                'location': {
                    'displayName': event_data.get('location', '')
                }
            }
            
            # Update event via Microsoft Graph API
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.patch(graph_endpoint, json=graph_event, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"Updated Outlook Calendar event {event_id} for appointment {appointment.id}")
                return True
            else:
                logger.error(f"Error updating Outlook Calendar event: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Error updating Outlook Calendar event: {e}")
            return False
    
    @staticmethod
    def delete_event(appointment, profile) -> bool:
        """Delete event from Outlook Calendar."""
        try:
            if not OUTLOOK_AVAILABLE:
                return False
            
            event_id = appointment.calendar_event_id.get('outlook')
            if not event_id:
                return False
            
            access_token = OutlookCalendarService._get_access_token(profile)
            if not access_token:
                return False
            
            # Build Microsoft Graph API request
            calendar_id = profile.calendar_calendar_id or 'calendar'
            graph_endpoint = f'https://graph.microsoft.com/v1.0/me/calendars/{calendar_id}/events/{event_id}'
            
            # Delete event via Microsoft Graph API
            headers = {
                'Authorization': f'Bearer {access_token}',
            }
            
            response = requests.delete(graph_endpoint, headers=headers)
            
            if response.status_code == 204:
                # Remove from appointment.calendar_event_id
                appointment.calendar_event_id = appointment.calendar_event_id or {}
                appointment.calendar_event_id.pop('outlook', None)
                synced_to = appointment.calendar_synced_to or []
                if 'outlook' in synced_to:
                    synced_to.remove('outlook')
                appointment.calendar_synced_to = synced_to
                appointment.save()
                
                logger.info(f"Deleted Outlook Calendar event {event_id} for appointment {appointment.id}")
                return True
            else:
                logger.error(f"Error deleting Outlook Calendar event: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting Outlook Calendar event: {e}")
            return False


class AppleCalendarService:
    """Apple Calendar integration (via .ics file generation)."""
    
    @staticmethod
    def create_event(appointment, profile, event_data: Dict[str, Any]) -> Optional[str]:
        """Generate .ics file for Apple Calendar (or any calendar app)."""
        try:
            # Generate .ics file content
            ics_content = AppleCalendarService._generate_ics_content(event_data)
            
            # For now, just log - in future, this could:
            # 1. Store .ics file on server and return download URL
            # 2. Email .ics file to user
            # 3. Return .ics content for frontend to handle
            
            logger.info(f"Apple Calendar: Generated .ics content for appointment {appointment.id}")
            
            # Store reference in appointment (could be URL to .ics file)
            event_id = f"ics_{appointment.id}_{int(timezone.now().timestamp())}"
            appointment.calendar_event_id.setdefault('apple', event_id)
            appointment.save()
            
            return event_id
        except Exception as e:
            logger.error(f"Error creating Apple Calendar .ics file: {e}")
            return None
    
    @staticmethod
    def _generate_ics_content(event_data: Dict[str, Any]) -> str:
        """Generate .ics (iCalendar) file content."""
        start_dt = event_data.get('start')
        end_dt = event_data.get('end')
        
        # Convert datetime to ICS format (YYYYMMDDTHHMMSSZ)
        def to_ics_datetime(dt):
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = timezone.make_aware(dt)
            return dt.strftime('%Y%m%dT%H%M%SZ')
        
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MultiBook//Booking System//EN
BEGIN:VEVENT
UID:{event_data.get('uid', f"multibook-{int(timezone.now().timestamp())}")}
DTSTART:{to_ics_datetime(start_dt)}
DTEND:{to_ics_datetime(end_dt)}
SUMMARY:{event_data.get('summary', 'Appointment')}
DESCRIPTION:{event_data.get('description', '').replace(chr(10), '\\n')}
LOCATION:{event_data.get('location', '')}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
        
        return ics_content


# Helper functions for building event data by role

def build_customer_event_data(order, appointment) -> Dict[str, Any]:
    """Build calendar event data for customer role."""
    customer_name = order.customer.name if order.customer else order.guest_name
    staff_name = appointment.staff.name if appointment.staff else "Staff"
    staff_phone = getattr(appointment.staff, 'phone', None) if appointment.staff else None
    
    return {
        "summary": f"Service: {appointment.service.name}",
        "description": f"""Order: {order.order_number}
Staff: {staff_name}
Phone: {staff_phone or 'N/A'}
Notes: {order.notes or 'None'}""".strip(),
        "location": f"{order.address_line1}, {order.city}, {order.postcode}",
        "start": appointment.start_time.isoformat(),
        "end": appointment.end_time.isoformat(),
        "uid": f"multibook-customer-{appointment.id}-{order.id}",
    }


def build_staff_event_data(order, appointment) -> Dict[str, Any]:
    """Build calendar event data for staff role (when order exists)."""
    customer_name = order.customer.name if order.customer else order.guest_name
    customer_email = order.customer.email if order.customer else order.guest_email
    customer_phone = order.customer.phone if order.customer else order.guest_phone
    
    return {
        "summary": f"{appointment.service.name} at {customer_name}'s",
        "description": f"""Customer: {customer_name}
Email: {customer_email or 'N/A'}
Phone: {customer_phone or 'N/A'}
Order: {order.order_number}
Special Instructions: {order.notes or 'None'}
Address: {order.address_line1}, {order.city}, {order.postcode}""".strip(),
        "location": f"{order.address_line1}, {order.city}, {order.postcode}",
        "start": appointment.start_time.isoformat(),
        "end": appointment.end_time.isoformat(),
        "uid": f"multibook-staff-{appointment.id}-{order.id}",
    }


def build_staff_event_data_from_appointment(appointment) -> Dict[str, Any]:
    """Build calendar event data for staff when appointment has no order (subscription/single)."""
    service_name = appointment.service.name if appointment.service else "Job"
    # Prefer customer from customer_booking, else subscription, else minimal
    desc_parts = [f"Service: {service_name}"]
    location = ""
    try:
        cb = getattr(appointment, "customer_booking", None)
        if cb and getattr(cb, "customer", None):
            c = cb.customer
            desc_parts.append(f"Customer: {getattr(c, 'name', 'N/A')}")
            desc_parts.append(f"Email: {getattr(c, 'email', 'N/A')}")
            desc_parts.append(f"Phone: {getattr(c, 'phone', 'N/A')}")
        if appointment.subscription_id and getattr(appointment, "subscription", None):
            sub = appointment.subscription
            if getattr(sub, "address_line1", None):
                location = f"{sub.address_line1}, {getattr(sub, 'city', '')}, {getattr(sub, 'postcode', '')}".strip(", ")
            if getattr(sub, "subscription_number", None):
                desc_parts.append(f"Subscription: {sub.subscription_number}")
        if appointment.order_id and getattr(appointment, "order", None):
            order = appointment.order
            desc_parts.append(f"Order: {order.order_number}")
            location = f"{order.address_line1}, {order.city}, {order.postcode}"
    except Exception:
        pass
    return {
        "summary": f"{service_name}",
        "description": "\n".join(desc_parts),
        "location": location or "N/A",
        "start": appointment.start_time.isoformat(),
        "end": appointment.end_time.isoformat(),
        "uid": f"multibook-staff-{appointment.id}-{getattr(appointment, 'order_id', 0) or getattr(appointment, 'subscription_id', 0) or 0}",
    }


def build_manager_event_data(order, appointment) -> Dict[str, Any]:
    """Build calendar event data for manager role."""
    customer_name = order.customer.name if order.customer else order.guest_name
    customer_email = order.customer.email if order.customer else order.guest_email
    customer_phone = order.customer.phone if order.customer else order.guest_phone
    staff_name = appointment.staff.name if appointment.staff else "Staff"
    staff_phone = getattr(appointment.staff, 'phone', None) if appointment.staff else None
    
    return {
        "summary": f"{staff_name} - {appointment.service.name}",
        "description": f"""Staff: {staff_name} ({staff_phone or 'N/A'})
Customer: {customer_name}
Email: {customer_email or 'N/A'}
Phone: {customer_phone or 'N/A'}
Order: {order.order_number}
Service: {appointment.service.name}
Address: {order.address_line1}, {order.city}, {order.postcode}
Notes: {order.notes or 'None'}""".strip(),
        "location": f"{order.address_line1}, {order.city}, {order.postcode}",
        "start": appointment.start_time.isoformat(),
        "end": appointment.end_time.isoformat(),
        "uid": f"multibook-manager-{appointment.id}-{order.id}",
    }
