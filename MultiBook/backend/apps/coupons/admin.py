"""
Coupons app admin.
"""
from django.contrib import admin
from .models import Coupon, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'discount_type', 'discount_value', 'status', 'used_count', 'valid_from', 'valid_until']
    list_filter = ['status', 'discount_type', 'valid_from', 'valid_until']
    search_fields = ['code', 'name']
    readonly_fields = ['used_count', 'created_at', 'updated_at']
    filter_horizontal = ['applicable_services', 'excluded_services']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'status')
        }),
        ('Discount Details', {
            'fields': ('discount_type', 'discount_value', 'minimum_order_amount')
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'max_uses_per_customer', 'used_count')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Service Restrictions', {
            'fields': ('applicable_services', 'excluded_services')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'customer', 'guest_email', 'discount_amount', 'order_amount', 'final_amount', 'created_at']
    list_filter = ['created_at', 'coupon']
    search_fields = ['coupon__code', 'customer__name', 'customer__email', 'guest_email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Usage Information', {
            'fields': ('coupon', 'customer', 'guest_email')
        }),
        ('Related Objects', {
            'fields': ('order', 'subscription', 'appointment')
        }),
        ('Amounts', {
            'fields': ('discount_amount', 'order_amount', 'final_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
