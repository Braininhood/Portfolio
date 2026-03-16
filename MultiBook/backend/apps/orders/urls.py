"""
Orders app URLs.
Public: /api/bkg/orders/ (guest checkout supported - multi-service)
Protected: /api/cus/orders/ (customer endpoints), /api/ad/orders/ (admin)
Note: Guest access endpoints are configured in main API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'orders'

# Public order router (guest checkout supported)
public_router = DefaultRouter()
public_router.register(r'', views.OrderPublicViewSet, basename='order-public')

urlpatterns = [
    # Public endpoints (POST /api/bkg/orders/ - create multi-service order)
    path('', include(public_router.urls)),
]

# Note: Guest access endpoints (/api/bkg/guest/order/{order_number}/, etc.) 
# are configured in apps/api/urls.py
# Protected endpoints (/api/cus/orders/, /api/ad/orders/) 
# will be configured in main URL routing files
