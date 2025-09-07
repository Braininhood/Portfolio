"""
URL configuration for network_monitor project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API routes (must come before catch-all)
    path('api/v1/', include('apps.api.urls')),
    path('', include('apps.ai_engine.urls')),
    
    # Authentication
    path('api/auth/', include('rest_framework.urls')),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Add catch-all pattern for React Router LAST
urlpatterns += [
    # Catch-all pattern for React Router
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
] 