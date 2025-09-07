from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from apps.ai_engine.views import AIEngineViewSet

# Create router and register ViewSets
router = DefaultRouter()
router.register(r'devices', views.NetworkDeviceViewSet)
router.register(r'scans', views.NetworkScanViewSet)
router.register(r'scan-templates', views.ScanTemplateViewSet)
router.register(r'traffic', views.NetworkTrafficViewSet)
router.register(r'security-events', views.SecurityEventViewSet)
router.register(r'interfaces', views.NetworkInterfaceViewSet)
router.register(r'configurations', views.NetworkConfigurationViewSet)
router.register(r'ai-engine', AIEngineViewSet, basename='ai-engine')

urlpatterns = [
    # Dashboard endpoints
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('network/overview/', views.network_overview, name='network-overview'),
    
    # Monitoring endpoints
    path('monitoring/start/', views.start_monitoring, name='start-monitoring'),
    path('monitoring/stop/', views.stop_monitoring, name='stop-monitoring'),
    path('monitoring/status/', views.monitoring_status, name='monitoring-status'),
    
    # Traffic monitoring endpoints
    path('traffic/real-time-metrics/', views.real_time_traffic_metrics, name='real-time-traffic-metrics'),
    
    # Router URLs (include all ViewSet routes)
    path('', include(router.urls)),
] 