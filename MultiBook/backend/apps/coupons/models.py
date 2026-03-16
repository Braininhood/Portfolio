"""
Coupons app models.
Coupon model with validation, usage tracking, expiry management, and service restrictions.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.core.models import TimeStampedModel


class Coupon(TimeStampedModel):
    """
    Coupon model for discounts.
    Supports percentage and fixed amount discounts.
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    ]
    
    # Coupon identification
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Coupon code (e.g., SAVE20, WELCOME10)'
    )
    name = models.CharField(
        max_length=200,
        help_text='Coupon name/description'
    )
    
    # Discount details
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        help_text='Discount type: percentage or fixed amount'
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Discount value (percentage: 0-100, fixed: amount in GBP)'
    )
    
    # Usage limits
    max_uses = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='Maximum number of times this coupon can be used (NULL = unlimited)'
    )
    max_uses_per_customer = models.IntegerField(
        null=True,
        blank=True,
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Maximum number of times a single customer can use this coupon (NULL = unlimited)'
    )
    used_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Number of times this coupon has been used'
    )
    
    # Expiry management
    valid_from = models.DateTimeField(
        help_text='Coupon valid from date/time'
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Coupon valid until date/time (NULL = no expiry)'
    )
    
    # Minimum order requirements
    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Minimum order amount required to use this coupon'
    )
    
    # Service restrictions
    applicable_services = models.ManyToManyField(
        'services.Service',
        blank=True,
        related_name='coupons',
        help_text='Services this coupon applies to (empty = all services)'
    )
    excluded_services = models.ManyToManyField(
        'services.Service',
        blank=True,
        related_name='excluded_coupons',
        help_text='Services this coupon does NOT apply to'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text='Coupon status'
    )
    
    # Additional information
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Coupon description/terms'
    )
    
    class Meta:
        verbose_name = 'coupon'
        verbose_name_plural = 'coupons'
        db_table = 'coupons_coupon'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status', 'valid_from', 'valid_until']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(discount_type__in=['percentage', 'fixed']),
                name='coupon_valid_discount_type'
            ),
            models.CheckConstraint(
                check=models.Q(status__in=['active', 'inactive', 'expired']),
                name='coupon_valid_status'
            ),
            models.CheckConstraint(
                check=models.Q(discount_value__gt=0),
                name='coupon_valid_discount_value'
            ),
            # Percentage discounts cannot exceed 100%
            models.CheckConstraint(
                check=models.Q(discount_type='fixed') | models.Q(discount_value__lte=100),
                name='coupon_percentage_max_100'
            ),
            models.CheckConstraint(
                check=models.Q(used_count__gte=0),
                name='coupon_valid_used_count'
            ),
            models.CheckConstraint(
                check=models.Q(max_uses__isnull=True) | models.Q(max_uses__gte=1),
                name='coupon_valid_max_uses'
            ),
            models.CheckConstraint(
                check=models.Q(max_uses_per_customer__isnull=True) | models.Q(max_uses_per_customer__gte=1),
                name='coupon_valid_max_uses_per_customer'
            ),
            models.CheckConstraint(
                check=models.Q(minimum_order_amount__gte=0),
                name='coupon_valid_minimum_order_amount'
            ),
            models.CheckConstraint(
                check=models.Q(code__isnull=False) & ~models.Q(code=''),
                name='coupon_code_not_empty'
            ),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def is_valid(self, customer=None, order_amount=0, service_ids=None):
        """
        Check if coupon is valid for use.
        
        Args:
            customer: Customer instance (optional, for per-customer limits)
            order_amount: Order total amount
            service_ids: List of service IDs in the order
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        from datetime import datetime
        
        # Check status
        if self.status != 'active':
            return False, 'Coupon is not active'
        
        # Check expiry
        now = timezone.now()
        if self.valid_from > now:
            return False, f'Coupon is not yet valid. Valid from {self.valid_from.strftime("%Y-%m-%d %H:%M")}'
        
        if self.valid_until and self.valid_until < now:
            return False, f'Coupon has expired. Expired on {self.valid_until.strftime("%Y-%m-%d %H:%M")}'
        
        # Check max uses
        if self.max_uses and self.used_count >= self.max_uses:
            return False, 'Coupon has reached maximum usage limit'
        
        # Check per-customer limit
        if customer and self.max_uses_per_customer:
            # Import here to avoid circular import
            customer_usage_count = self.usages.filter(customer=customer).count()
            if customer_usage_count >= self.max_uses_per_customer:
                return False, f'You have already used this coupon {customer_usage_count} time(s). Maximum allowed: {self.max_uses_per_customer}'
        
        # Check minimum order amount
        if order_amount < self.minimum_order_amount:
            return False, f'Minimum order amount of £{self.minimum_order_amount} required'
        
        # Check service restrictions
        if service_ids:
            # Check if any service is excluded
            if self.excluded_services.filter(id__in=service_ids).exists():
                return False, 'This coupon cannot be used with one or more selected services'
            
            # Check if coupon applies to specific services only
            if self.applicable_services.exists():
                if not self.applicable_services.filter(id__in=service_ids).exists():
                    return False, 'This coupon does not apply to the selected services'
        
        return True, ''
    
    def calculate_discount(self, order_amount):
        """
        Calculate discount amount for given order amount.
        
        Args:
            order_amount: Order total amount
        
        Returns:
            Discount amount
        """
        from decimal import Decimal
        
        if self.discount_type == 'percentage':
            discount = order_amount * (self.discount_value / Decimal('100'))
        else:  # fixed
            discount = min(self.discount_value, order_amount)  # Can't discount more than order amount
        
        return discount
    
    def save(self, *args, **kwargs):
        # Validate discount value based on type
        if self.discount_type == 'percentage':
            if self.discount_value > 100:
                raise ValueError('Percentage discount cannot exceed 100%')
        
        # Auto-update status based on expiry
        if self.valid_until and self.valid_until < timezone.now():
            self.status = 'expired'
        elif self.status == 'expired' and self.valid_until and self.valid_until >= timezone.now():
            self.status = 'active'
        
        super().save(*args, **kwargs)


class CouponUsage(TimeStampedModel):
    """
    Track coupon usage for analytics and per-customer limits.
    """
    coupon = models.ForeignKey(
        'coupons.Coupon',
        on_delete=models.CASCADE,
        related_name='usages',
        help_text='Coupon used'
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        related_name='coupon_usages',
        null=True,
        blank=True,
        help_text='Customer who used the coupon (NULL for guest usage)'
    )
    guest_email = models.EmailField(
        null=True,
        blank=True,
        help_text='Guest email if customer is NULL'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        related_name='coupon_usages',
        null=True,
        blank=True,
        help_text='Order where coupon was used'
    )
    subscription = models.ForeignKey(
        'subscriptions.Subscription',
        on_delete=models.SET_NULL,
        related_name='coupon_usages',
        null=True,
        blank=True,
        help_text='Subscription where coupon was used'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        related_name='coupon_usages',
        null=True,
        blank=True,
        help_text='Appointment where coupon was used'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Discount amount applied'
    )
    order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Order amount before discount'
    )
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Order amount after discount'
    )
    
    class Meta:
        verbose_name = 'coupon usage'
        verbose_name_plural = 'coupon usages'
        db_table = 'coupons_couponusage'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['coupon', 'customer']),
            models.Index(fields=['order']),
            models.Index(fields=['subscription']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(discount_amount__gte=0),
                name='couponusage_valid_discount_amount'
            ),
            models.CheckConstraint(
                check=models.Q(order_amount__gt=0),
                name='couponusage_valid_order_amount'
            ),
            models.CheckConstraint(
                check=models.Q(final_amount__gte=0),
                name='couponusage_valid_final_amount'
            ),
            models.CheckConstraint(
                check=models.Q(final_amount__lte=models.F('order_amount')),
                name='couponusage_final_not_exceeds_order'
            ),
            # Must have either customer or guest_email
            models.CheckConstraint(
                check=models.Q(customer__isnull=False) | (models.Q(guest_email__isnull=False) & ~models.Q(guest_email='')),
                name='couponusage_has_customer_or_guest_email'
            ),
        ]
    
    def __str__(self):
        customer_name = self.customer.name if self.customer else (self.guest_email or 'Guest')
        return f"{self.coupon.code} used by {customer_name} - £{self.discount_amount}"
