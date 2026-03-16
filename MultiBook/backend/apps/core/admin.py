"""
Core admin mixins for role-based access control.
"""
from django.contrib import admin
from django.db import models


class ManagerPermissionMixin:
    """
    Mixin to add manager permission checks to Django admin.
    Respects manager's permission settings (can_manage_customers, can_manage_staff, etc.)
    """
    
    def has_module_permission(self, request):
        """Check if user can see this module in admin."""
        if not request.user.is_authenticated:
            return False
        
        # Admin can always see all modules
        if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin'):
            return True
        
        # Managers can see modules based on their permissions
        if hasattr(request.user, 'role') and request.user.role == 'manager':
            if hasattr(request.user, 'manager_profile'):
                return self._check_manager_module_permission(request.user.manager_profile)
        
        # Staff and customers should not see admin by default
        # (unless explicitly granted permissions)
        return False
    
    def has_view_permission(self, request, obj=None):
        """Check if user can view objects."""
        if not request.user.is_authenticated:
            return False
        
        # Admin can view everything
        if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin'):
            return True
        
        # Managers can view based on permissions
        if hasattr(request.user, 'role') and request.user.role == 'manager':
            if hasattr(request.user, 'manager_profile'):
                return self._check_manager_view_permission(request.user.manager_profile, obj)
        
        return False
    
    def has_add_permission(self, request):
        """Check if user can add objects."""
        return self.has_view_permission(request)
    
    def has_change_permission(self, request, obj=None):
        """Check if user can change objects."""
        return self.has_view_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """Check if user can delete objects."""
        # Only admins and full managers can delete
        if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin'):
            return True
        
        if hasattr(request.user, 'role') and request.user.role == 'manager':
            if hasattr(request.user, 'manager_profile'):
                manager = request.user.manager_profile
                if manager.is_active and manager.can_manage_all:
                    return self._check_manager_view_permission(manager, obj)
        
        return False
    
    def _check_manager_module_permission(self, manager):
        """
        Override in subclasses to check module-specific permissions.
        Returns True if manager should see this module.
        """
        # Default: only active managers with can_manage_all can see modules
        return manager.is_active and manager.can_manage_all
    
    def _check_manager_view_permission(self, manager, obj=None):
        """
        Override in subclasses to check object-specific permissions.
        Returns True if manager can view this object.
        """
        if not manager.is_active:
            return False
        
        # If can_manage_all, can view everything
        if manager.can_manage_all:
            return True
        
        # Otherwise check specific permissions (override in subclasses)
        return False
    
    def get_queryset(self, request):
        """Filter queryset based on manager permissions."""
        qs = super().get_queryset(request)
        
        # Admin sees everything
        if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin'):
            return qs
        
        # Managers see filtered results
        if hasattr(request.user, 'role') and request.user.role == 'manager':
            if hasattr(request.user, 'manager_profile'):
                return self._filter_manager_queryset(request.user.manager_profile, qs)
        
        return qs.none()
    
    def _filter_manager_queryset(self, manager, qs):
        """
        Override in subclasses to filter queryset based on manager permissions.
        Returns filtered queryset.
        """
        if manager.can_manage_all:
            return qs
        return qs.none()


class StaffManagerPermissionMixin(ManagerPermissionMixin):
    """Admin mixin for staff-related models."""
    
    def _check_manager_module_permission(self, manager):
        """Managers can see staff module if they can manage staff."""
        return manager.is_active and (manager.can_manage_all or manager.can_manage_staff)
    
    def _check_manager_view_permission(self, manager, obj=None):
        """Check if manager can view specific staff."""
        if not manager.is_active:
            return False
        
        if manager.can_manage_all:
            return True
        
        if not manager.can_manage_staff:
            return False
        
        # Check if staff is in manager's scope
        if obj:
            if hasattr(obj, 'staff'):
                staff = obj.staff
            elif hasattr(obj, 'managed_staff'):
                # This is the Staff model itself
                staff = obj
            else:
                return False
            
            if hasattr(staff, 'managing_managers'):
                return manager in staff.managing_managers.all()
        
        # If no object, can see list if has permission
        return True
    
    def _filter_manager_queryset(self, manager, qs):
        """Filter staff queryset based on manager permissions."""
        if manager.can_manage_all:
            return qs
        
        if not manager.can_manage_staff:
            return qs.none()
        
        # Filter to only managed staff
        if hasattr(qs.model, 'staff'):
            # For models with staff FK, filter by managed_staff
            return qs.filter(staff__in=manager.managed_staff.all())
        elif hasattr(qs.model, 'managing_managers'):
            # For Staff model itself
            return qs.filter(managing_managers=manager)
        
        return qs.none()


