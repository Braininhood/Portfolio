from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'vault', views.VaultViewSet, basename='vault')
router.register(r'password-entries', views.PasswordEntryViewSet, basename='password-entries')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('check-username/', views.check_username, name='check-username'),
    path('setup-master-key/', views.setup_master_key, name='setup-master-key'),
    path('get-master-key-salt/', views.get_master_key_salt, name='get-master-key-salt'),
    path('verify-master-key/', views.verify_master_key, name='verify-master-key'),
] 