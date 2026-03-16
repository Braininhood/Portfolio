"""
Available slots URLs.
Public: /api/slots/
"""
from django.urls import path
from . import views

app_name = 'slots'

urlpatterns = [
    path('', views.available_slots_view, name='available-slots'),
]
