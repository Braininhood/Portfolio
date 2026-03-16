"""
Staff app self-service URLs.
Staff endpoints: /api/st/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.appointments.views import AppointmentViewSet
from . import views

app_name = 'staff-self-service'

router = DefaultRouter()
# Staff can view their own schedule
router.register(r'schedule', views.StaffScheduleViewSet, basename='staff-schedule-self')
# Staff can view their own jobs (appointments)
router.register(r'jobs', AppointmentViewSet, basename='staff-jobs')
# Staff manage their services (add/edit/delete, extras; new services need approval)
router.register(r'services', views.StaffSelfServiceViewSet, basename='staff-services-self')
# Staff manage their service areas (postcode + radius, optional per-service)
router.register(r'areas', views.StaffSelfAreaViewSet, basename='staff-areas-self')
# Staff list categories (for creating services)
router.register(r'categories', views.StaffCategoriesListView, basename='staff-categories')

urlpatterns = router.urls
