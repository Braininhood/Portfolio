"""
Coupons app URLs.
Public: /api/coupons/ (validate, list active)
Admin: /api/ad/coupons/ (CRUD)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'coupons'

router = DefaultRouter()
router.register(r'', views.CouponViewSet, basename='coupon')
router.register(r'usages', views.CouponUsageViewSet, basename='coupon-usage')

urlpatterns = router.urls
