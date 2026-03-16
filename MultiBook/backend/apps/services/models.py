"""
Services app models.
Service and Category models.
"""
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class Category(TimeStampedModel):
    """
    Service category (e.g., Cleaning Services, Maintenance, Green Spaces)
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Category name'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        help_text='URL-friendly category name (auto-generated)'
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Category description'
    )
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        help_text='Category image'
    )
    position = models.IntegerField(
        default=0,
        help_text='Display order (lower numbers appear first)'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Category is active and visible'
    )
    
    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        db_table = 'services_category'
        ordering = ['position', 'name']
        constraints = [
            models.CheckConstraint(
                check=models.Q(name__isnull=False) & ~models.Q(name=''),
                name='category_name_not_empty'
            ),
            models.CheckConstraint(
                check=models.Q(position__gte=0),
                name='category_valid_position'
            ),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Service(TimeStampedModel):
    """
    Service model (e.g., Window Cleaning, Grass Cutting, etc.)
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='services',
        help_text='Service category'
    )
    name = models.CharField(
        max_length=200,
        help_text='Service name'
    )
    slug = models.SlugField(
        max_length=200,
        blank=True,
        help_text='URL-friendly service name (auto-generated)'
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Service description'
    )
    
    # Service details
    duration = models.IntegerField(
        help_text='Service duration in minutes'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Base price for this service'
    )
    currency = models.CharField(
        max_length=3,
        default='GBP',
        help_text='Currency code (GBP, USD, etc.)'
    )
    
    # Visual
    image = models.ImageField(
        upload_to='services/',
        blank=True,
        null=True,
        help_text='Service image'
    )
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text='Color code for calendar/service display (hex)'
    )
    
    # Scheduling
    capacity = models.IntegerField(
        default=1,
        help_text='Number of customers that can book this service simultaneously'
    )
    padding_time = models.IntegerField(
        default=0,
        help_text='Padding time in minutes before next appointment'
    )
    
    # Display
    position = models.IntegerField(
        default=0,
        help_text='Display order (lower numbers appear first)'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Service is active and available for booking'
    )

    # Add-ons (e.g. [{"name": "Inside windows", "price": "10.00"}, ...])
    extras = models.JSONField(
        default=list,
        blank=True,
        help_text='Optional extras/add-ons: list of {name, price (string or number), description?}'
    )

    # Staff-created services require admin/manager approval before visible to customers
    APPROVAL_CHOICES = [
        ('approved', 'Approved'),
        ('pending_approval', 'Pending approval'),
    ]
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default='approved',
        help_text='Approved = visible to customers; Pending = only after admin/manager approval'
    )
    created_by_staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        related_name='services_created',
        null=True,
        blank=True,
        help_text='Staff who created this service (requires approval if set)'
    )

    class Meta:
        verbose_name = 'service'
        verbose_name_plural = 'services'
        db_table = 'services_service'
        ordering = ['position', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['slug']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(name__isnull=False) & ~models.Q(name=''),
                name='service_name_not_empty'
            ),
            models.CheckConstraint(
                check=models.Q(duration__gt=0),
                name='service_valid_duration'
            ),
            models.CheckConstraint(
                check=models.Q(price__gt=0),
                name='service_valid_price'
            ),
            models.CheckConstraint(
                check=models.Q(capacity__gt=0),
                name='service_valid_capacity'
            ),
            models.CheckConstraint(
                check=models.Q(padding_time__gte=0),
                name='service_valid_padding_time'
            ),
            models.CheckConstraint(
                check=models.Q(approval_status__in=['approved', 'pending_approval']),
                name='service_valid_approval_status'
            ),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
