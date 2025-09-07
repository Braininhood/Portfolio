"""
URL patterns for AI Engine API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIEngineViewSet

router = DefaultRouter()
router.register(r'ai-engine', AIEngineViewSet, basename='ai-engine')

urlpatterns = [
    path('api/v1/', include(router.urls)),
] 