"""
Customers app admin URLs.
Admin customer endpoints: /api/ad/customers/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'customers-admin'

router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet, basename='customer-admin')

urlpatterns = router.urls
