"""
Appointments app URLs.
Public: /api/bkg/appointments/ (bookings - guest checkout supported)
Protected: /api/cus/appointments/ (customer endpoints), /api/st/jobs/ (staff endpoints), /api/ad/appointments/ (admin)
Note: Available slots endpoint is in urls_slots.py
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'appointments'

# Public booking router (guest checkout supported)
public_router = DefaultRouter()
public_router.register(r'', views.AppointmentPublicViewSet, basename='appointment-public')

urlpatterns = [
    # Public endpoints (POST /api/bkg/appointments/ - create appointment)
    path('', include(public_router.urls)),
]

# Note: Available slots endpoint (/api/slots/) is configured in urls_slots.py
# Protected endpoints (/api/cus/appointments/, /api/st/jobs/, /api/ad/appointments/) 
# will be configured in main URL routing files
