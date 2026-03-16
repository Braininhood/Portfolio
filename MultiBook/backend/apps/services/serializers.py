"""
Services app serializers.
Service and Category serializers.
"""
from rest_framework import serializers
from .models import Category, Service


class CategorySerializer(serializers.ModelSerializer):
    """
    Category serializer.
    """
    services_count = serializers.IntegerField(source='services.count', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'position', 
                  'is_active', 'services_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class ServiceSerializer(serializers.ModelSerializer):
    """
    Service serializer with category information.
    """
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Service
        fields = ['id', 'category', 'category_id', 'category_name', 'name', 'slug', 
                  'description', 'duration', 'price', 'currency', 'image', 'color',
                  'capacity', 'padding_time', 'position', 'is_active',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class ServiceListSerializer(serializers.ModelSerializer):
    """
    Simplified service serializer for list views (public endpoints).
    """
    category_name = serializers.SerializerMethodField()
    extras = serializers.JSONField(required=False, default=list)

    class Meta:
        model = Service
        fields = ['id', 'category_name', 'name', 'slug', 'description', 'duration', 'price',
                  'currency', 'image', 'color', 'is_active', 'capacity', 'padding_time', 'extras']
    
    def get_category_name(self, obj):
        """Safely get category name, returning None if category is None."""
        return obj.category.name if obj.category else None


class StaffServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """
    For staff: create new service (pending approval) or update service they created / their overrides.
    """
    category_id = serializers.IntegerField(write_only=True, required=True)
    extras = serializers.JSONField(required=False, default=list)

    class Meta:
        model = Service
        fields = ['id', 'category_id', 'name', 'slug', 'description', 'duration', 'price', 'currency',
                  'extras', 'approval_status', 'created_by_staff', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'approval_status', 'created_by_staff', 'created_at', 'updated_at']
