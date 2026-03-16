"""
Customers admin configuration.
"""
from django.contrib import admin
from apps.core.admin import CustomerManagerPermissionMixin
from .models import Customer, Address


class AddressInline(admin.TabularInline):
    """Inline admin for Address."""
    model = Address
    extra = 1
    fields = ['type', 'address_line1', 'address_line2', 'city', 'postcode', 'country', 'is_default', 'address_validated']


@admin.register(Customer)
class CustomerAdmin(CustomerManagerPermissionMixin, admin.ModelAdmin):
    """Customer admin."""
    list_display = ['name', 'email', 'phone', 'postcode', 'user', 'created_at']
    list_filter = ['address_validated', 'created_at']
    search_fields = ['name', 'email', 'phone', 'postcode', 'address_line1']
    autocomplete_fields = ['user']
    ordering = ['name']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'name', 'email', 'phone')
        }),
        ('Primary Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'postcode', 'country', 'address_validated')
        }),
        ('Additional Information', {
            'fields': ('notes', 'tags'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [AddressInline]


@admin.register(Address)
class AddressAdmin(CustomerManagerPermissionMixin, admin.ModelAdmin):
    """Address admin."""
    list_display = ['customer', 'type', 'address_line1', 'city', 'postcode', 'is_default', 'address_validated']
    list_filter = ['type', 'is_default', 'address_validated', 'country']
    search_fields = ['customer__name', 'customer__email', 'address_line1', 'postcode', 'city']
    autocomplete_fields = ['customer']
    ordering = ['customer', '-is_default', 'type']
    
    fieldsets = (
        ('Address Information', {
            'fields': ('customer', 'type', 'address_line1', 'address_line2', 'city', 'postcode', 'country')
        }),
        ('Settings', {
            'fields': ('is_default', 'address_validated')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']

