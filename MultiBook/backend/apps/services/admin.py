"""
Services admin configuration.
"""
from django.contrib import admin
from apps.core.admin import ManagerPermissionMixin
from .models import Category, Service


@admin.register(Category)
class CategoryAdmin(ManagerPermissionMixin, admin.ModelAdmin):
    """Category admin."""
    list_display = ['name', 'slug', 'position', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['position', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'image')
        }),
        ('Display Settings', {
            'fields': ('position', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def _check_manager_module_permission(self, manager):
        """Managers can view categories (public information)."""
        return manager.is_active


@admin.register(Service)
class ServiceAdmin(ManagerPermissionMixin, admin.ModelAdmin):
    """Service admin."""
    list_display = ['name', 'category', 'price', 'currency', 'duration', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'currency', 'created_at']
    search_fields = ['name', 'description', 'category__name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['category', 'position', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'slug', 'description', 'image', 'color')
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'currency', 'duration', 'capacity', 'padding_time')
        }),
        ('Display Settings', {
            'fields': ('position', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def _check_manager_module_permission(self, manager):
        """Managers can view services (public information)."""
        return manager.is_active