class CustomerManagerPermissionMixin(ManagerPermissionMixin):
    """Admin mixin for customer-related models."""
    
    def _check_manager_module_permission(self, manager):
        """Managers can see customer module if they can manage customers."""
        return manager.is_active and (manager.can_manage_all or manager.can_manage_customers)
    
    def _check_manager_view_permission(self, manager, obj=None):
        """Check if manager can view specific customer."""
        if not manager.is_active:
            return False
        
        if manager.can_manage_all:
            return True
        
        if not manager.can_manage_customers:
            return False
        
        # Check if customer is in manager's scope
        if obj:
            if hasattr(obj, 'customer'):
                customer = obj.customer
            elif hasattr(obj, 'managing_managers'):
                # This is the Customer model itself
                customer = obj
            else:
                return False
            
            if hasattr(customer, 'managing_managers'):
                return manager in customer.managing_managers.all()
        
        # If no object, can see list if has permission
        return True
    
    def _filter_manager_queryset(self, manager, qs):
        """Filter customer queryset based on manager permissions."""
        if manager.can_manage_all:
            return qs
        
        if not manager.can_manage_customers:
            return qs.none()
        
        # Filter to only managed customers
        if hasattr(qs.model, 'customer'):
            # For models with customer FK, filter by managed_customers
            return qs.filter(customer__in=manager.managed_customers.all())
        elif hasattr(qs.model, 'managing_managers'):
            # For Customer model itself
            return qs.filter(managing_managers=manager)
        
        return qs.none()


class AppointmentManagerPermissionMixin(ManagerPermissionMixin):
    """Admin mixin for appointment-related models."""
    
    def _check_manager_module_permission(self, manager):
        """Managers can see appointments if they can manage appointments."""
        return manager.is_active and manager.can_manage_appointments
    
    def _check_manager_view_permission(self, manager, obj=None):
        """Check if manager can view specific appointment."""
        if not manager.is_active:
            return False
        
        if not manager.can_manage_appointments:
            return False
        
        # If can_manage_all, can view all appointments
        if manager.can_manage_all:
            return True
        
        # Otherwise, can only view appointments for their managed staff/customers
        if obj:
            if hasattr(obj, 'staff'):
                # Check if appointment's staff is managed by this manager
                if hasattr(obj.staff, 'managing_managers'):
                    return manager in obj.staff.managing_managers.all()
            if hasattr(obj, 'customer_booking') and obj.customer_booking:
                # Check if appointment's customer is managed by this manager
                customer = obj.customer_booking.customer
                if hasattr(customer, 'managing_managers'):
                    return manager in customer.managing_managers.all()
        
        # If no object, can see list if has permission
        return True
    
    def _filter_manager_queryset(self, manager, qs):
        """Filter appointment queryset based on manager permissions."""
        if not manager.can_manage_appointments:
            return qs.none()
        
        if manager.can_manage_all:
            return qs
        
        # Filter to appointments for managed staff or customers
        managed_staff_ids = manager.managed_staff.values_list('id', flat=True)
        managed_customer_ids = manager.managed_customers.values_list('id', flat=True)
        
        # Appointments for managed staff or customers
        qs = qs.filter(
            models.Q(staff__id__in=managed_staff_ids) |
            models.Q(customer_booking__customer__id__in=managed_customer_ids)
        )
        
        return qs.distinct()
