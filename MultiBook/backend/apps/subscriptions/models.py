"""
Subscriptions app models.
Subscription and SubscriptionAppointment models with guest checkout support.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel
from apps.core.utils import generate_subscription_number, generate_tracking_token, can_cancel_or_reschedule

# Note: Service and Staff imports are needed but may cause circular imports
# We'll use string references for ForeignKeys instead


class Subscription(TimeStampedModel):
    """
    Subscription model with guest checkout support.
    Customers can subscribe to recurring services (e.g., weekly cleaning for 3 months).
    """
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial Payment'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]
    
    # Customer relationship (nullable for guest subscriptions)
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        related_name='subscriptions',
        null=True,
        blank=True,
        help_text='Customer (NULL for guest subscriptions, linked after login/registration)'
    )
    
    # Guest subscription fields (NO LOGIN REQUIRED)
    guest_email = models.EmailField(
        blank=True,
        null=True,
        help_text='Email for guest subscriptions (required if customer is NULL)'
    )
    guest_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Name for guest subscriptions'
    )
    guest_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Phone for guest subscriptions'
    )
    subscription_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Unique subscription number (e.g., SUB-20240115-ABC123)'
    )
    tracking_token = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text='Unique tracking token for guest subscription access via email link'
    )
    is_guest_subscription = models.BooleanField(
        default=False,
        help_text='Flag for guest subscriptions (no account required)'
    )
    account_linked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When guest subscription was linked to customer account'
    )
    
    # Subscription details
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        help_text='Service for subscription'
    )
    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        related_name='subscriptions',
        null=True,
        blank=True,
        help_text='Preferred staff member (optional)'
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        help_text='Subscription frequency: weekly, biweekly, or monthly'
    )
    duration_months = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Subscription duration in months (1, 2, 3, 6, or 12)'
    )
    
    # Dates
    start_date = models.DateField(
        help_text='Subscription start date'
    )
    end_date = models.DateField(
        help_text='Subscription end date (calculated)'
    )
    next_appointment_date = models.DateField(
        null=True,
        blank=True,
        help_text='Next scheduled appointment date'
    )
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text='Subscription status'
    )
    total_appointments = models.IntegerField(
        default=0,
        help_text='Total number of appointments in this subscription (calculated)'
    )
    completed_appointments = models.IntegerField(
        default=0,
        help_text='Number of completed appointments'
    )
    
    # Pricing
    price_per_appointment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Price per appointment'
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Total subscription price'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        help_text='Payment status'
    )
    
    # Cancellation policy
    cancellation_policy_hours = models.IntegerField(
        default=24,
        help_text='Cancellation policy hours (default: 24 hours before appointment)'
    )
    
    # Guest address (for guest subscriptions)
    address_line1 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Guest address line 1'
    )
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Guest address line 2'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Guest city'
    )
    postcode = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Guest postcode'
    )
    country = models.CharField(
        max_length=100,
        default='United Kingdom',
        blank=True,
        null=True,
        help_text='Guest country'
    )
    
    class Meta:
        verbose_name = 'subscription'
        verbose_name_plural = 'subscriptions'
        db_table = 'subscriptions_subscription'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription_number']),
            models.Index(fields=['tracking_token']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['is_guest_subscription', 'guest_email']),
            models.Index(fields=['status', 'next_appointment_date']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(frequency__in=['weekly', 'biweekly', 'monthly']),
                name='subscription_valid_frequency'
            ),
            models.CheckConstraint(
                check=models.Q(status__in=['active', 'paused', 'cancelled', 'completed']),
                name='subscription_valid_status'
            ),
            models.CheckConstraint(
                check=models.Q(payment_status__in=['pending', 'partial', 'paid', 'refunded']),
                name='subscription_valid_payment_status'
            ),
            models.CheckConstraint(
                check=models.Q(duration_months__gte=1),
                name='subscription_valid_duration'
            ),
            models.CheckConstraint(
                check=models.Q(total_appointments__gte=0),
                name='subscription_valid_total_appointments'
            ),
            models.CheckConstraint(
                check=models.Q(completed_appointments__gte=0),
                name='subscription_valid_completed_appointments'
            ),
            models.CheckConstraint(
                check=models.Q(completed_appointments__lte=models.F('total_appointments')),
                name='subscription_completed_not_exceeds_total'
            ),
            models.CheckConstraint(
                check=models.Q(price_per_appointment__gt=0),
                name='subscription_valid_price_per_appointment'
            ),
            models.CheckConstraint(
                check=models.Q(total_price__gte=0),
                name='subscription_valid_total_price'
            ),
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F('start_date')),
                name='subscription_end_after_start'
            ),
            models.CheckConstraint(
                check=models.Q(subscription_number__isnull=False) & ~models.Q(subscription_number=''),
                name='subscription_number_not_empty'
            ),
            models.CheckConstraint(
                check=models.Q(tracking_token__isnull=False) & ~models.Q(tracking_token=''),
                name='subscription_tracking_token_not_empty'
            ),
            models.CheckConstraint(
                check=models.Q(customer__isnull=False) | (models.Q(guest_email__isnull=False) & ~models.Q(guest_email='')),
                name='subscription_has_customer_or_guest_email'
            ),
        ]
    
    def __str__(self):
        customer_name = self.customer.name if self.customer else (self.guest_name or self.guest_email)
        return f"{customer_name} - {self.service.name} ({self.frequency})"
    
    def save(self, *args, **kwargs):
        # Generate subscription number if not set
        if not self.subscription_number:
            self.subscription_number = generate_subscription_number()
        
        # Generate tracking token if not set
        if not self.tracking_token:
            self.tracking_token = generate_tracking_token()
        
        # Set guest subscription flag
        if not self.customer and self.guest_email:
            self.is_guest_subscription = True
        
        super().save(*args, **kwargs)


class SubscriptionAppointment(TimeStampedModel):
    """
    Subscription Appointment relationship.
    Links individual appointments to their parent subscription.
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('skipped', 'Skipped'),
    ]
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='subscription_appointments',
        help_text='Parent subscription'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='subscription_appointments',
        help_text='Appointment'
    )
    sequence_number = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Sequence number in subscription (1, 2, 3, etc.)'
    )
    scheduled_date = models.DateField(
        help_text='Scheduled date for this appointment'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        help_text='Subscription appointment status'
    )
    
    # Cancellation policy (24-hour policy)
    can_cancel = models.BooleanField(
        default=True,
        help_text='Can cancel this subscription appointment (based on 24h policy)'
    )
    can_reschedule = models.BooleanField(
        default=True,
        help_text='Can request change of date/time (based on 24h policy)'
    )
    cancellation_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Deadline for cancellation (24 hours before appointment start time)'
    )
    
    class Meta:
        verbose_name = 'subscription appointment'
        verbose_name_plural = 'subscription appointments'
        db_table = 'subscriptions_subscriptionappointment'
        unique_together = [['subscription', 'appointment']]
        ordering = ['subscription', 'sequence_number']
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['scheduled', 'completed', 'cancelled', 'skipped']),
                name='subscriptionappointment_valid_status'
            ),
            models.CheckConstraint(
                check=models.Q(sequence_number__gte=1),
                name='subscriptionappointment_valid_sequence'
            ),
        ]
    
    def __str__(self):
        return f"{self.subscription.subscription_number} - Appointment #{self.sequence_number} - {self.scheduled_date}"
    
    def save(self, *args, **kwargs):
        # Calculate cancellation/reschedule deadline based on appointment start time
        if self.appointment and self.appointment.start_time:
            can_cancel_val, can_reschedule_val, deadline = can_cancel_or_reschedule(
                self.appointment.start_time,
                self.subscription.cancellation_policy_hours
            )
            self.can_cancel = can_cancel_val
            self.can_reschedule = can_reschedule_val
            self.cancellation_deadline = deadline
        
        super().save(*args, **kwargs)


class SubscriptionAppointmentChangeRequest(TimeStampedModel):
    """
    Change request for a single subscription visit (reschedule date/time).
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    subscription_appointment = models.ForeignKey(
        SubscriptionAppointment,
        on_delete=models.CASCADE,
        related_name='change_requests',
        help_text='Subscription visit to reschedule'
    )
    requested_date = models.DateField(help_text='Requested new date')
    requested_time = models.TimeField(null=True, blank=True, help_text='Requested new time')
    reason = models.TextField(blank=True, null=True, help_text='Reason for change')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Change request status'
    )
    reviewed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_subscription_change_requests',
        help_text='User who reviewed this request'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'subscriptions_subscriptionappointmentchangerequest'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['pending', 'approved', 'rejected']),
                name='subscriptionappointmentchangerequest_valid_status'
            ),
            models.CheckConstraint(
                check=models.Q(requested_date__isnull=False),
                name='subscriptionappointmentchangerequest_has_date'
            ),
        ]

    def __str__(self):
        return f"Change request for subscription visit #{self.subscription_appointment.sequence_number} - {self.status}"
