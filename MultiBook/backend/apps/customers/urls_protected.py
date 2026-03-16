"""
Customers app protected URLs.
Customer endpoints: /api/cus/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.appointments.views import AppointmentViewSet
from apps.subscriptions.views import SubscriptionViewSet
from apps.orders.views import OrderViewSet
from . import views

app_name = 'customers-protected'

router = DefaultRouter()
# Customer profile endpoints
router.register(r'profile', views.CustomerViewSet, basename='customer-profile')
router.register(r'addresses', views.AddressViewSet, basename='address')
# Customer appointments (read-only for customer)
router.register(r'appointments', AppointmentViewSet, basename='customer-appointment')
# Customer subscriptions
router.register(r'subscriptions', SubscriptionViewSet, basename='customer-subscription')
# Customer orders
router.register(r'orders', OrderViewSet, basename='customer-order')

urlpatterns = router.urls
