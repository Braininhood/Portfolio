"""
Supabase Authentication Service
Handles authentication using Supabase Auth instead of Django's built-in auth.
"""
from supabase import create_client, Client
from django.conf import settings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SupabaseAuthService:
    """Service for Supabase authentication operations."""
    
    def __init__(self):
        self.url = getattr(settings, 'SUPABASE_URL', '')
        self.key = getattr(settings, 'SUPABASE_ANON_KEY', '')
        self.service_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', '')
        
        if not self.url or not self.key:
            logger.warning("Supabase credentials not configured. Auth operations will fail.")
            self.client = None
            self.admin_client = None
        else:
            self.client: Client = create_client(self.url, self.key)
            self.admin_client: Client = create_client(self.url, self.service_key) if self.service_key else None
    
    def sign_up(self, email: str, password: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Register a new user with Supabase Auth.
        
        Args:
            email: User email
            password: User password
            metadata: Additional user metadata (role, first_name, last_name, etc.)
        
        Returns:
            Dict with user data and session tokens
        """
        if not self.client:
            return {"success": False, "error": "Supabase client not initialized"}
        
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": metadata or {}
                }
            })
            return {
                "success": True,
                "user": response.user,
                "session": response.session,
            }
        except Exception as e:
            logger.error(f"Supabase sign up error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in user with Supabase Auth.
        
        Returns:
            Dict with user data and session tokens
        """
        if not self.client:
            return {"success": False, "error": "Supabase client not initialized"}
        
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {
                "success": True,
                "user": response.user,
                "session": response.session,
            }
        except Exception as e:
            logger.error(f"Supabase sign in error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def sign_out(self, access_token: str) -> Dict[str, Any]:
        """Sign out user."""
        if not self.client:
            return {"success": False, "error": "Supabase client not initialized"}
        
        try:
            self.client.auth.set_session(access_token, "")
            self.client.auth.sign_out()
            return {"success": True}
        except Exception as e:
            logger.error(f"Supabase sign out error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user from access token."""
        if not self.client:
            return None
        
        try:
            self.client.auth.set_session(access_token, "")
            user = self.client.auth.get_user(access_token)
            return user.user if user else None
        except Exception as e:
            logger.error(f"Supabase get user error: {str(e)}")
            return None
    
    def update_user(self, access_token: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user metadata."""
        if not self.client:
            return {"success": False, "error": "Supabase client not initialized"}
        
        try:
            self.client.auth.set_session(access_token, "")
            response = self.client.auth.update_user(updates)
            return {
                "success": True,
                "user": response.user
            }
        except Exception as e:
            logger.error(f"Supabase update user error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def reset_password(self, email: str) -> Dict[str, Any]:
        """Send password reset email."""
        if not self.client:
            return {"success": False, "error": "Supabase client not initialized"}
        
        try:
            self.client.auth.reset_password_for_email(email)
            return {"success": True}
        except Exception as e:
            logger.error(f"Supabase reset password error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def verify_email(self, token: str) -> Dict[str, Any]:
        """Verify user email."""
        if not self.client:
            return {"success": False, "error": "Supabase client not initialized"}
        
        try:
            response = self.client.auth.verify_otp({
                "token": token,
                "type": "email"
            })
            return {
                "success": True,
                "user": response.user,
                "session": response.session,
            }
        except Exception as e:
            logger.error(f"Supabase verify email error: {str(e)}")
            return {"success": False, "error": str(e)}


# Singleton instance
supabase_auth = SupabaseAuthService()
