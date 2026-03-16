"""
Accounts app URLs with security prefix /api/aut/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView  # type: ignore[import-untyped]
from . import views

app_name = 'accounts'

router = DefaultRouter()
router.register(r'profile', views.ProfileViewSet, basename='profile')
router.register(r'invitations', views.InvitationViewSet, basename='invitation')

urlpatterns = [
    # Authentication endpoints (public)
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    # Google OAuth (Google Cloud - new)
    path('google/start/', views.google_oauth_start_view, name='google-oauth-start'),
    path('google/callback/', views.google_oauth_callback_view, name='google-oauth-callback'),
    # Google login (legacy - Supabase OAuth support)
    path('google/', views.google_login_view, name='google-login'),
    path('logout/', views.logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('me/', views.user_profile_view, name='user-profile'),
    path('check-email/', views.check_email_view, name='check-email'),
    
    # Invitation endpoints
    path('invitations/validate/<str:token>/', views.validate_invitation_view, name='validate-invitation'),
    
    # Password reset endpoints (public)
    path('password-reset/request/', views.password_reset_request_view, name='password-reset-request'),
    path('password-reset/confirm/', views.password_reset_confirm_view, name='password-reset-confirm'),
    
    # Email verification endpoints
    path('verify-email/request/', views.email_verification_request_view, name='email-verification-request'),
    path('verify-email/confirm/', views.email_verification_confirm_view, name='email-verification-confirm'),
    path('verify-email/resend/', views.resend_verification_email_view, name='email-verification-resend'),
] + router.urls
