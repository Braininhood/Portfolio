"""
Orders app models.
Order and OrderItem models with guest checkout support.
Customers can request multiple services in one order (e.g., window cleaning + grass cutting).
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel
from apps.core.utils import generate_order_number, generate_tracking_token, can_cancel_or_reschedule

# Note: Service and Staff imports are needed but may cause circular imports
# We'll use string references for ForeignKeys instead


class Order(TimeStampedModel):
    """
    Order model with guest checkout support.
    Multi-service orders (e.g., window cleaning + grass cutting in one order).
    NO LOGIN/REGISTRATION REQUIRED - Perfect for elderly customers.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial Payment'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]
    
    # Customer relationship (nullable for guest orders)
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        related_name='orders',
        null=True,
        blank=True,
        help_text='Customer (NULL for guest orders, linked after login/registration)'
    )
    
    # Guest order fields (NO LOGIN REQUIRED)
    guest_email = models.EmailField(
        blank=True,
        null=True,
        help_text='Email for guest orders (required if customer is NULL)'
    )
    guest_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Name for guest orders'
    )
    guest_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Phone for guest orders'
    )
    order_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Unique order number (e.g., ORD-20240115-ABC123)'
    )
    tracking_token = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text='Unique tracking token for guest order access via email link'
    )
    is_guest_order = models.BooleanField(
        default=False,
        help_text='Flag for guest orders (no account required)'
    )
    account_linked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When guest order was linked to customer account'
    )
    
    # Order status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Order status'
    )
    
    # Pricing and payment
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Total order price'
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
    
    # Scheduling
    scheduled_date = models.DateField(
        help_text='Preferred service date'
    )
    scheduled_time = models.TimeField(
        null=True,
        blank=True,
        help_text='Preferred service time (optional)'
    )
    
    # Cancellation policy (24-hour policy)
    cancellation_policy_hours = models.IntegerField(
        default=24,
        help_text='Cancellation policy hours (default: 24 hours before scheduled date/time)'
    )
    can_cancel = models.BooleanField(
        default=True,
        help_text='Can cancel this order (based on 24h policy)'
    )
    can_reschedule = models.BooleanField(
        default=True,
        help_text='Can reschedule this order (based on 24h policy)'
    )
    cancellation_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Deadline for cancellation/rescheduling (24 hours before scheduled date/time)'
    )
    
    # Guest address (for guest orders)
    address_line1 = models.CharField(
        max_length=255,
        help_text='Service address line 1'
    )
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Service address line 2'
    )
    city = models.CharField(
        max_length=100,
        help_text='City'
    )
    postcode = models.CharField(
        max_length=20,
        help_text='Postcode (UK format)'
    )
    country = models.CharField(
        max_length=100,
        default='United Kingdom',
        help_text='Country'
    )
    
    # Additional information
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Customer notes or special instructions'
    )
    
    class Meta:
        verbose_name = 'order'
        verbose_name_plural = 'orders'
        db_table = 'orders_order'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['tracking_token']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['is_guest_order', 'guest_email']),
            models.Index(fields=['status', 'scheduled_date']),
            models.Index(fields=['postcode']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']),
                name='order_valid_status'
            ),
            models.CheckConstraint(
                check=models.Q(payment_status__in=['pending', 'partial', 'paid', 'refunded']),
                name='order_valid_payment_status'
            ),
            models.CheckConstraint(
                check=models.Q(total_price__gte=0),
                name='order_valid_total_price'
            ),
            models.CheckConstraint(
                check=models.Q(deposit_paid__gte=0),
                name='order_valid_deposit'
            ),
            models.CheckConstraint(
                check=models.Q(cancellation_policy_hours__gt=0),
                name='order_valid_policy_hours'
            ),
            models.CheckConstraint(
                check=models.Q(order_number__isnull=False) & ~models.Q(order_number=''),
                name='order_number_not_empty'
            ),
            models.CheckConstraint(
                check=models.Q(tracking_token__isnull=False) & ~models.Q(tracking_token=''),
                name='order_tracking_token_not_empty'
            ),
            # Guest orders require guest_email
            models.CheckConstraint(
                check=models.Q(customer__isnull=False) | (models.Q(guest_email__isnull=False) & ~models.Q(guest_email='')),
                name='order_has_customer_or_guest_email'
            ),
        ]
    
    def __str__(self):
        customer_name = self.customer.name if self.customer else (self.guest_name or self.guest_email)
        return f"{self.order_number} - {customer_name}"
    
    def save(self, *args, **kwargs):
        # Generate order number if not set
        if not self.order_number:
            self.order_number = generate_order_number()
        
        # Generate tracking token if not set
        if not self.tracking_token:
            self.tracking_token = generate_tracking_token()
        
        # Set guest order flag
        if not self.customer and self.guest_email:
            self.is_guest_order = True
        
        # Always recalculate cancellation deadline and flags (in case scheduled date/time changed)
        if self.scheduled_date and self.scheduled_time:
            from django.utils import timezone
            from datetime import datetime, timedelta
            scheduled_datetime = timezone.make_aware(
                datetime.combine(self.scheduled_date, self.scheduled_time)
            )
            can_cancel_val, can_reschedule_val, deadline = can_cancel_or_reschedule(
                scheduled_datetime,
                self.cancellation_policy_hours
            )
            self.can_cancel = can_cancel_val
            self.can_reschedule = can_reschedule_val
            self.cancellation_deadline = deadline
        elif self.status in ['completed', 'cancelled']:
            # If order is completed or cancelled, can't cancel/reschedule
            self.can_cancel = False
            self.can_reschedule = False
        
        super().save(*args, **kwargs)


