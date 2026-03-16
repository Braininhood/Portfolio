"""
Services app admin URLs.
Admin service endpoints: /api/ad/services/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'services-admin'

router = DefaultRouter()
router.register(r'services', views.ServiceViewSet, basename='service-admin')
router.register(r'categories', views.CategoryViewSet, basename='category-admin')

urlpatterns = router.urls
