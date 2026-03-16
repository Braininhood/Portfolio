"""
Appointments app serializers.
Appointment and CustomerAppointment serializers with calendar sync support.
"""
from rest_framework import serializers
from .models import Appointment, CustomerAppointment
from apps.staff.serializers import StaffListSerializer
from apps.services.serializers import ServiceListSerializer
from apps.customers.serializers import CustomerSerializer, CustomerListSerializer


class CustomerBookingSummarySerializer(serializers.ModelSerializer):
    """Minimal customer booking info for inclusion in Appointment (can_cancel, can_reschedule, price, customer name)."""
    customer = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomerAppointment
        fields = [
            'id', 'customer', 'total_price', 'deposit_paid', 'payment_status',
            'can_cancel', 'can_reschedule', 'cancellation_deadline', 'cancellation_policy_hours',
        ]
        read_only_fields = ['id', 'total_price', 'deposit_paid', 'payment_status',
            'can_cancel', 'can_reschedule', 'cancellation_deadline', 'cancellation_policy_hours']

    def get_customer(self, obj):
        if not obj.customer_id:
            return None
        return {'id': obj.customer.id, 'name': obj.customer.name, 'email': getattr(obj.customer, 'email', '') or ''}


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Appointment serializer with calendar sync fields and optional customer_booking.
    """
    staff = StaffListSerializer(read_only=True)
    staff_id = serializers.IntegerField(write_only=True, required=True)
    service = ServiceListSerializer(read_only=True)
    service_id = serializers.IntegerField(write_only=True, required=True)
    subscription_number = serializers.CharField(source='subscription.subscription_number', read_only=True, allow_null=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True, allow_null=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True, allow_null=True)
    subscription_id = serializers.IntegerField(source='subscription.id', read_only=True, allow_null=True)
    customer_booking = CustomerBookingSummarySerializer(read_only=True, allow_null=True)

    class Meta:
        model = Appointment
        fields = ['id', 'staff', 'staff_id', 'service', 'service_id',
                  'start_time', 'end_time', 'status', 'appointment_type',
                  'subscription', 'subscription_number', 'subscription_id',
                  'order', 'order_number', 'order_id',
                  'customer_booking',
                  'calendar_event_id', 'calendar_synced_to', 'internal_notes',
                  'location_notes', 'completion_photos',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'calendar_event_id': {'required': False, 'allow_null': True},
            'calendar_synced_to': {'required': False, 'allow_null': True},
        }


class CustomerAppointmentSerializer(serializers.ModelSerializer):
    """
    Customer-Appointment relationship serializer with booking details.
    """
    customer = CustomerListSerializer(read_only=True)
    customer_id = serializers.IntegerField(write_only=True, required=True)
    appointment = AppointmentSerializer(read_only=True)
    appointment_id = serializers.IntegerField(write_only=True, required=True)
    
    class Meta:
        model = CustomerAppointment
        fields = ['id', 'customer', 'customer_id', 'appointment', 'appointment_id',
                  'number_of_persons', 'extras', 'custom_fields', 'total_price',
                  'deposit_paid', 'payment_status', 'cancellation_token',
                  'cancellation_policy_hours', 'cancellation_deadline',
                  'can_cancel', 'can_reschedule', 'created_at', 'updated_at']
        read_only_fields = ['id', 'cancellation_deadline', 'can_cancel', 'can_reschedule',
                           'created_at', 'updated_at']


class AppointmentCreateSerializer(serializers.Serializer):
    """
    Serializer for creating appointments (used in booking flow).
    Supports both authenticated and guest customers.
    """
    # Service and Staff
    service_id = serializers.IntegerField(required=True)
    staff_id = serializers.IntegerField(required=False, allow_null=True)
    
    # Date and Time
    start_time = serializers.DateTimeField(required=True)
    end_time = serializers.DateTimeField(required=False)  # Can be calculated from service duration
    
    # Customer information (for guest checkout)
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    guest_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    guest_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Booking details
    number_of_persons = serializers.IntegerField(default=1, required=False)
    extras = serializers.ListField(required=False, allow_empty=True)
    custom_fields = serializers.DictField(required=False, allow_empty=True)
    notes = serializers.CharField(required=False, allow_blank=True)
