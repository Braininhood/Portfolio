"""
Services app URLs with security prefix /api/svc/
Public endpoints for services.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'services'

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'', views.ServiceViewSet, basename='service')

urlpatterns = router.urls
