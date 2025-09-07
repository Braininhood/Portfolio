from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/network/$', consumers.NetworkMonitorConsumer.as_asgi()),
    re_path(r'ws/network-monitor/$', consumers.NetworkMonitorConsumer.as_asgi()),  # Legacy support
    re_path(r'ws/scan/(?P<scan_id>\w+)/$', consumers.ScanProgressConsumer.as_asgi()),
    re_path(r'ws/device/(?P<device_ip>[\d\.]+)/$', consumers.DeviceDetailConsumer.as_asgi()),
] 