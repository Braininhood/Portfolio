"""
Customers app URLs.
Protected: /api/cus/ (customer endpoints)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'customers'

router = DefaultRouter()
router.register(r'profile', views.CustomerViewSet, basename='customer-profile')
router.register(r'addresses', views.AddressViewSet, basename='address')

urlpatterns = router.urls

# Note: Admin/Manager endpoints will be configured separately
# This file handles customer-specific endpoints (/api/cus/)
