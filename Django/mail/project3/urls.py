"""project3 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve
from django.conf import settings
import os
from rest_framework.authtoken.views import obtain_auth_token
from mail.views import api_login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mail.urls')),
    path('favicon.ico', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'mail/static/mail'),
        'path': 'favicon.ico'
    }),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/login/', api_login, name='api_login'),
]
