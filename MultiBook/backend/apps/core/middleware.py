"""
Custom middleware for authentication and role-based access.
"""
from django.utils.deprecation import MiddlewareMixin
from rest_framework.response import Response
from rest_framework import status


class AuthenticationMiddleware(MiddlewareMixin):
    """
    Custom authentication middleware.
    Adds user role information to request for easier access.
    """
    
    def process_request(self, request):
        """
        Add role helper methods to request.user if authenticated.
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Add convenience properties
            user = request.user
            if hasattr(user, 'role'):
                # These properties are already in the User model, but we ensure they're accessible
                request.user_role = user.role
                request.is_admin_user = user.is_admin
                request.is_manager_user = user.is_manager
                request.is_staff_user = user.is_staff_member
                request.is_customer_user = user.is_customer
        return None


class RoleBasedAccessMiddleware(MiddlewareMixin):
    """
    Role-based access control middleware.
    Can be used to enforce role-based access at middleware level.
    """
    
    # Define which paths require which roles
    ROLE_REQUIRED_PATHS = {
        '/api/ad/': ['admin'],
        '/api/man/': ['admin', 'manager'],
        '/api/st/': ['admin', 'manager', 'staff'],
        '/api/cus/': ['admin', 'manager', 'staff', 'customer'],
    }
    
    def process_request(self, request):
        """
        Check if user has required role for the requested path.
        """
        # Skip for public endpoints
        if request.path.startswith('/api/aut/') or request.path.startswith('/api/svc/') or \
           request.path.startswith('/api/stf/') or request.path.startswith('/api/bkg/') or \
           request.path.startswith('/api/slots/'):
            return None
        
        # Check if path requires specific role
        for path_prefix, allowed_roles in self.ROLE_REQUIRED_PATHS.items():
            if request.path.startswith(path_prefix):
                if not request.user.is_authenticated:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'AUTHENTICATION_REQUIRED',
                            'message': 'Authentication required',
                        }
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                user_role = getattr(request.user, 'role', None)
                if user_role not in allowed_roles:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'INSUFFICIENT_PERMISSIONS',
                            'message': f'Access denied. Required roles: {", ".join(allowed_roles)}',
                        }
                    }, status=status.HTTP_403_FORBIDDEN)
                break
        
        return None
