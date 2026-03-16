"""
Appointments admin configuration.
"""
from django.contrib import admin
from apps.core.admin import AppointmentManagerPermissionMixin
from .models import Appointment, CustomerAppointment


class CustomerAppointmentInline(admin.TabularInline):
    """Inline admin for CustomerAppointment."""
    model = CustomerAppointment
    extra = 0
    fields = ['customer', 'number_of_persons', 'total_price', 'payment_status', 'can_cancel', 'can_reschedule']
    readonly_fields = ['can_cancel', 'can_reschedule']


@admin.register(Appointment)
class AppointmentAdmin(AppointmentManagerPermissionMixin, admin.ModelAdmin):
    """Appointment admin."""
    list_display = ['id', 'service', 'staff', 'start_time', 'end_time', 'status', 'appointment_type', 'created_at']
    list_filter = ['status', 'appointment_type', 'created_at', 'staff']
    search_fields = ['service__name', 'staff__name', 'staff__email']
    autocomplete_fields = ['staff', 'service', 'subscription', 'order']
    date_hierarchy = 'start_time'
    ordering = ['-start_time']
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('staff', 'service', 'start_time', 'end_time', 'status', 'appointment_type')
        }),
        ('Relationships', {
            'fields': ('subscription', 'order'),
            'description': 'Leave blank for single appointments'
        }),
        ('Calendar Sync', {
            'fields': ('calendar_event_id', 'calendar_synced_to'),
            'classes': ('collapse',)
        }),
        ('Internal Notes', {
            'fields': ('internal_notes', 'location_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [CustomerAppointmentInline]


@admin.register(CustomerAppointment)
class CustomerAppointmentAdmin(AppointmentManagerPermissionMixin, admin.ModelAdmin):
    """Customer appointment booking admin."""
    list_display = ['customer', 'appointment', 'total_price', 'payment_status', 'can_cancel', 'can_reschedule', 'created_at']
    list_filter = ['payment_status', 'can_cancel', 'can_reschedule', 'created_at']
    search_fields = ['customer__name', 'customer__email', 'appointment__service__name']
    autocomplete_fields = ['customer', 'appointment']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('customer', 'appointment')
        }),
        ('Booking Details', {
            'fields': ('number_of_persons', 'extras', 'custom_fields')
        }),
        ('Pricing & Payment', {
            'fields': ('total_price', 'deposit_paid', 'payment_status', 'payment_method')
        }),
        ('Cancellation Policy', {
            'fields': ('cancellation_deadline', 'can_cancel', 'can_reschedule', 'refund_amount'),
            'description': '24-hour cancellation policy'
        }),
        ('Status', {
            'fields': ('is_confirmed', 'is_cancelled', 'cancellation_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'cancellation_deadline', 'can_cancel', 'can_reschedule']

