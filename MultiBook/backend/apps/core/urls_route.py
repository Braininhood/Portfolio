"""
Route optimization URLs.
Admin/manager: /api/ad/routes/
"""
from django.urls import path
from . import views_route

app_name = 'routes'

urlpatterns = [
    path('optimize/', views_route.route_optimize_view, name='optimize'),
    path('staff-day/', views_route.route_staff_day_view, name='staff-day'),
]
