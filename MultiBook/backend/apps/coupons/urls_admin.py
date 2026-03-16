"""
Coupons app admin URLs.
Admin coupon endpoints: /api/ad/coupons/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'coupons-admin'

router = DefaultRouter()
router.register(r'coupons', views.CouponViewSet, basename='coupon-admin')
router.register(r'coupons/usages', views.CouponUsageViewSet, basename='coupon-usage-admin')

urlpatterns = router.urls
