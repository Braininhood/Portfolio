"""
Authentication utilities for password reset and email verification.
"""
import secrets
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()


def generate_verification_token():
    """Generate a secure random token for email verification."""
    return secrets.token_urlsafe(32)


def generate_password_reset_token():
    """Generate a secure random token for password reset."""
    return secrets.token_urlsafe(32)


def send_verification_email(user):
    """
    Send email verification email to user.
    In production, this would send a real email. For now, prints to console.
    """
    token = generate_verification_token()
    
    # Store token in user's profile or create a verification record
    # For simplicity, we'll use a simple approach with a hash
    verification_code = hashlib.sha256(f"{user.email}{token}{settings.SECRET_KEY}".encode()).hexdigest()[:16]
    
    verification_url = f"{settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'}/verify-email?token={token}&code={verification_code}"
    
    subject = 'Verify your MultiBook account'
    message = f"""
    Hello {user.first_name or user.email},
    
    Please verify your email address by clicking the link below:
    
    {verification_url}
    
    If you didn't create an account, please ignore this email.
    
    Best regards,
    MultiBook Team
    """
    
    # In development, print to console
    if settings.DEBUG:
        print(f"\n{'='*60}")
        print(f"VERIFICATION EMAIL (Development Mode)")
        print(f"{'='*60}")
        print(f"To: {user.email}")
        print(f"Subject: {subject}")
        print(f"Verification URL: {verification_url}")
        print(f"Token: {token}")
        print(f"Code: {verification_code}")
        print(f"{'='*60}\n")
    else:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    
    return token, verification_code


def send_password_reset_email(user):
    """
    Send password reset email to user.
    In production, this would send a real email. For now, prints to console.
    """
    token = generate_password_reset_token()
    
    # Store token in user's profile or create a reset record
    # For simplicity, we'll use a simple approach with a hash
    reset_code = hashlib.sha256(f"{user.email}{token}{settings.SECRET_KEY}".encode()).hexdigest()[:16]
    
    reset_url = f"{settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'}/reset-password?token={token}&code={reset_code}"
    
    subject = 'Reset your MultiBook password'
    message = f"""
    Hello {user.first_name or user.email},
    
    You requested to reset your password. Click the link below to reset it:
    
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request a password reset, please ignore this email.
    
    Best regards,
    MultiBook Team
    """
    
    # In development, print to console
    if settings.DEBUG:
        print(f"\n{'='*60}")
        print(f"PASSWORD RESET EMAIL (Development Mode)")
        print(f"{'='*60}")
        print(f"To: {user.email}")
        print(f"Subject: {subject}")
        print(f"Reset URL: {reset_url}")
        print(f"Token: {token}")
        print(f"Code: {reset_code}")
        print(f"{'='*60}\n")
    else:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    
    return token, reset_code
