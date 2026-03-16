"""
Customers app models.
Customer and Address models.
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import TimeStampedModel

User = get_user_model()


class Customer(TimeStampedModel):
    """
    Customer model.
    Can be linked to a User account or standalone (for guest orders).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='customer_profile',
        null=True,
        blank=True,
        limit_choices_to={'role': 'customer'},
        help_text='Customer user account (optional - can be NULL for guest customers)'
    )
    name = models.CharField(
        max_length=200,
        help_text='Customer full name'
    )
    email = models.EmailField(
        help_text='Customer email address'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Customer phone number (UK format)'
    )
    
    # Address fields (primary address)
    address_line1 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Address line 1'
    )
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Address line 2'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='City'
    )
    postcode = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Postcode (UK format)'
    )
    country = models.CharField(
        max_length=100,
        default='United Kingdom',
        help_text='Country'
    )
    address_validated = models.BooleanField(
        default=False,
        help_text='Address has been validated via Google Places API'
    )
    
    # Additional information
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Internal notes about this customer'
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text='Customer tags (JSON array): ["vip", "repeat", etc.]'
    )
    
    class Meta:
        verbose_name = 'customer'
        verbose_name_plural = 'customers'
        db_table = 'customers_customer'
        ordering = ['name']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['postcode']),
            models.Index(fields=['user']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(name__isnull=False) & ~models.Q(name=''),
                name='customer_name_not_empty'
            ),
            models.CheckConstraint(
                check=models.Q(email__isnull=False) & ~models.Q(email=''),
                name='customer_email_not_empty'
            ),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Ensure user role is 'customer' if user is linked
        if self.user and self.user.role != 'customer':
            self.user.role = 'customer'
            self.user.save()
        super().save(*args, **kwargs)


class Address(TimeStampedModel):
    """
    Customer address model.
    Supports multiple addresses per customer (billing, service, etc.)
    """
    ADDRESS_TYPE_CHOICES = [
        ('billing', 'Billing Address'),
        ('service', 'Service Address'),
        ('other', 'Other'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='addresses',
        help_text='Customer'
    )
    type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPE_CHOICES,
        default='service',
        help_text='Address type: billing, service, or other'
    )
    
    # Address fields
    address_line1 = models.CharField(
        max_length=255,
        help_text='Address line 1'
    )
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Address line 2'
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
    
    is_default = models.BooleanField(
        default=False,
        help_text='Default address for this customer'
    )
    address_validated = models.BooleanField(
        default=False,
        help_text='Address has been validated via Google Places API'
    )
    
    class Meta:
        verbose_name = 'address'
        verbose_name_plural = 'addresses'
        db_table = 'customers_address'
        ordering = ['customer', '-is_default', 'type']
        constraints = [
            models.CheckConstraint(
                check=models.Q(type__in=['billing', 'service', 'other']),
                name='address_valid_type'
            ),
            models.CheckConstraint(
                check=models.Q(address_line1__isnull=False) & ~models.Q(address_line1=''),
                name='address_line1_not_empty'
            ),
            models.CheckConstraint(
                check=models.Q(city__isnull=False) & ~models.Q(city=''),
                name='address_city_not_empty'
            ),
            models.CheckConstraint(
                check=models.Q(postcode__isnull=False) & ~models.Q(postcode=''),
                name='address_postcode_not_empty'
            ),
        ]
    
    def __str__(self):
        return f"{self.customer.name} - {self.address_line1}, {self.postcode}"
