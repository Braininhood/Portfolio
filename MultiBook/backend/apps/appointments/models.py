"""
Appointments app models.
Appointment and CustomerAppointment models with calendar sync support.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel

User = get_user_model()

# Note: Service and Staff imports are needed but may cause circular imports
# We'll use string references for ForeignKeys instead


class Appointment(TimeStampedModel):
    """
    Appointment model with calendar sync support.
    Can be a single appointment, part of a subscription, or part of an order.
    """
    APPOINTMENT_TYPE_CHOICES = [
        ('single', 'Single Appointment'),
        ('subscription', 'Subscription Appointment'),
        ('order_item', 'Order Item Appointment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
        related_name='appointments',
        help_text='Staff member assigned to this appointment'
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='appointments',
        help_text='Service being performed'
    )
    
    # Date and time
    start_time = models.DateTimeField(
        help_text='Appointment start date and time'
    )
    end_time = models.DateTimeField(
        help_text='Appointment end date and time'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Appointment status'
    )
    appointment_type = models.CharField(
        max_length=20,
        choices=APPOINTMENT_TYPE_CHOICES,
        default='single',
        help_text='Appointment type: single, subscription, or order_item'
    )
    
    # Relationships (nullable - for single appointments)
    subscription = models.ForeignKey(
        'subscriptions.Subscription',
        on_delete=models.SET_NULL,
        related_name='appointments',
        null=True,
        blank=True,
        help_text='Subscription this appointment belongs to (if applicable)'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        related_name='appointments',
        null=True,
        blank=True,
        help_text='Order this appointment belongs to (if applicable)'
    )
    
    # Calendar Sync Fields (JSON storage for multiple providers)
    calendar_event_id = models.JSONField(
        default=dict,
        blank=True,
        help_text='Calendar event IDs for each provider (JSON): {"google": "event_id", "outlook": "event_id", "apple": "event_id"}'
    )
    calendar_synced_to = models.JSONField(
        default=list,
        blank=True,
        help_text='List of calendars this appointment is synced to (JSON array): ["google", "outlook", "apple"]'
    )
    
    # Additional information
    internal_notes = models.TextField(
        blank=True,
        null=True,
        help_text='Internal notes for staff/admin'
    )
    location_notes = models.TextField(
        blank=True,
        null=True,
        help_text='Location-specific notes (gate codes, parking, etc.)'
    )
    completion_photos = models.JSONField(
        default=list,
        blank=True,
        help_text='Job completion photos in Supabase Storage: list of {url, path, uploaded_at}'
    )

    class Meta:
        verbose_name = 'appointment'
        verbose_name_plural = 'appointments'
        db_table = 'appointments_appointment'
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['staff', 'start_time']),
            models.Index(fields=['status', 'start_time']),
            models.Index(fields=['appointment_type']),
            models.Index(fields=['subscription']),
            models.Index(fields=['order']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['pending', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show']),
                name='appointment_valid_status'
            ),
            models.CheckConstraint(
                check=models.Q(appointment_type__in=['single', 'subscription', 'order_item']),
                name='appointment_valid_type'
            ),
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F('start_time')),
                name='appointment_end_after_start'
            ),
        ]
    
    def __str__(self):
        return f"{self.service.name} - {self.staff.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"


class CustomerAppointment(TimeStampedModel):
    """
    Customer-Appointment relationship.
    Links customer to appointment with booking details, payment, and cancellation policy.
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial Payment'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]
    
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='appointments',
        help_text='Customer who booked this appointment'
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='customer_booking',
        help_text='Appointment'
    )
    
    # Booking details
    number_of_persons = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Number of persons'
    )
    extras = models.JSONField(
        default=list,
        blank=True,
        help_text='Additional services/extras (JSON array)'
    )
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text='Custom fields filled during booking (JSON)'
    )
    
    # Pricing and payment
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Total price for this appointment'
    )
    deposit_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Deposit amount paid'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        help_text='Payment status'
    )
    
    # Cancellation policy (24-hour policy)
    cancellation_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text='Unique token for cancellation/rescheduling (for guest orders)'
    )
    cancellation_policy_hours = models.IntegerField(
        default=24,
        help_text='Cancellation policy hours (default: 24 hours before appointment)'
    )
    cancellation_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Deadline for cancellation (24 hours before appointment start time)'
    )
    can_cancel = models.BooleanField(
        default=True,
        help_text='Can cancel this appointment (based on 24h policy)'
    )
    can_reschedule = models.BooleanField(
        default=True,
        help_text='Can reschedule this appointment (based on 24h policy)'
    )
    
    class Meta:
        verbose_name = 'customer appointment'
        verbose_name_plural = 'customer appointments'
        db_table = 'appointments_customerappointment'
        ordering = ['appointment__start_time']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['cancellation_token']),
            models.Index(fields=['can_cancel', 'can_reschedule']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(number_of_persons__gte=1),
                name='customerappointment_valid_persons'
            ),
            models.CheckConstraint(
                check=models.Q(total_price__gte=0),
                name='customerappointment_valid_total_price'
            ),
            models.CheckConstraint(
                check=models.Q(deposit_paid__gte=0),
                name='customerappointment_valid_deposit'
            ),
            models.CheckConstraint(
                check=models.Q(payment_status__in=['pending', 'partial', 'paid', 'refunded']),
                name='customerappointment_valid_payment_status'
            ),
            models.CheckConstraint(
                check=models.Q(cancellation_policy_hours__gt=0),
                name='customerappointment_valid_policy_hours'
            ),
        ]
    
    def __str__(self):
        return f"{self.customer.name} - {self.appointment.service.name} - {self.appointment.start_time.strftime('%Y-%m-%d')}"
