"""
Subscriptions app serializers.
Subscription and SubscriptionAppointment serializers with guest checkout support.
"""
from rest_framework import serializers
from .models import Subscription, SubscriptionAppointment
from apps.services.serializers import ServiceListSerializer
from apps.staff.serializers import StaffListSerializer
from apps.customers.serializers import CustomerListSerializer, GuestCustomerSerializer
from apps.appointments.serializers import AppointmentSerializer


class SubscriptionAppointmentSerializer(serializers.ModelSerializer):
    """
    Subscription Appointment serializer.
    """
    appointment = AppointmentSerializer(read_only=True)
    appointment_id = serializers.IntegerField(write_only=True, required=True)
    
    class Meta:
        model = SubscriptionAppointment
        fields = ['id', 'subscription', 'appointment', 'appointment_id',
                  'sequence_number', 'scheduled_date', 'status',
                  'can_cancel', 'can_reschedule', 'cancellation_deadline',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'can_cancel', 'can_reschedule', 'cancellation_deadline',
                             'created_at', 'updated_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Subscription serializer with guest checkout support.
    """
    service = ServiceListSerializer(read_only=True)
    service_id = serializers.IntegerField(write_only=True, required=True)
    staff = StaffListSerializer(read_only=True, allow_null=True)
    staff_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    customer = CustomerListSerializer(read_only=True, allow_null=True)
    customer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    appointments = SubscriptionAppointmentSerializer(many=True, read_only=True, source='subscription_appointments')
    
    class Meta:
        model = Subscription
        fields = ['id', 'customer', 'customer_id', 'guest_email', 'guest_name', 'guest_phone',
                  'subscription_number', 'tracking_token', 'is_guest_subscription',
                  'account_linked_at', 'service', 'service_id', 'staff', 'staff_id',
                  'frequency', 'duration_months', 'start_date', 'end_date',
                  'next_appointment_date', 'status', 'total_appointments',
                  'completed_appointments', 'price_per_appointment', 'total_price',
                  'payment_status', 'cancellation_policy_hours',
                  'address_line1', 'address_line2', 'city', 'postcode', 'country',
                  'appointments', 'created_at', 'updated_at']
        read_only_fields = ['id', 'subscription_number', 'tracking_token',
                             'account_linked_at', 'total_appointments',
                             'created_at', 'updated_at']
        extra_kwargs = {
            'guest_email': {'required': False, 'allow_blank': True},
            'guest_name': {'required': False, 'allow_blank': True},
            'guest_phone': {'required': False, 'allow_blank': True},
        }


class SubscriptionCreateSerializer(serializers.Serializer):
    """
    Serializer for creating subscriptions (supports guest checkout).
    """
    # Service and Staff
    service_id = serializers.IntegerField(required=True)
    staff_id = serializers.IntegerField(required=False, allow_null=True)
    
    # Subscription details
    frequency = serializers.ChoiceField(choices=['weekly', 'biweekly', 'monthly'], required=True)
    duration_months = serializers.IntegerField(required=True, min_value=1)
    start_date = serializers.DateField(required=True)
    price_per_appointment = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    
    # Customer (optional for guest subscriptions)
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    
    # Guest customer information (if customer_id is not provided)
    guest_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    guest_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Guest address (for guest subscriptions)
    address_line1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postcode = serializers.CharField(max_length=20, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, default='United Kingdom', required=False)
    
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


class SubscriptionListSerializer(serializers.ModelSerializer):
    """
    Simplified subscription serializer for list views.
    """
    service_name = serializers.CharField(source='service.name', read_only=True)
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = ['id', 'subscription_number', 'customer_name', 'service_name',
                  'frequency', 'duration_months', 'start_date', 'end_date',
                  'status', 'total_appointments', 'completed_appointments',
                  'total_price', 'payment_status', 'is_guest_subscription']
    
    def get_customer_name(self, obj):
        """Return customer name (account or guest)."""
        if obj.customer:
            return obj.customer.name
        return obj.guest_name or obj.guest_email
