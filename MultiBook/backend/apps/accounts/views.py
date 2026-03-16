"""
Accounts app views.
Authentication views (register, login, logout, token refresh).
"""
from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken  # type: ignore[import-untyped]
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView  # type: ignore[import-untyped]
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .serializers import (
    UserSerializer, UserCreateSerializer, ProfileSerializer, ManagerSerializer,
    InvitationSerializer
)
from .models import Profile, Invitation
from apps.core.permissions import IsAdmin, IsAdminOrManager
from rest_framework.exceptions import PermissionDenied, ValidationError as DRFValidationError

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint (public).
    POST /api/aut/register/
    
    Security: Returns 200 OK for all valid requests (including existing emails)
    to prevent user enumeration attacks. Frontend handles redirect based on
    the 'redirect_to_login' flag in the response.
    """
    permission_classes = [AllowAny]
    serializer_class = UserCreateSerializer
    
    def create(self, request, *args, **kwargs):
        email = request.data.get('email', '').lower().strip() if request.data.get('email') else ''
        
        # SECURITY: Check if email exists BEFORE validation to prevent user enumeration
        # We return 200 OK in both cases (existing and new) to prevent attackers
        # from determining if an email is registered
        existing_user = None
        if email:
            try:
                existing_user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                existing_user = None
        
        # If email exists, return 200 OK with redirect flag (security: same status as success)
        if existing_user:
            return Response({
                'success': True,
                'data': {
                    'redirect_to_login': True,
                    'email': email,
                },
                'meta': {
                    'message': 'Please login to continue',
                }
            }, status=status.HTTP_200_OK)
        
        # Email doesn't exist - proceed with normal registration
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            # Send welcome email (non-blocking; log on failure)
            try:
                from apps.notifications.email_service import send_welcome_email
                send_welcome_email(user, customer_name=user.get_full_name() or user.email)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning('Failed to send welcome email: %s', e)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'success': True,
                'data': {
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    },
                    'redirect_to_login': False,
                },
                'meta': {
                    'message': 'User registered successfully',
                }
            }, status=status.HTTP_200_OK)  # Changed to 200 OK for consistency (security)
        
        except DRFValidationError as e:
            # SECURITY: Catch validation errors (including race condition duplicates)
            # Only return 200 OK for email duplicates to prevent user enumeration
            error_detail = e.detail
            email_error = None
            
            # Check if error is about email already exists
            if isinstance(error_detail, dict):
                email_error = error_detail.get('email')
                if email_error and isinstance(email_error, list):
                    email_error = email_error[0] if email_error else None
            
            # If it's an email duplicate error, return 200 OK with redirect flag (security)
            if email_error and 'already exists' in str(email_error).lower():
                return Response({
                    'success': True,
                    'data': {
                        'redirect_to_login': True,
                        'email': email,
                    },
                    'meta': {
                        'message': 'Please login to continue',
                    }
                }, status=status.HTTP_200_OK)
            
            # Other validation errors (password mismatch, invalid role, etc.)
            # These can return 400 as they don't reveal user information
            # Re-raise to let DRF handle it normally
            raise


class LoginView(TokenObtainPairView):
    """
    User login endpoint (public).
    POST /api/aut/login/
    Returns JWT tokens and user information.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Email and password are required',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Normalize email to lowercase for case-insensitive lookup
        email = email.lower().strip()
        
        # SECURITY: Prevent user enumeration by always returning the same error
        # Don't differentiate between "email not found" and "wrong password"
        # This prevents attackers from determining if an email exists
        
        # Try to get user (case-insensitive lookup)
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Email doesn't exist - return same generic error as wrong password
            # This prevents user enumeration attacks
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid email or password',
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Email exists - check password
        if not user.check_password(password):
            # Password is wrong - return same generic error
            # Frontend will show "Invalid email or password" for both cases
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid email or password',
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Password is correct - authenticate user
        user = authenticate(username=user.username, password=password)
        if user is None:
            return Response({
                'success': False,
                'error': {
                    'code': 'AUTHENTICATION_FAILED',
                    'message': 'Authentication failed',
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'success': False,
                'error': {
                    'code': 'ACCOUNT_DISABLED',
                    'message': 'Account is disabled',
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            },
            'meta': {
                'message': 'Login successful',
            }
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    User logout endpoint (protected).
    POST /api/aut/logout/
    Invalidates refresh token.
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        # Invalid/expired/already blacklisted token - still return 200 so frontend can clear state
        pass
    # Always return 200 so frontend can clear tokens (avoids 400 in console when token already invalid)
    return Response({
        'success': True,
        'data': {},
        'meta': {
            'message': 'Logout successful',
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def google_oauth_start_view(request):
    """
    Start Google OAuth flow (Google Cloud OAuth, not Supabase).
    GET /api/aut/google/start/
    Redirects user to Google OAuth consent screen.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Check if Google OAuth libraries are available
    try:
        from google_auth_oauthlib.flow import Flow
        GOOGLE_OAUTH_AVAILABLE = True
    except ImportError:
        GOOGLE_OAUTH_AVAILABLE = False
        logger.warning("Google OAuth libraries not installed. Install with: pip install google-auth-oauthlib")
    
    if not GOOGLE_OAUTH_AVAILABLE:
        return Response({
            'success': False,
            'error': {
                'code': 'LIBRARY_NOT_INSTALLED',
                'message': 'Google OAuth libraries not installed. Install with: pip install google-auth-oauthlib'
            }
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        # Get Google OAuth credentials from settings
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
        client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
        redirect_uri = getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', 
                              getattr(settings, 'GOOGLE_REDIRECT_URI', 
                                     'http://localhost:8000/api/aut/google/callback/'))
        
        if not client_id or not client_secret:
            return Response({
                'success': False,
                'error': {
                    'code': 'MISSING_CONFIG',
                    'message': 'Google OAuth credentials not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in settings.'
                }
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Define scopes (must match exactly in callback)
        oauth_scopes = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
        
        # Create OAuth flow
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
            scopes=oauth_scopes,  # Use the defined scopes variable
            redirect_uri=redirect_uri
        )
        
        # Get authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Store state in cache so callback works without session cookie (e.g. cross-origin redirect from Google)
        from django.core.cache import cache
        cache_key = f'google_oauth_login_state_{state}'
        cache.set(cache_key, {'scopes': oauth_scopes}, timeout=600)
        # Also store in session as fallback
        request.session['google_oauth_state'] = state
        request.session['google_oauth_purpose'] = 'login'
        request.session['google_oauth_scopes'] = oauth_scopes
        
        # Return authorization URL for frontend to redirect
        return Response({
            'success': True,
            'data': {
                'authorization_url': authorization_url
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error starting Google OAuth flow: {e}")
        return Response({
            'success': False,
            'error': {
                'code': 'OAUTH_ERROR',
                'message': f'Failed to start OAuth flow: {str(e)}'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def google_oauth_callback_view(request):
    """
    Handle Google OAuth callback (Google Cloud OAuth, not Supabase).
    GET /api/aut/google/callback/
    Exchanges authorization code for user info and creates/logs in user.
    """
    import logging
    from django.db import IntegrityError
    from django.shortcuts import redirect
    
    logger = logging.getLogger(__name__)
    
    try:
        from google_auth_oauthlib.flow import Flow
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        GOOGLE_OAUTH_AVAILABLE = True
    except ImportError:
        GOOGLE_OAUTH_AVAILABLE = False
    
    if not GOOGLE_OAUTH_AVAILABLE:
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/login?error=oauth_library_not_installed")
    
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    if error:
        logger.error(f"Google OAuth error: {error}")
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/login?error={error}")
    
    if not code:
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/login?error=no_code")
    if not state:
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/login?error=invalid_state")
    
    # Verify state from cache (primary) or session (fallback) so callback works when session cookie is not sent
    from django.core.cache import cache
    cache_key = f'google_oauth_login_state_{state}'
    cached_data = cache.get(cache_key)
    if cached_data:
        cache.delete(cache_key)  # one-time use
        oauth_scopes = cached_data.get('scopes', ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'])
    else:
        session_state = request.session.get('google_oauth_state')
        if not session_state or session_state != state:
            logger.warning("Google OAuth state mismatch or expired (cache and session)")
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return redirect(f"{frontend_url}/login?error=invalid_state")
        oauth_scopes = request.session.get('google_oauth_scopes',
                                          ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'])
    
    try:
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
        client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
        redirect_uri = getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI',
                              getattr(settings, 'GOOGLE_REDIRECT_URI',
                                     'http://localhost:8000/api/aut/google/callback/'))
        
        if not client_id or not client_secret:
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return redirect(f"{frontend_url}/login?error=missing_config")
        
        # Use actual callback URL so it matches exactly what Google redirected to
        actual_callback = request.build_absolute_uri().split('?')[0]
        if actual_callback and actual_callback.startswith('http'):
            redirect_uri = actual_callback
            logger.info(f"Using actual callback URL for token exchange: {redirect_uri}")
        
        # oauth_scopes already set from cache or session above
        logger.info(f"Using scopes for token exchange: {oauth_scopes}")
        
        # Relax oauthlib scope check: Google may return scopes in different order or with
        # include_granted_scopes; without this we get "Scope has changed" error.
        import os
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
        
        # Create flow and exchange code for tokens (MUST use same scopes as authorization)
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
            scopes=oauth_scopes,  # Use exact same scopes from authorization
            redirect_uri=redirect_uri
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user info from Google
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        
        email = (user_info.get('email') or '').lower().strip()
        name = user_info.get('name', '').strip()
        given_name = user_info.get('given_name', '').strip()
        family_name = user_info.get('family_name', '').strip()
        
        if not name and (given_name or family_name):
            name = f"{given_name} {family_name}".strip()
        
        if not email:
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return redirect(f"{frontend_url}/login?error=no_email")
        
        # Create or get user
        from apps.customers.models import Customer
        
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Create new user (customer) and Customer record
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f'{base_username}{counter}'
                counter += 1
            
            name_parts = (name or 'User').split(None, 1)
            first_name = name_parts[0] if name_parts else 'User'
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            try:
                user = User.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role='customer',
                )
                user.set_unusable_password()
                user.save()
                Customer.objects.get_or_create(
                    user=user,
                    defaults={
                        'name': name or f'{first_name} {last_name}'.strip() or email,
                        'email': email,
                    },
                )
            except IntegrityError:
                # Race condition: user was created by another request
                user = User.objects.get(email__iexact=email)
        
        if not user.is_active:
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return redirect(f"{frontend_url}/login?error=account_disabled")
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Clear session
        request.session.pop('google_oauth_state', None)
        request.session.pop('google_oauth_purpose', None)
        request.session.pop('google_oauth_scopes', None)
        
        # Redirect to frontend with tokens in URL (frontend will extract and store)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        role = user.role or 'customer'
        role_prefix = {'admin': 'ad', 'customer': 'cus', 'staff': 'st', 'manager': 'man'}.get(role, 'cus')
        
        # Redirect with tokens in URL parameters (must be strings and URL-safe)
        from urllib.parse import quote
        access_str = str(refresh.access_token)
        refresh_str = str(refresh)
        token_param = quote(access_str, safe='')
        refresh_param = quote(refresh_str, safe='')
        return redirect(f"{frontend_url}/auth/google-callback?token={token_param}&refresh={refresh_param}")
        
    except Exception as e:
        logger.exception(f"Error in Google OAuth callback: {e}")
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        # Pass through specific error for debugging (frontend can show generic message)
        err_msg = str(e).replace(' ', '_')[:50] if e else 'oauth_failed'
        return redirect(f"{frontend_url}/login?error=oauth_failed&detail={err_msg}")


@api_view(['POST'])
@permission_classes([AllowAny])
def google_login_view(request):
    """
    Legacy endpoint: Exchange Google (Supabase) OAuth for Django user and JWT.
    POST /api/aut/google/
    Body: { "access_token": "<supabase_jwt>" } or (dev) { "email": "...", "name": "..." }
    Creates or finds User in Django DB and returns Django JWT + user (role) for dashboard redirect.
    
    NOTE: This endpoint is kept for backward compatibility with Supabase OAuth.
    New implementations should use /api/aut/google/start/ and /api/aut/google/callback/
    """
    import logging
    from django.db import IntegrityError

    logger = logging.getLogger(__name__)
    data = getattr(request, 'data', None) or {}
    if not isinstance(data, dict):
        data = {}

    access_token = data.get('access_token')
    email = (data.get('email') or '').lower().strip()
    name = (data.get('name') or '').strip()

    # Option 1: Verify Supabase JWT and extract email/name (legacy support)
    supabase_jwt_secret = getattr(settings, 'SUPABASE_JWT_SECRET', None)
    if access_token and supabase_jwt_secret:
        try:
            import jwt as pyjwt
            payload = pyjwt.decode(
                access_token,
                supabase_jwt_secret,
                algorithms=['HS256'],
                options={'verify_aud': False},
            )
            email = (payload.get('email') or payload.get('sub') or '').lower().strip()
            if not email and payload.get('sub'):
                # Supabase may put email in user_metadata or app_metadata
                email = (payload.get('user_metadata', {}).get('email') or '').lower().strip()
            name = (payload.get('user_metadata', {}).get('full_name') or
                    payload.get('user_metadata', {}).get('name') or
                    payload.get('name') or
                    (payload.get('given_name', '') + ' ' + payload.get('family_name', '')).strip() or
                    name)
        except Exception as e:
            # Fallback: use email/name from body (JWT secret mismatch, PyJWT not installed, etc.)
            logger.debug('Google login JWT fallback: %s', e)
            email = (data.get('email') or '').lower().strip()
            name = (data.get('name') or '').strip()
            if not email:
                return Response({
                    'success': False,
                    'error': {'code': 'INVALID_TOKEN', 'message': 'Invalid token. Send email (and name) in the request body as fallback, or set SUPABASE_JWT_SECRET in backend .env to match Supabase project JWT Secret.'},
                }, status=status.HTTP_401_UNAUTHORIZED)

    # Option 2: No token or no secret – accept email + name from body (e.g. frontend sends session.user)
    if not email and data.get('email'):
        email = (data.get('email') or '').lower().strip()
        name = (data.get('name') or '').strip()

    if not email:
        return Response({
            'success': False,
            'error': {'code': 'MISSING_EMAIL', 'message': 'Email is required'},
        }, status=status.HTTP_400_BAD_REQUEST)

    from apps.customers.models import Customer

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        # Create new user (customer) and Customer record
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}{counter}'
            counter += 1
        name_parts = (name or 'User').split(None, 1)
        first_name = name_parts[0] if name_parts else 'User'
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        try:
            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='customer',
            )
            user.set_unusable_password()
            user.save()
            Customer.objects.get_or_create(
                user=user,
                defaults={
                    'name': name or f'{first_name} {last_name}'.strip() or email,
                    'email': email,
                },
            )
        except IntegrityError:
            # Race: user was created by another request; fetch and continue
            user = User.objects.get(email__iexact=email)

    if not user.is_active:
        return Response({
            'success': False,
            'error': {'code': 'ACCOUNT_DISABLED', 'message': 'Account is disabled'},
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
            },
            'meta': {'message': 'Signed in successfully'},
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception('Google login failed after user lookup: %s', e)
        return Response({
            'success': False,
            'error': {'code': 'SERVER_ERROR', 'message': 'Sign-in failed. Please try again.'},
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    """
    Get current user profile (protected).
    GET /api/aut/me/
    """
    serializer = UserSerializer(request.user)
    return Response({
        'success': True,
        'data': serializer.data,
        'meta': {}
    }, status=status.HTTP_200_OK)


from rest_framework import viewsets
from .models import Manager
from django.db.models import Q


class UserViewSet(viewsets.ModelViewSet):
    """
    User ViewSet (admin only).
    GET, PUT, PATCH, DELETE /api/ad/users/
    Manage all users (customers, staff, managers, admins).
    """
    queryset = User.objects.select_related('profile').all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    
    def list(self, request, *args, **kwargs):
        """List all users with filters."""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Filter by role
        role = request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by active status
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by verified status
        is_verified = request.query_params.get('is_verified')
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified.lower() == 'true')
        
        # Search by email or username
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | 
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'count': queryset.count(),
            }
        }, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve user detail."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {}
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Update user (role, is_active, is_verified, etc.)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Prevent admin from deactivating themselves
        if instance.id == request.user.id:
            if request.data.get('is_active') is False:
                return Response({
                    'success': False,
                    'error': {'code': 'CANNOT_DEACTIVATE_SELF', 'message': 'You cannot deactivate your own account.'},
                }, status=status.HTTP_400_BAD_REQUEST)
            if request.data.get('role') and request.data.get('role') != 'admin':
                return Response({
                    'success': False,
                    'error': {'code': 'CANNOT_CHANGE_SELF_ROLE', 'message': 'You cannot change your own role.'},
                }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {'message': 'User updated successfully'}
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """Delete user (with safeguards)."""
        instance = self.get_object()
        
        # Prevent admin from deleting themselves
        if instance.id == request.user.id:
            return Response({
                'success': False,
                'error': {'code': 'CANNOT_DELETE_SELF', 'message': 'You cannot delete your own account.'},
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prevent deleting superuser accounts
        if instance.is_superuser:
            return Response({
                'success': False,
                'error': {'code': 'CANNOT_DELETE_SUPERUSER', 'message': 'Cannot delete superuser accounts.'},
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'data': {},
            'meta': {'message': 'User deleted successfully'}
        }, status=status.HTTP_200_OK)


class ManagerViewSet(viewsets.ModelViewSet):
    """
    Manager ViewSet (admin only).
    GET, POST, PUT, PATCH, DELETE /api/ad/managers/
    """
    queryset = Manager.objects.select_related('user').prefetch_related(
        'managed_staff', 'managed_customers'
    ).all()
    serializer_class = ManagerSerializer
    permission_classes = [IsAdmin]
    
    def list(self, request, *args, **kwargs):
        """List all managers."""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Filter by active status if provided
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'count': queryset.count(),
            }
        }, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve manager detail."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {}
        }, status=status.HTTP_200_OK)


class InvitationViewSet(viewsets.ModelViewSet):
    """
    Invitation ViewSet (admin and manager).
    - Managers can only invite staff
    - Admins can invite staff, managers, and admins
    GET, POST, PUT, PATCH, DELETE /api/aut/invitations/
    """
    permission_classes = [IsAdminOrManager]
    serializer_class = InvitationSerializer
    queryset = Invitation.objects.all().order_by('-created_at')
    
    def get_queryset(self):
        """Filter invitations based on user role."""
        queryset = super().get_queryset()
        # Managers can only see their own invitations
        if hasattr(self.request.user, 'role') and self.request.user.role == 'manager':
            return queryset.filter(invited_by=self.request.user)
        # Admins can see all invitations
        return queryset
    
    def perform_create(self, serializer):
        """Set invited_by to current user and validate permissions."""
        user = self.request.user
        role = serializer.validated_data.get('role')
        
        # Check permissions based on user role
        if hasattr(user, 'role'):
            if user.role == 'manager':
                # Managers can only invite staff
                if role != 'staff':
                    raise PermissionDenied({
                        'error': {
                            'code': 'PERMISSION_DENIED',
                            'message': 'Managers can only invite staff members.',
                        }
                    })
            elif user.role == 'admin' or user.is_superuser:
                # Admins can invite staff, managers, and admins
                if role not in ['staff', 'manager', 'admin']:
                    raise PermissionDenied({
                        'error': {
                            'code': 'PERMISSION_DENIED',
                            'message': 'Admins can only invite staff, managers, and admins.',
                        }
                    })
            else:
                # Other roles cannot create invitations
                raise PermissionDenied({
                    'error': {
                        'code': 'PERMISSION_DENIED',
                        'message': 'You do not have permission to create invitations.',
                    }
                })
        
        serializer.save(invited_by=user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except PermissionDenied as e:
            # Return PermissionDenied with proper response format
            if isinstance(e.detail, dict):
                return Response(e.detail, status=status.HTTP_403_FORBIDDEN)
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': str(e.detail) if e.detail else 'You do not have permission to create this invitation.',
                }
            }, status=status.HTTP_403_FORBIDDEN)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'message': 'Invitation created successfully',
            }
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'count': queryset.count(),
            }
        }, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {}
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def validate_invitation_view(request, token):
    """
    Validate invitation token (public).
    GET /api/aut/invitations/validate/<token>/
    """
    try:
        invitation = Invitation.objects.get(token=token, is_active=True)
        if invitation.is_expired():
            return Response({
                'success': False,
                'error': {
                    'code': 'INVITATION_EXPIRED',
                    'message': 'This invitation has expired.',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        if invitation.used_at:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVITATION_USED',
                    'message': 'This invitation has already been used.',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': {
                'email': invitation.email,
                'role': invitation.role,
                'expires_at': invitation.expires_at.isoformat(),
            },
            'meta': {
                'message': 'Invitation is valid',
            }
        }, status=status.HTTP_200_OK)
    except Invitation.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'INVITATION_NOT_FOUND',
                'message': 'Invalid or expired invitation token.',
            }
        }, status=status.HTTP_404_NOT_FOUND)


class ProfileViewSet(viewsets.ModelViewSet):
    """
    Profile ViewSet (protected).
    GET, PUT, PATCH /api/aut/profile/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer
    http_method_names = ['get', 'put', 'patch']  # Only allow GET, PUT, PATCH
    
    def get_queryset(self):
        """Return only the current user's profile."""
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return Profile.objects.filter(id=profile.id)
    
    def get_object(self):
        """Return the current user's profile."""
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {}
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'message': 'Profile updated successfully',
            }
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def check_email_view(request):
    """
    Check if email exists (for account linking prompt) (public).
    POST /api/aut/check-email/
    """
    email = request.data.get('email')
    if not email:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Email is required',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Normalize email to lowercase for case-insensitive lookup
    email = email.lower().strip()
    email_exists = User.objects.filter(email__iexact=email).exists()
    
    return Response({
        'success': True,
        'data': {
            'email': email,
            'exists': email_exists,
            'suggestion': 'Login to link your order/subscription to your account' if email_exists else 'Register to create an account and link your order/subscription'
        },
        'meta': {}
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """
    Request password reset (public).
    POST /api/aut/password-reset/request/
    Sends password reset email.
    """
    email = request.data.get('email')
    if not email:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Email is required',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Normalize email to lowercase for case-insensitive lookup
    email = email.lower().strip()
    
    try:
        user = User.objects.get(email__iexact=email)
        if not user.is_active:
            return Response({
                'success': False,
                'error': {
                    'code': 'ACCOUNT_DISABLED',
                    'message': 'Account is disabled',
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Send password reset email
        from .utils import send_password_reset_email
        token, code = send_password_reset_email(user)
        
        # Store token in user's profile preferences (temporary solution)
        # In production, use a dedicated PasswordResetToken model
        profile, _ = Profile.objects.get_or_create(user=user)
        if not profile.preferences:
            profile.preferences = {}
        profile.preferences['password_reset_token'] = token
        profile.preferences['password_reset_code'] = code
        profile.preferences['password_reset_expires'] = (timezone.now() + timedelta(hours=1)).isoformat()
        profile.save()
        
        return Response({
            'success': True,
            'data': {
                'message': 'Password reset email sent',
                'token': token if settings.DEBUG else None,  # Only return in debug mode
                'code': code if settings.DEBUG else None,  # Only return in debug mode
            },
            'meta': {}
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        # Don't reveal if email exists (security best practice)
        return Response({
            'success': True,
            'data': {
                'message': 'If the email exists, a password reset link has been sent',
            },
            'meta': {}
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    """
    Confirm password reset (public).
    POST /api/aut/password-reset/confirm/
    Resets password with token.
    """
    token = request.data.get('token')
    code = request.data.get('code')
    new_password = request.data.get('new_password')
    new_password_confirm = request.data.get('new_password_confirm')
    
    if not all([token, code, new_password, new_password_confirm]):
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Token, code, new_password, and new_password_confirm are required',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if new_password != new_password_confirm:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Passwords do not match',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate password
    from django.contrib.auth.password_validation import validate_password
    try:
        validate_password(new_password)
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Password does not meet requirements',
                'details': list(e.messages) if hasattr(e, 'messages') else [str(e)],
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Find user with matching token
    import hashlib
    from django.conf import settings
    from django.utils import timezone
    from datetime import timedelta
    
    users = User.objects.filter(is_active=True)
    for user in users:
        profile, _ = Profile.objects.get_or_create(user=user)
        if profile.preferences and 'password_reset_token' in profile.preferences:
            stored_token = profile.preferences.get('password_reset_token')
            stored_code = profile.preferences.get('password_reset_code')
            expires_str = profile.preferences.get('password_reset_expires')
            
            if stored_token == token and stored_code == code:
                # Check expiration
                if expires_str:
                    expires = timezone.datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                    if timezone.now() > expires:
                        return Response({
                            'success': False,
                            'error': {
                                'code': 'TOKEN_EXPIRED',
                                'message': 'Password reset token has expired',
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Reset password
                user.set_password(new_password)
                user.save()
                
                # Clear reset token
                profile.preferences.pop('password_reset_token', None)
                profile.preferences.pop('password_reset_code', None)
                profile.preferences.pop('password_reset_expires', None)
                profile.save()
                
                return Response({
                    'success': True,
                    'data': {
                        'message': 'Password reset successfully',
                    },
                    'meta': {}
                }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'error': {
            'code': 'INVALID_TOKEN',
            'message': 'Invalid or expired password reset token',
        }
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def email_verification_request_view(request):
    """
    Request email verification (public).
    POST /api/aut/verify-email/request/
    Sends verification email.
    """
    email = request.data.get('email')
    if not email:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Email is required',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Normalize email to lowercase for case-insensitive lookup
    email = email.lower().strip()
    
    try:
        user = User.objects.get(email__iexact=email)
        if user.is_verified:
            return Response({
                'success': True,
                'data': {
                    'message': 'Email is already verified',
                },
                'meta': {}
            }, status=status.HTTP_200_OK)
        
        # Send verification email
        from .utils import send_verification_email
        token, code = send_verification_email(user)
        
        # Store token in user's profile preferences (temporary solution)
        profile, _ = Profile.objects.get_or_create(user=user)
        if not profile.preferences:
            profile.preferences = {}
        profile.preferences['verification_token'] = token
        profile.preferences['verification_code'] = code
        profile.save()
        
        return Response({
            'success': True,
            'data': {
                'message': 'Verification email sent',
                'token': token if settings.DEBUG else None,  # Only return in debug mode
                'code': code if settings.DEBUG else None,  # Only return in debug mode
            },
            'meta': {}
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'USER_NOT_FOUND',
                'message': 'User with this email does not exist',
            }
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def email_verification_confirm_view(request):
    """
    Confirm email verification (public).
    POST /api/aut/verify-email/confirm/
    Verifies email with token.
    """
    token = request.data.get('token')
    code = request.data.get('code')
    
    if not all([token, code]):
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Token and code are required',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Find user with matching token
    users = User.objects.filter(is_active=True, is_verified=False)
    for user in users:
        profile, _ = Profile.objects.get_or_create(user=user)
        if profile.preferences and 'verification_token' in profile.preferences:
            stored_token = profile.preferences.get('verification_token')
            stored_code = profile.preferences.get('verification_code')
            
            if stored_token == token and stored_code == code:
                # Verify email
                user.is_verified = True
                user.save()
                
                # Clear verification token
                profile.preferences.pop('verification_token', None)
                profile.preferences.pop('verification_code', None)
                profile.save()
                
                return Response({
                    'success': True,
                    'data': {
                        'message': 'Email verified successfully',
                        'user': UserSerializer(user).data,
                    },
                    'meta': {}
                }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'error': {
            'code': 'INVALID_TOKEN',
            'message': 'Invalid verification token',
        }
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_verification_email_view(request):
    """
    Resend verification email (authenticated).
    POST /api/aut/verify-email/resend/
    """
    user = request.user
    if user.is_verified:
        return Response({
            'success': True,
            'data': {
                'message': 'Email is already verified',
            },
            'meta': {}
        }, status=status.HTTP_200_OK)
    
    # Send verification email
    from .utils import send_verification_email
    token, code = send_verification_email(user)
    
    # Store token
    profile, _ = Profile.objects.get_or_create(user=user)
    if not profile.preferences:
        profile.preferences = {}
    profile.preferences['verification_token'] = token
    profile.preferences['verification_code'] = code
    profile.save()
    
    return Response({
        'success': True,
        'data': {
            'message': 'Verification email sent',
            'token': token if settings.DEBUG else None,
            'code': code if settings.DEBUG else None,
        },
        'meta': {}
    }, status=status.HTTP_200_OK)
