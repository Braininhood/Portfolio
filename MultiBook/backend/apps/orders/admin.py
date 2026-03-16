"""
Orders admin configuration.
"""
from django.contrib import admin
from apps.core.admin import AppointmentManagerPermissionMixin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline admin for OrderItem."""
    model = OrderItem
    extra = 1
    fields = ['service', 'staff', 'quantity', 'unit_price', 'total_price', 'status']
    autocomplete_fields = ['service', 'staff']


@admin.register(Order)
class OrderAdmin(AppointmentManagerPermissionMixin, admin.ModelAdmin):
    """Order admin."""
    list_display = ['order_number', 'customer_or_guest', 'total_price', 'status', 'payment_status', 'is_guest_order', 'scheduled_date_time', 'items_count', 'created_at']
    list_filter = ['status', 'payment_status', 'is_guest_order', 'created_at']
    search_fields = ['order_number', 'tracking_token', 'customer__name', 'customer__email', 'guest_email', 'guest_name', 'postcode']
    autocomplete_fields = ['customer']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def items_count(self, obj):
        """Display number of items in order."""
        return obj.items.count()
    items_count.short_description = 'Items'
    
    def scheduled_date_time(self, obj):
        """Display scheduled date and time."""
        if obj.scheduled_date:
            date_str = obj.scheduled_date.strftime('%Y-%m-%d')
            time_str = obj.scheduled_time.strftime('%H:%M') if obj.scheduled_time else 'N/A'
            return f"{date_str} {time_str}"
        return 'N/A'
    scheduled_date_time.short_description = 'Scheduled'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'tracking_token', 'customer', 'is_guest_order', 'account_linked_at')
        }),
        ('Guest Information', {
            'fields': ('guest_email', 'guest_name', 'guest_phone'),
            'description': 'Required for guest orders (when customer is NULL)'
        }),
        ('Order Status', {
            'fields': ('status', 'payment_status', 'total_price', 'deposit_paid')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'scheduled_time')
        }),
        ('Cancellation Policy', {
            'fields': ('cancellation_policy_hours', 'cancellation_deadline', 'can_cancel', 'can_reschedule'),
            'description': '24-hour cancellation policy'
        }),
        ('Service Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'postcode', 'country', 'notes'),
            'description': 'Service address and notes (required for all orders)'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['order_number', 'tracking_token', 'account_linked_at', 'cancellation_deadline', 'can_cancel', 'can_reschedule', 'created_at', 'updated_at']
    
    inlines = [OrderItemInline]
    
    def customer_or_guest(self, obj):
        """Display customer name or guest info."""
        if obj.customer:
            return obj.customer.name
        return f"{obj.guest_name or 'Guest'} ({obj.guest_email})"
    customer_or_guest.short_description = 'Customer / Guest'


@admin.register(OrderItem)
class OrderItemAdmin(AppointmentManagerPermissionMixin, admin.ModelAdmin):
    """Order item admin."""
    list_display = ['order', 'service', 'staff', 'quantity', 'unit_price', 'total_price', 'status', 'appointment']
    list_filter = ['order__status', 'order__created_at', 'status']
    search_fields = ['order__order_number', 'service__name', 'staff__name']
    autocomplete_fields = ['order', 'service', 'staff', 'appointment']
    ordering = ['order', 'created_at']
    
    fieldsets = (
        ('Item Information', {
            'fields': ('order', 'service', 'staff', 'quantity')
        }),
        ('Pricing', {
            'fields': ('unit_price', 'total_price')
        }),
        ('Appointment', {
            'fields': ('appointment',),
            'description': 'Appointment created for this order item (created when order is confirmed)'
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']

