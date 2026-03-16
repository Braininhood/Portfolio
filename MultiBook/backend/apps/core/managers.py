"""
Custom model managers.
"""
from django.db import models


class ActiveManager(models.Manager):
    """
    Manager that returns only active objects.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class GuestOrderManager(models.Manager):
    """
    Manager for guest orders.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_guest_order=True)


class ActiveSubscriptionManager(models.Manager):
    """
    Manager for active subscriptions.
    """
    def get_queryset(self):
        return super().get_queryset().filter(status='active')
