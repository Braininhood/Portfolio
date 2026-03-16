"""
Subscriptions app URLs.
Public: /api/bkg/subscriptions/ (guest checkout supported)
Protected: /api/cus/subscriptions/ (customer endpoints), /api/ad/subscriptions/ (admin)
Note: Guest access endpoints are configured in main API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'subscriptions'

# Public subscription router (guest checkout supported)
public_router = DefaultRouter()
public_router.register(r'', views.SubscriptionPublicViewSet, basename='subscription-public')

urlpatterns = [
    # Public endpoints (POST /api/bkg/subscriptions/ - create subscription)
    path('', include(public_router.urls)),
]

# Note: Guest access endpoints (/api/bkg/guest/subscription/{subscription_number}/, etc.) 
# are configured in apps/api/urls.py
# Protected endpoints (/api/cus/subscriptions/, /api/ad/subscriptions/) 
# will be configured in main URL routing files
