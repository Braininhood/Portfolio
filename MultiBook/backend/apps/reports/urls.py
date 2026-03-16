"""
Reports app URLs.
Admin reports endpoints: /api/ad/reports/
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('revenue/', views.revenue_report_view, name='revenue'),
    path('dashboard/', views.dashboard_overview_view, name='dashboard'),
    path('appointments/', views.appointment_reports_view, name='appointments'),
    path('staff-performance/', views.staff_performance_view, name='staff-performance'),
]
