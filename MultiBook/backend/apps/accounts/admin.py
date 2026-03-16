"""
Accounts admin configuration.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile, Manager, Invitation


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User Admin with role support.
    """
    list_display = ('email', 'username', 'role', 'is_active', 'is_verified', 'date_joined')
    list_filter = ('role', 'is_active', 'is_verified', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('MultiBook Custom Fields', {
            'fields': ('role', 'is_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('MultiBook Custom Fields', {
            'fields': ('role', 'is_verified')
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Profile Admin with calendar sync fields.
    """
    list_display = ('user', 'phone', 'timezone', 'calendar_provider', 'calendar_sync_enabled', 'created_at')
    list_filter = ('calendar_provider', 'calendar_sync_enabled', 'timezone', 'created_at')
    search_fields = ('user__email', 'user__username', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Contact Information', {
            'fields': ('phone', 'avatar')
        }),
        ('Settings', {
            'fields': ('timezone', 'preferences')
        }),
        ('Calendar Sync', {
            'fields': (
                'calendar_sync_enabled',
                'calendar_provider',
                'calendar_access_token',
                'calendar_refresh_token',
                'calendar_calendar_id',
                'calendar_sync_settings'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    """
    Manager Admin with permissions configuration.
    """
    list_display = ('user', 'can_manage_all', 'can_manage_customers', 'can_manage_staff', 'is_active', 'created_at')
    list_filter = ('can_manage_all', 'can_manage_customers', 'can_manage_staff', 'can_manage_appointments', 'can_view_reports', 'is_active')
    search_fields = ('user__email', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('managed_staff', 'managed_customers')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Permissions', {
            'fields': (
                'can_manage_all',
                'can_manage_customers',
                'can_manage_staff',
                'can_manage_appointments',
                'can_view_reports',
                'permissions'
            )
        }),
        ('Managed Resources', {
            'fields': ('managed_staff', 'managed_customers', 'managed_locations')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    """
    Invitation Admin for managing staff/manager/admin invitations.
    """
    list_display = ('email', 'role', 'token', 'invited_by', 'is_active', 'used_at', 'expires_at', 'created_at')
    list_filter = ('role', 'is_active', 'used_at', 'expires_at', 'created_at')
    search_fields = ('email', 'token', 'invited_by__email')
    readonly_fields = ('token', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Invitation Details', {
            'fields': ('email', 'role', 'token', 'invited_by')
        }),
        ('Status', {
            'fields': ('is_active', 'used_at', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set invited_by to current user if creating new invitation."""
        if not change:
            obj.invited_by = request.user
        super().save_model(request, obj, form, change)
