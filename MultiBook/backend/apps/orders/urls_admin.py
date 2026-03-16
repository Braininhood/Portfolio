"""
Orders app admin URLs.
Admin order endpoints: /api/ad/orders/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'orders-admin'

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='order-admin')
router.register(r'change-requests', views.ChangeRequestViewSet, basename='change-request-admin')

urlpatterns = router.urls
