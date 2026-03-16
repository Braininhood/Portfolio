"""
Calendar Sync app URL routing.
Calendar sync endpoints for all roles.
"""
from django.urls import path
from . import views

app_name = 'calendar_sync'

urlpatterns = [
    # Calendar status
    path('status/', views.CalendarStatusView.as_view(), name='calendar_status'),
    # Manual sync (all roles)
    path('sync/', views.ManualSyncView.as_view(), name='calendar_sync'),
    # Bulk sync (admin only)
    path('sync-bulk/', views.BulkSyncView.as_view(), name='calendar_sync_bulk'),
    # Custom event (all roles)
    path('events/', views.CustomEventCreateView.as_view(), name='calendar_events_create'),
    
    # Google Calendar OAuth
    path('google/connect/', views.GoogleCalendarConnectView.as_view(), name='google_connect'),
    path('google/callback/', views.google_calendar_callback, name='google_callback'),
    path('google/disconnect/', views.GoogleCalendarDisconnectView.as_view(), name='google_disconnect'),
    
    # Microsoft Outlook OAuth
    path('outlook/connect/', views.OutlookConnectView.as_view(), name='outlook_connect'),
    path('outlook/callback/', views.outlook_calendar_callback, name='outlook_callback'),
    path('outlook/disconnect/', views.OutlookDisconnectView.as_view(), name='outlook_disconnect'),
    
    # Apple Calendar .ics download
    path('ics/<int:appointment_id>/', views.ICalendarDownloadView.as_view(), name='ics_download'),
]
