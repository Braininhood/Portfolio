"""
Address API URLs with security prefix /api/addr/
Public endpoints for address autocomplete and validation.
"""
from django.urls import path
from . import views_address

app_name = 'address'

urlpatterns = [
    path('autocomplete/', views_address.address_autocomplete_view, name='autocomplete'),
    path('validate/', views_address.address_validate_view, name='validate'),
    path('config/', views_address.address_config_view, name='config'),
]
