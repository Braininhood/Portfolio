"""
Subscriptions admin configuration.
"""
from django.contrib import admin
from apps.core.admin import AppointmentManagerPermissionMixin
from .models import Subscription, SubscriptionAppointment, SubscriptionAppointmentChangeRequest


class SubscriptionAppointmentInline(admin.TabularInline):
    """Inline admin for SubscriptionAppointment."""
    model = SubscriptionAppointment
    extra = 0
    fields = ['appointment', 'scheduled_date', 'status', 'created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['appointment']


@admin.register(Subscription)
class SubscriptionAdmin(AppointmentManagerPermissionMixin, admin.ModelAdmin):
    """Subscription admin."""
    list_display = ['subscription_number', 'customer_or_guest', 'service', 'staff', 'frequency', 'status', 'payment_status', 'is_guest_subscription', 'created_at']
    list_filter = ['status', 'payment_status', 'frequency', 'is_guest_subscription', 'created_at']
    search_fields = ['subscription_number', 'tracking_token', 'customer__name', 'customer__email', 'guest_email', 'guest_name', 'service__name']
    autocomplete_fields = ['customer', 'service', 'staff']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Subscription Information', {
            'fields': ('subscription_number', 'tracking_token', 'customer', 'is_guest_subscription', 'account_linked_at')
        }),
        ('Guest Information', {
            'fields': ('guest_email', 'guest_name', 'guest_phone'),
            'description': 'Required for guest subscriptions (when customer is NULL)'
        }),
        ('Subscription Details', {
            'fields': ('service', 'staff', 'frequency', 'duration_months', 'start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('status', 'payment_status', 'total_price', 'total_paid', 'total_refunded')
        }),
        ('Appointment Scheduling', {
            'fields': ('next_appointment_date', 'total_appointments', 'completed_appointments')
        }),
        ('Cancellation Policy', {
            'fields': ('cancellation_policy_hours', 'paused_until'),
            'description': '24-hour cancellation policy'
        }),
        ('Guest Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'postcode', 'country'),
            'classes': ('collapse',),
            'description': 'Guest address (for guest subscriptions)'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['subscription_number', 'tracking_token', 'account_linked_at', 'created_at', 'updated_at']
    
    inlines = [SubscriptionAppointmentInline]
    
    def customer_or_guest(self, obj):
        """Display customer name or guest info."""
        if obj.customer:
            return obj.customer.name
        return f"{obj.guest_name or 'Guest'} ({obj.guest_email})"
    customer_or_guest.short_description = 'Customer / Guest'


@admin.register(SubscriptionAppointment)
class SubscriptionAppointmentAdmin(AppointmentManagerPermissionMixin, admin.ModelAdmin):
    """Subscription appointment admin."""
    list_display = ['subscription', 'appointment', 'scheduled_date', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'subscription__status']
    search_fields = ['subscription__subscription_number', 'appointment__service__name']
    autocomplete_fields = ['subscription', 'appointment']
    ordering = ['subscription', 'scheduled_date']
    
    fieldsets = (
        ('Appointment Information', {
            'fields': ('subscription', 'appointment', 'scheduled_date', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SubscriptionAppointmentChangeRequest)
class SubscriptionAppointmentChangeRequestAdmin(AppointmentManagerPermissionMixin, admin.ModelAdmin):
    """Admin for subscription visit change requests (approve/reject)."""
    list_display = ['id', 'subscription_appointment', 'requested_date', 'requested_time', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['subscription_appointment__subscription__subscription_number', 'reason']
    autocomplete_fields = ['subscription_appointment', 'reviewed_by']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
