"""
Staff app URLs.
Public: /api/stf/ (public listing)
Protected: /api/st/ (staff endpoints), /api/ad/staff/ or /api/man/staff/ (admin/manager)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'staff'

# Public staff listing router
public_router = DefaultRouter()
public_router.register(r'', views.StaffPublicViewSet, basename='staff-public')

urlpatterns = [
    # Public endpoints (security prefix: /api/stf/)
    path('', include(public_router.urls)),
]

# Note: Protected endpoints (/api/st/, /api/ad/staff/, /api/man/staff/) 
# will be configured in main URL routing files
