"""
Staff admin configuration.
"""
from django.contrib import admin
from apps.core.admin import StaffManagerPermissionMixin
from .models import Staff, StaffSchedule, StaffService, StaffArea


class StaffServiceInline(admin.TabularInline):
    """Inline admin for StaffService."""
    model = StaffService
    extra = 1
    fields = ['service', 'price_override', 'duration_override', 'is_active']
    autocomplete_fields = ['service']


class StaffScheduleInline(admin.TabularInline):
    """Inline admin for StaffSchedule."""
    model = StaffSchedule
    extra = 0
    fields = ['day_of_week', 'start_time', 'end_time', 'breaks', 'is_active']
    readonly_fields = []


class StaffAreaInline(admin.TabularInline):
    """Inline admin for StaffArea."""
    model = StaffArea
    extra = 1
    fields = ['postcode', 'radius_miles', 'is_active']


@admin.register(Staff)
class StaffAdmin(StaffManagerPermissionMixin, admin.ModelAdmin):
    """Staff member admin."""
    list_display = ['name', 'email', 'phone', 'is_active', 'user', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'email', 'phone', 'bio']
    autocomplete_fields = ['user']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'email', 'phone', 'photo', 'bio')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [StaffServiceInline, StaffScheduleInline, StaffAreaInline]


@admin.register(StaffSchedule)
class StaffScheduleAdmin(StaffManagerPermissionMixin, admin.ModelAdmin):
    """Staff schedule admin."""
    list_display = ['staff', 'day_of_week', 'start_time', 'end_time', 'is_active', 'created_at']
    list_filter = ['is_active', 'day_of_week', 'created_at']
    search_fields = ['staff__name', 'staff__email']
    autocomplete_fields = ['staff']
    ordering = ['staff', 'day_of_week']
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('staff', 'day_of_week', 'start_time', 'end_time', 'breaks')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StaffService)
class StaffServiceAdmin(StaffManagerPermissionMixin, admin.ModelAdmin):
    """Staff service assignment admin."""
    list_display = ['staff', 'service', 'price_override', 'duration_override', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['staff__name', 'service__name']
    autocomplete_fields = ['staff', 'service']
    ordering = ['staff', 'service']
    
    fieldsets = (
        ('Assignment', {
            'fields': ('staff', 'service')
        }),
        ('Overrides', {
            'fields': ('price_override', 'duration_override'),
            'description': 'Leave blank to use service default pricing/duration'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StaffArea)
class StaffAreaAdmin(StaffManagerPermissionMixin, admin.ModelAdmin):
    """Staff service area admin."""
    list_display = ['staff', 'postcode', 'radius_miles', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['staff__name', 'postcode']
    autocomplete_fields = ['staff']
    ordering = ['staff', 'postcode']
    
    fieldsets = (
        ('Area Information', {
            'fields': ('staff', 'postcode', 'radius_miles')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']

