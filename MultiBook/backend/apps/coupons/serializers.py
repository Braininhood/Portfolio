"""
Coupons app serializers.
"""
from rest_framework import serializers
from .models import Coupon, CouponUsage
from apps.services.serializers import ServiceListSerializer


def get_service_queryset():
    """Get Service queryset - defined as function to avoid circular imports."""
    from apps.services.models import Service
    return Service.objects.all()


class CouponSerializer(serializers.ModelSerializer):
    """
    Coupon serializer.
    """
    applicable_services = ServiceListSerializer(many=True, read_only=True)
    applicable_service_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=get_service_queryset(),
        write_only=True,
        required=False,
        source='applicable_services'
    )
    excluded_services = ServiceListSerializer(many=True, read_only=True)
    excluded_service_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=get_service_queryset(),
        write_only=True,
        required=False,
        source='excluded_services'
    )
    is_valid = serializers.SerializerMethodField()
    used_count_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'name', 'discount_type', 'discount_value',
            'max_uses', 'max_uses_per_customer', 'used_count', 'used_count_display',
            'valid_from', 'valid_until', 'minimum_order_amount',
            'applicable_services', 'applicable_service_ids',
            'excluded_services', 'excluded_service_ids',
            'status', 'description', 'is_valid',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'used_count', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for applicable_service_ids and excluded_service_ids
        from apps.services.models import Service
        if 'applicable_service_ids' in self.fields:
            self.fields['applicable_service_ids'].queryset = Service.objects.all()
        if 'excluded_service_ids' in self.fields:
            self.fields['excluded_service_ids'].queryset = Service.objects.all()
    
    def get_is_valid(self, obj):
        """Check if coupon is currently valid."""
        is_valid, _ = obj.is_valid()
        return is_valid
    
    def get_used_count_display(self, obj):
        """Display used count with max uses if applicable."""
        if obj.max_uses:
            return f"{obj.used_count} / {obj.max_uses}"
        return f"{obj.used_count} (unlimited)"


class CouponListSerializer(serializers.ModelSerializer):
    """
    Simplified coupon serializer for list views.
    """
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'name', 'discount_type', 'discount_value',
            'max_uses', 'used_count', 'valid_from', 'valid_until',
            'minimum_order_amount', 'status', 'is_valid'
        ]
    
    def get_is_valid(self, obj):
        """Check if coupon is currently valid."""
        is_valid, _ = obj.is_valid()
        return is_valid


class CouponValidateSerializer(serializers.Serializer):
    """
    Serializer for validating and applying coupons.
    """
    code = serializers.CharField(required=True, help_text='Coupon code')
    order_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        help_text='Order total amount'
    )
    service_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text='List of service IDs in the order'
    )
    customer_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text='Customer ID (optional, for per-customer limits)'
    )


class CouponUsageSerializer(serializers.ModelSerializer):
    """
    Coupon usage serializer.
    """
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CouponUsage
        fields = [
            'id', 'coupon', 'coupon_code', 'customer', 'customer_name',
            'guest_email', 'order', 'subscription', 'appointment',
            'discount_amount', 'order_amount', 'final_amount',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_customer_name(self, obj):
        """Return customer name or guest email."""
        if obj.customer:
            return obj.customer.name
        return obj.guest_email or 'Guest'
