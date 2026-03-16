"""
Staff app models.
Staff, StaffSchedule, StaffService, and StaffArea models.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel

User = get_user_model()

# Note: Service import removed to avoid circular imports
# We use string references 'services.Service' for ForeignKeys instead


class Staff(TimeStampedModel):
    """
    Staff member model.
    Can be linked to a User account (for staff portal access) or standalone.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='staff_profile',
        null=True,
        blank=True,
        limit_choices_to={'role': 'staff'},
        help_text='Staff user account (optional - for portal access)'
    )
    name = models.CharField(
        max_length=200,
        help_text='Staff member full name'
    )
    email = models.EmailField(
        help_text='Staff email address'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Staff phone number (UK format)'
    )
    photo = models.ImageField(
        upload_to='staff/',
        blank=True,
        null=True,
        help_text='Staff photo'
    )
    bio = models.TextField(
        blank=True,
        null=True,
        help_text='Staff biography/description'
    )
    
    # Service assignments
    services = models.ManyToManyField(
        'services.Service',
        related_name='staff_members',
        blank=True,
        through='StaffService',
        help_text='Services this staff member can perform'
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text='Staff member is active and available for booking'
    )
    
    class Meta:
        verbose_name = 'staff member'
        verbose_name_plural = 'staff members'
        db_table = 'staff_staff'
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'email']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(name__isnull=False) & ~models.Q(name=''),
                name='staff_name_not_empty'
            ),
            models.CheckConstraint(
                check=models.Q(email__isnull=False) & ~models.Q(email=''),
                name='staff_email_not_empty'
            ),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Ensure user role is 'staff' if user is linked
        if self.user and self.user.role != 'staff':
            self.user.role = 'staff'
            self.user.save()
        super().save(*args, **kwargs)


class StaffSchedule(TimeStampedModel):
    """
    Staff weekly schedule.
    Defines working hours for each day of the week (0=Monday, 6=Sunday)
    """
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text='Staff member'
    )
    day_of_week = models.IntegerField(
        choices=DAY_CHOICES,
        help_text='Day of week (0=Monday, 6=Sunday)'
    )
    start_time = models.TimeField(
        help_text='Work start time'
    )
    end_time = models.TimeField(
        help_text='Work end time'
    )
    breaks = models.JSONField(
        default=list,
        blank=True,
        help_text='Break periods (JSON array): [{"start": "12:00", "end": "13:00"}]'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='This schedule entry is active'
    )
    
    class Meta:
        verbose_name = 'staff schedule'
        verbose_name_plural = 'staff schedules'
        db_table = 'staff_staffschedule'
        unique_together = [['staff', 'day_of_week']]
        ordering = ['staff', 'day_of_week']
        constraints = [
            models.CheckConstraint(
                check=models.Q(day_of_week__gte=0) & models.Q(day_of_week__lte=6),
                name='staffschedule_valid_day'
            ),
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F('start_time')),
                name='staffschedule_end_after_start'
            ),
        ]
    
    def __str__(self):
        return f"{self.staff.name} - {self.get_day_of_week_display()} ({self.start_time} - {self.end_time})"


class StaffService(TimeStampedModel):
    """
    Staff-Service relationship with overrides.
    Allows different pricing/duration per staff member for the same service.
    """
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name='staff_services',
        help_text='Staff member'
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='staff_services',
        help_text='Service'
    )
    price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Custom price for this staff member (overrides service base price)'
    )
    duration_override = models.IntegerField(
        null=True,
        blank=True,
        help_text='Custom duration in minutes (overrides service base duration)'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='This staff-service assignment is active'
    )
    
    class Meta:
        verbose_name = 'staff service'
        verbose_name_plural = 'staff services'
        db_table = 'staff_staffservice'
        unique_together = [['staff', 'service']]
        ordering = ['staff', 'service']
        constraints = [
            models.CheckConstraint(
                check=models.Q(price_override__isnull=True) | models.Q(price_override__gt=0),
                name='staffservice_valid_price_override'
            ),
            models.CheckConstraint(
                check=models.Q(duration_override__isnull=True) | models.Q(duration_override__gt=0),
                name='staffservice_valid_duration_override'
            ),
        ]
    
    def __str__(self):
        return f"{self.staff.name} - {self.service.name}"


class StaffArea(TimeStampedModel):
    """
    Staff service area assignment.
    Defines postcode and radius (in miles) where staff member can provide services.
    If service is set, this area applies only when the customer is booking that service;
    if service is null, this area applies to all services this staff offers.
    UK uses miles, not kilometers.
    """
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name='service_areas',
        help_text='Staff member'
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='staff_areas',
        null=True,
        blank=True,
        help_text='If set, this area applies only to this service; null = all services'
    )
    postcode = models.CharField(
        max_length=20,
        help_text='Center postcode (e.g., SW1A 1AA)'
    )
    radius_miles = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Service radius in miles from center postcode'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='This service area is active'
    )
    
    class Meta:
        verbose_name = 'staff service area'
        verbose_name_plural = 'staff service areas'
        db_table = 'staff_staffarea'
        ordering = ['staff', 'postcode']
        indexes = [
            models.Index(fields=['postcode', 'is_active']),
            models.Index(fields=['staff', 'is_active']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(radius_miles__gt=0),
                name='staffarea_valid_radius'
            ),
            models.CheckConstraint(
                check=models.Q(postcode__isnull=False) & ~models.Q(postcode=''),
                name='staffarea_postcode_not_empty'
            ),
        ]
    
    def __str__(self):
        return f"{self.staff.name} - {self.postcode} ({self.radius_miles} miles)"