class ChangeRequest(TimeStampedModel):
    """
    Order change request model for tracking and approval workflow.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='change_requests',
        help_text='Order for this change request'
    )
    requested_date = models.DateField(
        help_text='Requested new date'
    )
    requested_time = models.TimeField(
        null=True,
        blank=True,
        help_text='Requested new time (optional)'
    )
    reason = models.TextField(
        blank=True,
        null=True,
        help_text='Reason for change request'
    )
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
        related_name='reviewed_change_requests',
        help_text='User who reviewed this change request'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this change request was reviewed'
    )
    review_notes = models.TextField(
        blank=True,
        null=True,
        help_text='Admin review notes'
    )
    
    class Meta:
        verbose_name = 'change request'
        verbose_name_plural = 'change requests'
        db_table = 'orders_changerequest'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['pending', 'approved', 'rejected']),
                name='changerequest_valid_status'
            ),
            models.CheckConstraint(
                check=models.Q(requested_date__isnull=False),
                name='changerequest_has_date'
            ),
        ]
    
    def __str__(self):
        return f"Change request for {self.order.order_number} - {self.status}"


class OrderItem(TimeStampedModel):
    """
    Order Item model.
    Each service in a multi-service order.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Parent order'
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='order_items',
        help_text='Service for this order item'
    )
    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        related_name='order_items',
        null=True,
        blank=True,
        help_text='Assigned staff member (optional - can be assigned later)'
    )
    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Quantity of this service'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Price per unit'
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Total price for this item (quantity * unit_price)'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        related_name='order_items',
        null=True,
        blank=True,
        help_text='Appointment created for this order item (created when order is confirmed)'
    )
    status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        default='pending',
        help_text='Order item status'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Item-specific notes'
    )
    
    class Meta:
        verbose_name = 'order item'
        verbose_name_plural = 'order items'
        db_table = 'orders_orderitem'
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['service']),
            models.Index(fields=['staff']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=1),
                name='orderitem_valid_quantity'
            ),
            models.CheckConstraint(
                check=models.Q(unit_price__gt=0),
                name='orderitem_valid_unit_price'
            ),
            models.CheckConstraint(
                check=models.Q(total_price__gte=0),
                name='orderitem_valid_total_price'
            ),
            models.CheckConstraint(
                check=models.Q(status__in=['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']),
                name='orderitem_valid_status'
            ),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.service.name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        if self.unit_price and self.quantity:
            self.total_price = self.unit_price * self.quantity
        
        super().save(*args, **kwargs)
