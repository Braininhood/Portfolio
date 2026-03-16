"""
Staff app serializers.
Staff, StaffSchedule, StaffService, and StaffArea serializers.
"""
from rest_framework import serializers
from .models import Staff, StaffSchedule, StaffService, StaffArea
from apps.services.serializers import ServiceListSerializer


class StaffAreaSerializer(serializers.ModelSerializer):
    """
    Staff service area serializer (postcode + radius; optional service for per-service area).
    """
    service_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    service_name = serializers.SerializerMethodField()

    class Meta:
        model = StaffArea
        fields = ['id', 'staff', 'service', 'service_id', 'service_name', 'postcode', 'radius_miles', 'is_active',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'staff', 'created_at', 'updated_at']
    
    def get_service_name(self, obj):
        """Safely get service name, returning None if service is None."""
        return obj.service.name if obj.service else None

    def create(self, validated_data):
        service_id = validated_data.pop('service_id', None)
        from apps.services.models import Service
        validated_data['service'] = Service.objects.get(id=service_id) if service_id else None
        return super().create(validated_data)

    def update(self, instance, validated_data):
        service_id = validated_data.pop('service_id', None)
        if 'service_id' in self.initial_data:
            from apps.services.models import Service
            instance.service = Service.objects.get(id=service_id) if service_id else None
        return super().update(instance, validated_data)


class StaffScheduleSerializer(serializers.ModelSerializer):
    """
    Staff schedule serializer.
    """
    day_name = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffSchedule
        fields = ['id', 'staff', 'day_of_week', 'day_name', 'start_time', 'end_time',
                  'breaks', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_day_name(self, obj):
        """Safely get day name."""
        try:
            return obj.get_day_of_week_display()
        except Exception:
            return None


class StaffServiceSerializer(serializers.ModelSerializer):
    """
    Staff-Service relationship serializer with price/duration overrides.
    """
    service = serializers.SerializerMethodField()
    service_id = serializers.IntegerField(write_only=True, required=True)
    service_name = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffService
        fields = ['id', 'staff', 'service', 'service_id', 'service_name',
                  'price_override', 'duration_override', 'is_active',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_service(self, obj):
        """Safely serialize service, returning None if service is missing."""
        try:
            if obj.service:
                return ServiceListSerializer(obj.service).data
        except Exception:
            # If serialization fails, return None to prevent 500 errors
            pass
        return None
    
    def get_service_name(self, obj):
        """Safely get service name, returning None if service is None."""
        return obj.service.name if obj.service else None


class StaffSerializer(serializers.ModelSerializer):
    """
    Staff serializer with related schedules, services, and areas.
    """
    schedules = StaffScheduleSerializer(many=True, read_only=True)
    services = StaffServiceSerializer(many=True, read_only=True, source='staff_services')
    service_areas = StaffAreaSerializer(many=True, read_only=True)
    user_email = serializers.SerializerMethodField()
    
    class Meta:
        model = Staff
        fields = ['id', 'user', 'user_email', 'name', 'email', 'phone', 'photo', 'bio',
                  'services', 'schedules', 'service_areas', 'is_active',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_email(self, obj):
        """Safely get user email, returning None if user is None."""
        try:
            return obj.user.email if obj.user else None
        except Exception:
            return None


class StaffListSerializer(serializers.ModelSerializer):
    """
    Simplified staff serializer for public list views (filtered by postcode/area).
    """
    service_areas = serializers.SerializerMethodField()
    
    class Meta:
        model = Staff
        fields = ['id', 'name', 'email', 'phone', 'photo', 'bio', 'service_areas', 'is_active']
    
    def get_service_areas(self, obj):
        """Return active service areas for this staff member."""
        areas = obj.service_areas.filter(is_active=True)
        return [{'postcode': area.postcode, 'radius_miles': float(area.radius_miles)} 
                for area in areas]


class AdminStaffListSerializer(StaffListSerializer):
    """
    Staff list for admin/manager: same as StaffListSerializer but includes user (FK id)
    for bulk calendar sync and other admin tools. Not used on public API.
    """
    class Meta(StaffListSerializer.Meta):
        fields = ['id', 'user', 'name', 'email', 'phone', 'photo', 'bio', 'service_areas', 'is_active']
