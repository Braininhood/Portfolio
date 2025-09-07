"""
ASGI config for network_monitor project.
"""

import os
import django
from django.core.asgi import get_asgi_application

# Setup Django first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'network_monitor.settings')
django.setup()

# Now import Django-dependent modules
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.websocket.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            apps.websocket.routing.websocket_urlpatterns
        )
    ),
}) 