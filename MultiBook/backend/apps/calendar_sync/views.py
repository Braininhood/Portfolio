"""
Calendar Sync app views.

Handles OAuth 2.0 flows for Google Calendar and Microsoft Outlook,
and .ics file generation/download for Apple Calendar.
"""
import logging
import json
from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.models import Profile
from apps.appointments.models import Appointment

logger = logging.getLogger(__name__)

# Import OAuth libraries (optional - will handle gracefully if not installed)
try:
    from google_auth_oauthlib.flow import Flow
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
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


class GoogleCalendarConnectView(APIView):
    """Initiate Google Calendar OAuth 2.0 authorization flow."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Start Google Calendar OAuth flow."""
        if not GOOGLE_CALENDAR_AVAILABLE:
            return Response({
                'success': False,
                'error': {
                    'code': 'LIBRARY_NOT_INSTALLED',
                    'message': 'Google Calendar API libraries not installed. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib'
                }
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            profile, _ = Profile.objects.get_or_create(user=request.user)
            
            # Google Calendar OAuth 2.0 configuration
            # Use calendar-specific credentials (separate from login OAuth)
            client_id = getattr(settings, 'GOOGLE_CALENDAR_CLIENT_ID', None)
            client_secret = getattr(settings, 'GOOGLE_CALENDAR_CLIENT_SECRET', None)
            redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/calendar/google/callback/')
            
            # Fallback to general Google OAuth credentials if calendar-specific not set
            if not client_id:
                client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
            if not client_secret:
                client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
            
            if not client_id or not client_secret:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'MISSING_CONFIG',
                        'message': 'Google OAuth credentials not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in settings.'
                    }
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    'web': {
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                        'token_uri': 'https://oauth2.googleapis.com/token',
                        'redirect_uris': [redirect_uri],
                        'scopes': ['https://www.googleapis.com/auth/calendar']
                    }
                },
                scopes=['https://www.googleapis.com/auth/calendar'],
                redirect_uri=redirect_uri
            )
            
            # Get authorization URL
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'  # Force consent to get refresh token
            )
            
            logger.info(f"Created authorization URL with redirect_uri: {redirect_uri}, state: {state[:20]}...")
            
            # Store state->user_id mapping in cache (more reliable than session for OAuth callbacks)
            from django.core.cache import cache
            cache_key = f"google_oauth_state_{state}"
            cache.set(cache_key, request.user.id, timeout=600)  # 10 minutes expiry
            
            # Also store in session as fallback
            request.session['google_oauth_state'] = state
            request.session['google_oauth_user_id'] = request.user.id
            
            # Return original authorization URL (don't modify state)
            return Response({
                'success': True,
                'data': {
                    'authorization_url': authorization_url,
                    'state': state
                }
            })
            
        except Exception as e:
            logger.error(f"Error initiating Google Calendar OAuth: {e}")
            return Response({
                'success': False,
                'error': {
                    'code': 'OAUTH_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])  # Allow callback without authentication (Google redirects here)
def google_calendar_callback(request):
    """Handle Google Calendar OAuth callback."""
    if not GOOGLE_CALENDAR_AVAILABLE:
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/cus/calendar/settings?error=library_not_installed")
    
    try:
        # Get authorization code and state from callback
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        logger.info(f"Google Calendar callback received - code: {'present' if code else 'missing'}, state: {'present' if state else 'missing'}, error: {error}")
        
        if error:
            logger.error(f"Google Calendar OAuth error: {error}")
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return redirect(f"{frontend_url}/cus/calendar/settings?error={error}")
        
        if not code or not state:
            logger.error(f"Missing code or state - code: {bool(code)}, state: {bool(state)}")
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return redirect(f"{frontend_url}/cus/calendar/settings?error=missing_code_or_state")
        
        # Get user_id from cache (primary method)
        from django.core.cache import cache
        cache_key = f"google_oauth_state_{state}"
        user_id = cache.get(cache_key)
        
        logger.info(f"Retrieved user_id from cache: {user_id}")
        
        # Fallback to session if cache miss
        if not user_id:
            session_state = request.session.get('google_oauth_state')
            user_id = request.session.get('google_oauth_user_id')
            
            logger.info(f"Fallback to session - session_state: {'present' if session_state else 'missing'}, user_id: {user_id}")
            
            if not user_id or (state and session_state and session_state != state):
                logger.warning(f"Could not extract user_id from cache or session - state: {state}, session_state: {session_state}")
                frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
                return redirect(f"{frontend_url}/cus/calendar/settings?error=session_expired")
        
        if not user_id:
            logger.error("No user_id found after all attempts")
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return redirect(f"{frontend_url}/cus/calendar/settings?error=user_not_found")
        
        # Get user and ensure profile exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        profile, _ = Profile.objects.get_or_create(user=user)
        
        # Exchange code for tokens
        # Use calendar-specific credentials (separate from login OAuth)
        client_id = getattr(settings, 'GOOGLE_CALENDAR_CLIENT_ID', None)
        client_secret = getattr(settings, 'GOOGLE_CALENDAR_CLIENT_SECRET', None)
        
        # Fallback to general Google OAuth credentials if calendar-specific not set
        if not client_id:
            client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
        if not client_secret:
            client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
        
        if not client_id or not client_secret:
            logger.error(f"Missing OAuth credentials - client_id: {bool(client_id)}, client_secret: {bool(client_secret)}")
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return redirect(f"{frontend_url}/cus/calendar/settings?error=missing_credentials")
        
        # Use redirect_uri from settings (same as login callback approach)
        # This MUST match exactly what's registered in Google Cloud Console
        redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/calendar/google/callback/')
        
        # Get actual callback URL for logging/comparison
        actual_callback_url = request.build_absolute_uri().split('?')[0]  # Remove query params
        
        logger.info(f"Using redirect_uri from settings: {redirect_uri}")
        logger.info(f"Actual callback URL from request: {actual_callback_url}")
        logger.info(f"Client ID: {client_id[:30]}...")
        logger.info(f"Code length: {len(code) if code else 0}, State: {state[:50] if state else 'None'}...")
        
        # Verify they match (normalize for comparison - remove trailing slashes)
        if redirect_uri.rstrip('/') != actual_callback_url.rstrip('/'):
            logger.warning(f"Redirect URI mismatch! Settings: {redirect_uri}, Actual: {actual_callback_url}")
            logger.warning("This might cause token exchange to fail. Ensure Google Cloud Console has the correct redirect URI.")
        
        # Create flow with redirect_uri from settings (same as login callback)
        flow = Flow.from_client_config(
            {
                'web': {
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'redirect_uris': [redirect_uri]
                }
            },
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri=redirect_uri
        )
        
        try:
            # Match the login callback approach - just pass code, Flow uses the redirect_uri from config
            logger.info(f"Calling fetch_token with code, redirect_uri: {redirect_uri}")
            logger.info(f"Flow redirect_uri: {flow.redirect_uri}")
            logger.info(f"Flow client_id: {flow.client_config.get('web', {}).get('client_id', 'N/A')[:30]}...")
            
            flow.fetch_token(code=code)
            
        except Exception as token_error:
            error_type = type(token_error).__name__
            error_msg = str(token_error)
            error_module = type(token_error).__module__
            
            logger.error(f"Token exchange failed - Type: {error_type}, Module: {error_module}, Message: {error_msg}", exc_info=True)
            
            # Log all available error attributes
            error_attrs = dir(token_error)
            logger.error(f"Error attributes: {[attr for attr in error_attrs if not attr.startswith('_')]}")
            
            # Try to extract OAuth error details
            oauth_error = None
            oauth_error_description = None
            
            if hasattr(token_error, 'error'):
                oauth_error = token_error.error
                logger.error(f"OAuth error: {oauth_error}")
            if hasattr(token_error, 'error_description'):
                oauth_error_description = token_error.error_description
                logger.error(f"OAuth error_description: {oauth_error_description}")
            if hasattr(token_error, 'status_code'):
                logger.error(f"HTTP status code: {token_error.status_code}")
            if hasattr(token_error, 'response'):
                try:
                    logger.error(f"Response content: {token_error.response}")
                except:
                    pass
            
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            
            # Provide more specific error messages based on OAuth error code
            error_lower = error_msg.lower()
            if oauth_error:
                oauth_error_lower = str(oauth_error).lower()
                if 'redirect_uri_mismatch' in oauth_error_lower or 'redirect_uri' in oauth_error_lower:
                    logger.error(f"REDIRECT URI MISMATCH - Expected: {redirect_uri}, Actual callback: {actual_callback_url}")
                    return redirect(f"{frontend_url}/cus/calendar/settings?error=redirect_uri_mismatch")
                elif 'invalid_grant' in oauth_error_lower:
                    return redirect(f"{frontend_url}/cus/calendar/settings?error=invalid_grant")
                elif 'invalid_client' in oauth_error_lower:
                    return redirect(f"{frontend_url}/cus/calendar/settings?error=invalid_client")
            
            if 'redirect_uri_mismatch' in error_lower or 'redirect_uri' in error_lower:
                logger.error(f"REDIRECT URI MISMATCH (from message) - Expected: {redirect_uri}, Actual callback: {actual_callback_url}")
                return redirect(f"{frontend_url}/cus/calendar/settings?error=redirect_uri_mismatch")
            elif 'invalid_grant' in error_lower:
                return redirect(f"{frontend_url}/cus/calendar/settings?error=invalid_grant")
            elif 'invalid_client' in error_lower:
                return redirect(f"{frontend_url}/cus/calendar/settings?error=invalid_client")
            else:
                # Include error details in URL for debugging
                error_detail = oauth_error if oauth_error else error_type
                return redirect(f"{frontend_url}/cus/calendar/settings?error=token_exchange_failed&type={error_type}&detail={error_detail}")
        
        # Store tokens in profile
        credentials = flow.credentials
        if not credentials.token:
            logger.error("No access token received from Google")
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return redirect(f"{frontend_url}/cus/calendar/settings?error=no_token_received")
        
        logger.info(f"Successfully obtained tokens for user_id: {user_id}")
        profile.calendar_sync_enabled = True
        profile.calendar_provider = 'google'
        profile.calendar_access_token = credentials.token
        profile.calendar_refresh_token = credentials.refresh_token
        profile.calendar_calendar_id = 'primary'  # Default to primary calendar
        profile.save()
        logger.info(f"Calendar sync enabled for user_id: {user_id}")
        
        # Clear cache and session
        from django.core.cache import cache
        cache_key = f"google_oauth_state_{state}"
        cache.delete(cache_key)
        
        if 'google_oauth_state' in request.session:
            request.session.pop('google_oauth_state', None)
        if 'google_oauth_user_id' in request.session:
            request.session.pop('google_oauth_user_id', None)
        
        # Redirect to frontend success page (role-agnostic - frontend will route correctly)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        # Try to determine role and redirect to appropriate settings page
        try:
            if user.role == 'customer':
                return redirect(f"{frontend_url}/cus/calendar/settings?connected=google")
            elif user.role == 'staff':
                return redirect(f"{frontend_url}/st/calendar/settings?connected=google")
            elif user.role == 'admin' or user.role == 'manager':
                return redirect(f"{frontend_url}/settings/calendar?connected=google")
        except:
            pass
        # Fallback
        return redirect(f"{frontend_url}/cus/calendar/settings?connected=google")
        
    except Exception as e:
        logger.error(f"Error in Google Calendar OAuth callback: {e}", exc_info=True)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        error_msg = str(e)
        # Try to redirect to appropriate settings page based on user role if available
        try:
            user_id = None
            state = request.GET.get('state', '')
            
            # Try cache first
            if state:
                from django.core.cache import cache
                cache_key = f"google_oauth_state_{state}"
                user_id = cache.get(cache_key)
            
            # Fallback to session
            if not user_id:
                user_id = request.session.get('google_oauth_user_id')
            
            if user_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(id=user_id)
                    if user.role == 'customer':
                        return redirect(f"{frontend_url}/cus/calendar/settings?error=google_oauth_error")
                    elif user.role == 'staff':
                        return redirect(f"{frontend_url}/st/calendar/settings?error=google_oauth_error")
                except:
                    pass
        except:
            pass
        return redirect(f"{frontend_url}/cus/calendar/settings?error=google_oauth_error")


class GoogleCalendarDisconnectView(APIView):
    """Disconnect Google Calendar integration."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Disconnect Google Calendar."""
        try:
            profile, _ = Profile.objects.get_or_create(user=request.user)
            
            # Revoke token if available
            if profile.calendar_access_token and GOOGLE_CALENDAR_AVAILABLE:
                try:
                    credentials = Credentials(token=profile.calendar_access_token)
                    credentials.revoke(Request())
                except:
                    pass  # Ignore revocation errors
            
            # Clear calendar sync settings
            profile.calendar_sync_enabled = False
            profile.calendar_provider = 'none'
            profile.calendar_access_token = None
            profile.calendar_refresh_token = None
            profile.calendar_calendar_id = None
            profile.save()
            
            return Response({
                'success': True,
                'message': 'Google Calendar disconnected successfully'
            })
            
        except Exception as e:
            logger.error(f"Error disconnecting Google Calendar: {e}")
            return Response({
                'success': False,
                'error': {
                    'code': 'DISCONNECT_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OutlookConnectView(APIView):
    """Initiate Microsoft Outlook OAuth 2.0 authorization flow."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Start Microsoft Outlook OAuth flow."""
        if not OUTLOOK_AVAILABLE:
            return Response({
                'success': False,
                'error': {
                    'code': 'LIBRARY_NOT_INSTALLED',
                    'message': 'Microsoft Graph API libraries not installed. Install with: pip install msal msgraph-sdk'
                }
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            # Microsoft Graph OAuth 2.0 configuration
            client_id = getattr(settings, 'OUTLOOK_CLIENT_ID', None)
            client_secret = getattr(settings, 'OUTLOOK_CLIENT_SECRET', None)
            redirect_uri = getattr(settings, 'OUTLOOK_REDIRECT_URI', 'http://localhost:8000/api/calendar/outlook/callback/')
            authority = 'https://login.microsoftonline.com/common'
            
            if not client_id or not client_secret:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'MISSING_CONFIG',
                        'message': 'Microsoft OAuth credentials not configured. Set OUTLOOK_CLIENT_ID and OUTLOOK_CLIENT_SECRET in settings.'
                    }
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Create MSAL app
            app = ConfidentialClientApplication(
                client_id=client_id,
                client_credential=client_secret,
                authority=authority
            )
            
            # Get authorization URL
            scopes = ['https://graph.microsoft.com/Calendars.ReadWrite']
            authorization_url = app.get_authorization_request_url(
                scopes=scopes,
                redirect_uri=redirect_uri
            )
            
            # Store user ID in session
            request.session['outlook_oauth_user_id'] = request.user.id
            
            return Response({
                'success': True,
                'data': {
                    'authorization_url': authorization_url
                }
            })
            
        except Exception as e:
            logger.error(f"Error initiating Outlook OAuth: {e}")
            return Response({
                'success': False,
                'error': {
                    'code': 'OAUTH_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def outlook_calendar_callback(request):
    """Handle Microsoft Outlook OAuth callback."""
    if not OUTLOOK_AVAILABLE:
        return Response({
            'success': False,
            'error': {
                'code': 'LIBRARY_NOT_INSTALLED',
                'message': 'Microsoft Graph API libraries not installed.'
            }
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        # Get authorization code from callback
        code = request.GET.get('code')
        error = request.GET.get('error')
        
        if error:
            logger.error(f"Outlook OAuth error: {error}")
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return redirect(f"{frontend_url}/settings/calendar?error=outlook_oauth_error")
        
        if not code:
            return Response({
                'success': False,
                'error': {
                    'code': 'MISSING_CODE',
                    'message': 'Authorization code not provided'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = request.session.get('outlook_oauth_user_id')
        if not user_id:
            return Response({
                'success': False,
                'error': {
                    'code': 'SESSION_EXPIRED',
                    'message': 'OAuth session expired. Please try again.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user and ensure profile exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        profile, _ = Profile.objects.get_or_create(user=user)
        
        # Exchange code for tokens
        client_id = getattr(settings, 'OUTLOOK_CLIENT_ID', None)
        client_secret = getattr(settings, 'OUTLOOK_CLIENT_SECRET', None)
        redirect_uri = getattr(settings, 'OUTLOOK_REDIRECT_URI', 'http://localhost:8000/api/calendar/outlook/callback/')
        authority = 'https://login.microsoftonline.com/common'
        
        app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority
        )
        
        scopes = ['https://graph.microsoft.com/Calendars.ReadWrite']
        result = app.acquire_token_by_authorization_code(
            code=code,
            scopes=scopes,
            redirect_uri=redirect_uri
        )
        
        if 'error' in result:
            logger.error(f"Outlook token acquisition error: {result['error']}")
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return redirect(f"{frontend_url}/settings/calendar?error=outlook_token_error")
        
        # Store tokens in profile
        profile.calendar_sync_enabled = True
        profile.calendar_provider = 'outlook'
        profile.calendar_access_token = result.get('access_token')
        profile.calendar_refresh_token = result.get('refresh_token')
        profile.calendar_calendar_id = 'calendar'  # Default calendar ID
        profile.save()
        
        # Clear session
        request.session.pop('outlook_oauth_user_id', None)
        
        # Redirect to frontend success page
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/settings/calendar?connected=outlook")
        
    except Exception as e:
        logger.error(f"Error in Outlook OAuth callback: {e}")
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/settings/calendar?error=outlook_oauth_error")


class OutlookDisconnectView(APIView):
    """Disconnect Microsoft Outlook integration."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Disconnect Microsoft Outlook."""
        try:
            profile, _ = Profile.objects.get_or_create(user=request.user)
            
            # Clear calendar sync settings
            profile.calendar_sync_enabled = False
            profile.calendar_provider = 'none'
            profile.calendar_access_token = None
            profile.calendar_refresh_token = None
            profile.calendar_calendar_id = None
            profile.save()
            
            return Response({
                'success': True,
                'message': 'Microsoft Outlook disconnected successfully'
            })
            
        except Exception as e:
            logger.error(f"Error disconnecting Outlook: {e}")
            return Response({
                'success': False,
                'error': {
                    'code': 'DISCONNECT_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ManualSyncView(APIView):
    """Trigger manual sync of appointments to connected calendar. All roles."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.calendar_sync.services import sync_user_appointments_to_calendar
        synced_count, error_message = sync_user_appointments_to_calendar(request.user)
        if error_message and synced_count == 0:
            return Response({
                'success': False,
                'error': {'code': 'SYNC_FAILED', 'message': error_message},
            }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'success': True,
            'data': {
                'synced_count': synced_count,
                'message': f'Synced {synced_count} appointment(s) to your calendar.',
                'last_error': error_message,
            },
        }, status=status.HTTP_200_OK)


class BulkSyncView(APIView):
    """Bulk sync appointments for multiple users (admin only)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from django.contrib.auth import get_user_model
        from apps.calendar_sync.services import sync_user_appointments_to_calendar

        if not (getattr(request.user, 'role', None) == 'admin' or request.user.is_superuser):
            return Response({
                'success': False,
                'error': {'code': 'PERMISSION_DENIED', 'message': 'Admin only.'},
            }, status=status.HTTP_403_FORBIDDEN)
        user_ids = request.data.get('user_ids') or []
        User = get_user_model()
        results = []
        for uid in user_ids:
            try:
                user = User.objects.get(id=uid)
                synced_count, err = sync_user_appointments_to_calendar(user)
                results.append({'user_id': uid, 'synced_count': synced_count, 'error': err})
            except User.DoesNotExist:
                results.append({'user_id': uid, 'synced_count': 0, 'error': 'User not found'})
            except Exception as e:
                results.append({'user_id': uid, 'synced_count': 0, 'error': str(e)})
        return Response({
            'success': True,
            'data': {'results': results},
        }, status=status.HTTP_200_OK)


class CustomEventCreateView(APIView):
    """Create a custom calendar event or list synced appointments. All roles."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List appointments synced to calendar for current user (event management)."""
        from apps.appointments.models import Appointment
        from apps.staff.models import Staff
        from apps.orders.models import Order
        from apps.customers.models import Customer

        user = request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        if not profile.calendar_sync_enabled or not profile.calendar_provider or profile.calendar_provider == 'none':
            return Response({'success': True, 'data': {'events': []}}, status=status.HTTP_200_OK)

        now = timezone.now()
        events = []
        if user.role == 'staff':
            try:
                staff = Staff.objects.get(user=user)
                qs = Appointment.objects.filter(
                    staff=staff, start_time__gte=now,
                    status__in=['pending', 'confirmed'],
                ).filter(calendar_synced_to__contains=[profile.calendar_provider]).order_by('start_time')[:50]
            except Staff.DoesNotExist:
                qs = []
        elif user.role == 'customer':
            try:
                customer = Customer.objects.get(user=user)
                order_ids = Order.objects.filter(customer=customer).values_list('id', flat=True)
                qs = Appointment.objects.filter(
                    order_id__in=order_ids, start_time__gte=now,
                    status__in=['pending', 'confirmed'],
                ).filter(calendar_synced_to__contains=[profile.calendar_provider]).order_by('start_time')[:50]
            except Customer.DoesNotExist:
                qs = []
        else:
            qs = []
        for apt in qs:
            events.append({
                'id': apt.id,
                'start': apt.start_time.isoformat(),
                'end': apt.end_time.isoformat(),
                'summary': getattr(apt.service, 'name', 'Appointment') if apt.service_id else 'Appointment',
                'synced_to': apt.calendar_synced_to or [],
            })
        return Response({'success': True, 'data': {'events': events}}, status=status.HTTP_200_OK)

    def post(self, request):
        from apps.calendar_sync.services import CalendarSyncService
        summary = request.data.get('title') or request.data.get('summary') or 'Event'
        start_str = request.data.get('start')
        end_str = request.data.get('end')
        if not start_str or not end_str:
            return Response({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': 'start and end (ISO datetime) are required.'},
            }, status=status.HTTP_400_BAD_REQUEST)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not profile.calendar_sync_enabled or profile.calendar_provider in ('none', None, ''):
            return Response({
                'success': False,
                'error': {'code': 'CALENDAR_NOT_CONNECTED', 'message': 'Connect a calendar first.'},
            }, status=status.HTTP_400_BAD_REQUEST)
        event_data = {
            'summary': summary,
            'start': start_str,
            'end': end_str,
            'description': request.data.get('description') or '',
            'location': request.data.get('location') or '',
        }
        event_id = CalendarSyncService.create_custom_event(profile, event_data)
        if not event_id:
            return Response({
                'success': False,
                'error': {'code': 'CREATE_FAILED', 'message': 'Failed to create calendar event.'},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({
            'success': True,
            'data': {'event_id': event_id, 'message': 'Event created.'},
        }, status=status.HTTP_201_CREATED)


class CalendarStatusView(APIView):
    """Get calendar sync status for a user."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get calendar sync status for current user or specified user_id (admin only)."""
        try:
            # Allow admin to check status for other users (for staff management)
            user_id = request.query_params.get('user_id')
            if user_id and request.user.role in ['admin', 'manager']:
                from apps.accounts.models import User
                try:
                    target_user = User.objects.get(id=user_id)
                    profile, _ = Profile.objects.get_or_create(user=target_user)
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'USER_NOT_FOUND',
                            'message': 'User not found'
                        }
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                profile, _ = Profile.objects.get_or_create(user=request.user)
            
            settings_json = profile.calendar_sync_settings or {}
            return Response({
                'success': True,
                'data': {
                    'calendar_sync_enabled': profile.calendar_sync_enabled,
                    'calendar_provider': profile.calendar_provider,
                    'calendar_calendar_id': profile.calendar_calendar_id,
                    'has_access_token': bool(profile.calendar_access_token),
                    'has_refresh_token': bool(profile.calendar_refresh_token),
                    'last_sync_at': settings_json.get('last_sync_at'),
                    'last_sync_error': settings_json.get('last_sync_error'),
                }
            })
        except Profile.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'PROFILE_NOT_FOUND',
                    'message': 'User profile not found'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting calendar status: {e}")
            return Response({
                'success': False,
                'error': {
                    'code': 'STATUS_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ICalendarDownloadView(APIView):
    """Download .ics file for an appointment."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, appointment_id):
        """Generate and download .ics file for appointment."""
        try:
            appointment = Appointment.objects.select_related(
                'service', 'staff', 'order', 'subscription'
            ).select_related('customer_booking__customer').get(id=appointment_id)
            
            # Check if user has access to this appointment
            # Customer can download their own appointments
            # Staff can download appointments assigned to them
            # Managers and admins can download any appointment
            has_access = False
            
            if request.user.role == 'customer':
                # Check if appointment is linked to customer's orders
                if appointment.order and appointment.order.customer and appointment.order.customer.user == request.user:
                    has_access = True
            elif request.user.role == 'staff':
                # Check if appointment is assigned to staff member
                if appointment.staff and appointment.staff.user == request.user:
                    has_access = True
            elif request.user.role in ['manager', 'admin']:
                has_access = True
            
            if not has_access:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'PERMISSION_DENIED',
                        'message': 'You do not have permission to access this appointment'
                    }
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Build event data for .ics generation
            from apps.calendar_sync.services import AppleCalendarService
            
            order = appointment.order
            
            # Build event data based on user role (staff can have no order e.g. subscription)
            if request.user.role == 'customer':
                if not order:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'NO_ORDER',
                            'message': 'Appointment is not linked to an order'
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
                from apps.calendar_sync.services import build_customer_event_data
                event_data = build_customer_event_data(order, appointment)
            elif request.user.role == 'staff':
                if order:
                    from apps.calendar_sync.services import build_staff_event_data
                    event_data = build_staff_event_data(order, appointment)
                else:
                    from apps.calendar_sync.services import build_staff_event_data_from_appointment
                    event_data = build_staff_event_data_from_appointment(appointment)
            else:
                # Admin/Manager: use staff event data if no order, otherwise manager event data
                if not order:
                    # For appointments without orders (subscriptions), use staff event data
                    from apps.calendar_sync.services import build_staff_event_data_from_appointment
                    event_data = build_staff_event_data_from_appointment(appointment)
                else:
                    from apps.calendar_sync.services import build_manager_event_data
                    event_data = build_manager_event_data(order, appointment)
            
            # Generate .ics content
            ics_content = AppleCalendarService._generate_ics_content(event_data)
            
            # Return as file download
            from django.http import HttpResponse
            
            response = HttpResponse(ics_content, content_type='text/calendar')
            response['Content-Disposition'] = f'attachment; filename="appointment-{appointment_id}.ics"'
            return response
            
        except Appointment.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Appointment not found'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error generating .ics file: {e}")
            return Response({
                'success': False,
                'error': {
                    'code': 'ICS_GENERATION_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
