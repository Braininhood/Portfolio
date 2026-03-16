"""
Accounts app admin URLs.
Admin user and manager endpoints: /api/ad/users/, /api/ad/managers/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'accounts-admin'

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user-admin')
router.register(r'managers', views.ManagerViewSet, basename='manager-admin')

urlpatterns = router.urls
