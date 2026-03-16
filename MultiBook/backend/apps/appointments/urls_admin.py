"""
Appointments app admin URLs.
Admin appointment endpoints: /api/ad/appointments/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'appointments-admin'

router = DefaultRouter()
router.register(r'appointments', views.AppointmentViewSet, basename='appointment-admin')

urlpatterns = router.urls
