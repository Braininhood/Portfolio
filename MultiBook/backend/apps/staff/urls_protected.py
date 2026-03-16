"""
Staff app protected URLs.
Admin: /api/ad/staff/, /api/ad/staff-areas/, /api/ad/staff-schedules/, /api/ad/staff-services/
Manager: /api/man/staff/ (read-only)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'staff_protected'

# Admin/Manager routers
admin_router = DefaultRouter()
admin_router.register(r'staff', views.StaffViewSet, basename='staff-admin')
admin_router.register(r'staff-areas', views.StaffAreaViewSet, basename='staff-area-admin')
admin_router.register(r'staff-schedules', views.StaffScheduleViewSet, basename='staff-schedule-admin')
admin_router.register(r'staff-services', views.StaffServiceViewSet, basename='staff-service-admin')

# Manager router (read-only staff)
manager_router = DefaultRouter()
manager_router.register(r'staff', views.StaffViewSet, basename='staff-manager')

urlpatterns = [
    # Admin endpoints
    path('ad/', include(admin_router.urls)),
    # Manager endpoints
    path('man/', include(manager_router.urls)),
]
