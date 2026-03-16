"""
Role-based access control decorators.
"""
from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def require_role(*allowed_roles):
    """
    Decorator to require specific role(s) for a view.
    
    Usage:
        @require_role('admin', 'manager')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
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
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_admin(view_func):
    """
    Decorator to require admin role.
    
    Usage:
        @require_admin
        def admin_view(request):
            ...
    """
    return require_role('admin')(view_func)


def require_manager(view_func):
    """
    Decorator to require manager role.
    
    Usage:
        @require_manager
        def manager_view(request):
            ...
    """
    return require_role('manager')(view_func)


def require_staff(view_func):
    """
    Decorator to require staff role.
    
    Usage:
        @require_staff
        def staff_view(request):
            ...
    """
    return require_role('staff')(view_func)


def require_customer(view_func):
    """
    Decorator to require customer role.
    
    Usage:
        @require_customer
        def customer_view(request):
            ...
    """
    return require_role('customer')(view_func)


def require_admin_or_manager(view_func):
    """
    Decorator to require admin or manager role.
    
    Usage:
        @require_admin_or_manager
        def manager_view(request):
            ...
    """
    return require_role('admin', 'manager')(view_func)


def require_staff_or_manager(view_func):
    """
    Decorator to require staff or manager role.
    
    Usage:
        @require_staff_or_manager
        def staff_view(request):
            ...
    """
    return require_role('admin', 'manager', 'staff')(view_func)
