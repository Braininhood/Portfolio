"""
Custom permissions for role-based access control.
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission check for Admin users.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role == 'admin'
        )


class IsManager(permissions.BasePermission):
    """
    Permission check for Manager users.
    Managers have flexible permissions assigned by admin.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if not hasattr(request.user, 'role') or request.user.role != 'manager':
            return False
        
        # Check if manager profile exists and is active
        if hasattr(request.user, 'manager_profile'):
            return request.user.manager_profile.is_active
        
        return True


class ManagerCanManageCustomers(permissions.BasePermission):
    """
    Permission check for Manager's ability to manage customers.
    Respects manager's permission settings.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Admin can always manage customers
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        # Check manager permissions
        if hasattr(request.user, 'role') and request.user.role == 'manager':
            if hasattr(request.user, 'manager_profile'):
                manager = request.user.manager_profile
                return manager.is_active and (manager.can_manage_all or manager.can_manage_customers)
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Admin can manage any customer
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        # Manager can manage customers within their scope
        if hasattr(request.user, 'role') and request.user.role == 'manager':
            if hasattr(request.user, 'manager_profile'):
                manager = request.user.manager_profile
                if not (manager.is_active and (manager.can_manage_all or manager.can_manage_customers)):
                    return False
                
                # Check if customer is in manager's scope
                if manager.can_manage_all:
                    return True
                
                # Check if customer is in managed_customers
                if hasattr(obj, 'customer'):
                    customer = obj.customer
                else:
                    customer = obj
                
                if hasattr(customer, 'managing_managers'):
                    return manager in customer.managing_managers.all()
        
        return False


class ManagerCanManageStaff(permissions.BasePermission):
    """
    Permission check for Manager's ability to manage staff.
    Respects manager's permission settings.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Admin can always manage staff
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        # Check manager permissions
        if hasattr(request.user, 'role') and request.user.role == 'manager':
            if hasattr(request.user, 'manager_profile'):
                manager = request.user.manager_profile
                return manager.is_active and (manager.can_manage_all or manager.can_manage_staff)
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Admin can manage any staff
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        # Manager can manage staff within their scope
        if hasattr(request.user, 'role') and request.user.role == 'manager':
            if hasattr(request.user, 'manager_profile'):
                manager = request.user.manager_profile
                if not (manager.is_active and (manager.can_manage_all or manager.can_manage_staff)):
                    return False
                
                # Check if staff is in manager's scope
                if manager.can_manage_all:
                    return True
                
                # Check if staff is in managed_staff
                if hasattr(obj, 'staff'):
                    staff = obj.staff
                else:
                    staff = obj
                
                if hasattr(staff, 'managing_managers'):
                    return manager in staff.managing_managers.all()
        
        return False


class ManagerCanManageAppointments(permissions.BasePermission):
    """
    Permission check for Manager's ability to manage appointments.
    Respects manager's permission settings.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Admin can always manage appointments
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        # Check manager permissions
        if hasattr(request.user, 'role') and request.user.role == 'manager':
            if hasattr(request.user, 'manager_profile'):
                manager = request.user.manager_profile
                return manager.is_active and manager.can_manage_appointments
        
        return False


class IsStaff(permissions.BasePermission):
    """
    Permission check for Staff users.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role == 'staff'
        )


class IsCustomer(permissions.BasePermission):
    """
    Permission check for Customer users.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role == 'customer'
        )


class IsAdminOrManager(permissions.BasePermission):
    """
    Permission check for Admin or Manager users.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role in ['admin', 'manager']
        )


class IsStaffOrManager(permissions.BasePermission):
    """
    Permission check for Staff or Manager users.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role in ['staff', 'manager']
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission check for object owners or Admin users.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access anything
        if request.user and request.user.is_authenticated and request.user.role == 'admin':
            return True
        
        # Check if user is the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'customer'):
            return obj.customer.user == request.user
        
        return False
