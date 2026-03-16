"""
Orders app serializers.
Order and OrderItem serializers with guest checkout support.
"""
from rest_framework import serializers
from .models import Order, OrderItem, ChangeRequest
from apps.services.serializers import ServiceListSerializer
from apps.staff.serializers import StaffListSerializer
from apps.customers.serializers import CustomerListSerializer, GuestCustomerSerializer
from apps.appointments.serializers import AppointmentSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Order Item serializer.
    """
    service = ServiceListSerializer(read_only=True)
    service_id = serializers.IntegerField(write_only=True, required=True)
    staff = StaffListSerializer(read_only=True, allow_null=True)
    staff_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    appointment = AppointmentSerializer(read_only=True, allow_null=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'service', 'service_id', 'staff', 'staff_id',
                  'quantity', 'unit_price', 'total_price', 'appointment', 'status',
                  'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_price', 'created_at', 'updated_at']


class OrderSerializer(serializers.ModelSerializer):
    """
    Order serializer with guest checkout support (multi-service orders).
    """
    customer = CustomerListSerializer(read_only=True, allow_null=True)
    customer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    items = OrderItemSerializer(many=True, read_only=True)
    appointments = serializers.SerializerMethodField()
    coupon_used = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'customer_id', 'guest_email', 'guest_name', 'guest_phone',
                  'order_number', 'tracking_token', 'is_guest_order', 'account_linked_at',
                  'status', 'total_price', 'deposit_paid', 'payment_status',
                  'scheduled_date', 'scheduled_time', 'cancellation_policy_hours',
                  'can_cancel', 'can_reschedule', 'cancellation_deadline',
                  'address_line1', 'address_line2', 'city', 'postcode', 'country',
                  'notes', 'items', 'appointments', 'coupon_used', 'created_at', 'updated_at']
        read_only_fields = ['id', 'order_number', 'tracking_token', 'account_linked_at',
                             'can_cancel', 'can_reschedule', 'cancellation_deadline',
                             'created_at', 'updated_at']
        extra_kwargs = {
            'guest_email': {'required': False, 'allow_blank': True},
            'guest_name': {'required': False, 'allow_blank': True},
            'guest_phone': {'required': False, 'allow_blank': True},
        }
    
    def get_appointments(self, obj):
        """Get all appointments for this order."""
        appointments = obj.appointments.all()
        return AppointmentSerializer(appointments, many=True).data
    
    def get_coupon_used(self, obj):
        """Return coupon applied to this order (from CouponUsage) for display."""
        usage = obj.coupon_usages.select_related('coupon').first()
        if not usage:
            return None
        return {
            'code': usage.coupon.code,
            'discount_amount': str(usage.discount_amount),
        }


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating orders (multi-service, guest checkout supported).
    """
    # Items (multiple services)
    items = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        min_length=1,
        help_text='List of order items: [{"service_id": 1, "quantity": 1, "staff_id": null}]'
    )
    
    # Scheduling
    scheduled_date = serializers.DateField(required=True)
    scheduled_time = serializers.TimeField(required=False, allow_null=True)
    
    # Customer (optional for guest orders)
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    
    # Guest customer information (if customer_id is not provided)
    guest_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    guest_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Guest address (for guest orders)
    address_line1 = serializers.CharField(max_length=255, required=True)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=True)
    postcode = serializers.CharField(max_length=20, required=True)
    country = serializers.CharField(max_length=100, default='United Kingdom', required=False)
    
    # Additional information
    notes = serializers.CharField(required=False, allow_blank=True)
    
    # Coupon code (optional)
    coupon_code = serializers.CharField(required=False, allow_blank=True, help_text='Coupon code to apply')
    
    def validate_items(self, value):
        """Validate order items structure."""
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        
        for item in value:
            if 'service_id' not in item:
                raise serializers.ValidationError("Each item must have a service_id.")
            if 'quantity' not in item or item['quantity'] < 1:
                raise serializers.ValidationError("Each item must have quantity >= 1.")
        
        return value
    
    def validate(self, attrs):
        """Ensure either customer_id or guest information is provided."""
        customer_id = attrs.get('customer_id')
        guest_email = attrs.get('guest_email')
        
        if not customer_id and not guest_email:
            raise serializers.ValidationError({
                'customer_id': 'Either customer_id or guest_email must be provided.',
                'guest_email': 'Either customer_id or guest_email must be provided.'
            })
        
        return attrs


class OrderListSerializer(serializers.ModelSerializer):
    """
    Simplified order serializer for list views.
    """
    customer_name = serializers.SerializerMethodField()
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'customer_name', 'status', 'total_price',
                  'payment_status', 'scheduled_date', 'scheduled_time',
                  'can_cancel', 'can_reschedule', 'items_count', 'is_guest_order',
                  'created_at']
    
    def get_customer_name(self, obj):
        """Return customer name (account or guest)."""
        if obj.customer:
            return obj.customer.name
        return obj.guest_name or obj.guest_email


class ChangeRequestSerializer(serializers.ModelSerializer):
    """
    Change request serializer.
    """
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    reviewed_by_email = serializers.CharField(source='reviewed_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = ChangeRequest
        fields = [
            'id', 'order', 'order_number', 'requested_date', 'requested_time',
            'reason', 'status', 'reviewed_by', 'reviewed_by_email',
            'reviewed_at', 'review_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']
