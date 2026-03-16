"""
Reports app views.
Revenue reporting with export functionality.
Dashboard overview for admin (metrics + recent activity).
Day 3-4: Appointment reports (statistics, trends, popular services, peak times, cancellation, conversion).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncHour
from datetime import datetime, timedelta
from django.http import HttpResponse
import csv
import json

from apps.core.permissions import IsAdminOrManager
from .revenue_utils import (
    calculate_revenue_by_period,
    calculate_revenue_by_service,
    calculate_revenue_by_staff,
    calculate_total_revenue
)


@api_view(['GET'])
@permission_classes([IsAdminOrManager])
def dashboard_overview_view(request):
    """
    Admin dashboard overview: key metrics and recent activity.
    GET /api/ad/reports/dashboard/
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    month_start = today_start.replace(day=1)
    week_start = today_start - timedelta(days=today_start.weekday())

    from apps.orders.models import Order, ChangeRequest
    from apps.appointments.models import Appointment
    from apps.customers.models import Customer
    from apps.staff.models import Staff

    # Key metrics
    orders_today = Order.objects.filter(created_at__gte=today_start, created_at__lt=today_end).count()
    orders_this_week = Order.objects.filter(created_at__gte=week_start, created_at__lte=now).count()
    orders_pending = Order.objects.filter(status='pending').count()
    orders_confirmed_today = Order.objects.filter(status='confirmed', scheduled_date=today_start.date()).count()

    appointments_today = Appointment.objects.filter(
        start_time__gte=today_start,
        start_time__lt=today_end,
        status__in=['confirmed', 'pending'],
    ).count()
    appointments_upcoming = Appointment.objects.filter(
        start_time__gte=now,
        status__in=['confirmed', 'pending'],
    ).order_by('start_time')[:10]

    total_customers = Customer.objects.count()
    total_staff = Staff.objects.filter(is_active=True).count()

    pending_change_requests = ChangeRequest.objects.filter(status='pending').count()

    revenue_today = calculate_total_revenue(today_start, now)
    revenue_this_month = calculate_total_revenue(month_start, now)

    # Recent orders (last 10)
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:10]
    recent_orders_data = [
        {
            'id': o.id,
            'order_number': o.order_number,
            'status': o.status,
            'total_price': str(o.total_price),
            'scheduled_date': o.scheduled_date.isoformat() if o.scheduled_date else None,
            'scheduled_time': str(o.scheduled_time) if o.scheduled_time else None,
            'customer_name': o.customer.name if o.customer else o.guest_name,
            'created_at': o.created_at.isoformat() if o.created_at else None,
        }
        for o in recent_orders
    ]

    # Upcoming appointments (next 10)
    upcoming_appointments_data = [
        {
            'id': a.id,
            'start_time': a.start_time.isoformat() if a.start_time else None,
            'end_time': a.end_time.isoformat() if a.end_time else None,
            'status': a.status,
            'service_name': a.service.name if a.service_id else None,
            'staff_name': a.staff.name if a.staff_id else None,
        }
        for a in appointments_upcoming
    ]

    return Response({
        'success': True,
        'data': {
            'metrics': {
                'orders_today': orders_today,
                'orders_this_week': orders_this_week,
                'orders_pending': orders_pending,
                'orders_confirmed_today': orders_confirmed_today,
                'appointments_today': appointments_today,
                'total_customers': total_customers,
                'total_staff': total_staff,
                'pending_change_requests': pending_change_requests,
                'revenue_today': revenue_today,
                'revenue_this_month': revenue_this_month,
            },
            'recent_orders': recent_orders_data,
            'upcoming_appointments': upcoming_appointments_data,
        },
        'meta': {'generated_at': now.isoformat()},
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminOrManager])
def revenue_report_view(request):
    """
    Get revenue report.
    GET /api/ad/reports/revenue/
    
    Query params:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - period: 'day', 'week', or 'month' (default: 'day')
    - group_by: 'period', 'service', 'staff', or 'all' (default: 'all')
    - format: 'json', 'csv', or 'pdf' (default: 'json')
    """
    # Get query parameters
    start_date_str = request.query_params.get('start_date')
    end_date_str = request.query_params.get('end_date')
    period = request.query_params.get('period', 'day')
    group_by = request.query_params.get('group_by', 'all')
    format_type = request.query_params.get('format', 'json')
    
    # Default to last 30 days if not provided
    if not end_date_str:
        end_date = timezone.now()
    else:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        except ValueError:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_DATE',
                    'message': 'Invalid end_date format. Use YYYY-MM-DD',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    
    if not start_date_str:
        start_date = end_date - timedelta(days=30)
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        except ValueError:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_DATE',
                    'message': 'Invalid start_date format. Use YYYY-MM-DD',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate period
    if period not in ['day', 'week', 'month']:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_PERIOD',
                'message': 'Period must be "day", "week", or "month"',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Calculate total revenue
    total_revenue = calculate_total_revenue(start_date, end_date)
    
    # Prepare response data
    data = {
        'start_date': start_date.date().isoformat(),
        'end_date': end_date.date().isoformat(),
        'period': period,
        'total_revenue': total_revenue,
    }
    
    # Add breakdown based on group_by
    if group_by in ['all', 'period']:
        data['by_period'] = calculate_revenue_by_period(start_date, end_date, period)
    
    if group_by in ['all', 'service']:
        data['by_service'] = calculate_revenue_by_service(start_date, end_date)
    
    if group_by in ['all', 'staff']:
        data['by_staff'] = calculate_revenue_by_staff(start_date, end_date)
    
    # Handle export formats
    if format_type == 'csv':
        return export_revenue_csv(data, start_date, end_date)
    elif format_type == 'pdf':
        # PDF export requires reportlab library
        # Install with: pip install reportlab
        # For now, return JSON with a note
        return Response({
            'success': False,
            'error': {
                'code': 'PDF_NOT_IMPLEMENTED',
                'message': 'PDF export requires reportlab library. Install with: pip install reportlab. For now, use CSV or JSON format.',
            }
        }, status=status.HTTP_501_NOT_IMPLEMENTED)
    
    # Return JSON response
    return Response({
        'success': True,
        'data': data,
        'meta': {
            'generated_at': timezone.now().isoformat(),
            'format': format_type,
        }
    }, status=status.HTTP_200_OK)


def export_revenue_csv(data, start_date, end_date):
    """
    Export revenue data to CSV.
    """
    response = HttpResponse(content_type='text/csv')
    filename = f'revenue_report_{start_date.date()}_to_{end_date.date()}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(['Revenue Report'])
    writer.writerow([f'Period: {start_date.date()} to {end_date.date()}'])
    writer.writerow(['Generated:', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    
    # Write total revenue
    writer.writerow(['Total Revenue Summary'])
    writer.writerow(['Total Revenue', f"£{data['total_revenue']['total_revenue']:.2f}"])
    writer.writerow(['Order Revenue', f"£{data['total_revenue']['order_revenue']:.2f}"])
    writer.writerow(['Subscription Revenue', f"£{data['total_revenue']['subscription_revenue']:.2f}"])
    writer.writerow(['Appointment Revenue', f"£{data['total_revenue']['appointment_revenue']:.2f}"])
    writer.writerow([])
    
    # Write by period
    if 'by_period' in data:
        writer.writerow(['Revenue by Period'])
        writer.writerow(['Period', 'Revenue', 'Orders', 'Subscriptions', 'Appointments', 'Total Count'])
        for item in data['by_period']:
            writer.writerow([
                item['period'],
                f"£{item['revenue']:.2f}",
                item['order_count'],
                item['subscription_count'],
                item['appointment_count'],
                item['total_count'],
            ])
        writer.writerow([])
    
    # Write by service
    if 'by_service' in data:
        writer.writerow(['Revenue by Service'])
        writer.writerow(['Service', 'Revenue', 'Orders', 'Subscriptions', 'Appointments', 'Total Count'])
        for item in data['by_service']:
            writer.writerow([
                item['service_name'],
                f"£{item['revenue']:.2f}",
                item['order_count'],
                item['subscription_count'],
                item['appointment_count'],
                item['total_count'],
            ])
        writer.writerow([])
    
    # Write by staff
    if 'by_staff' in data:
        writer.writerow(['Revenue by Staff'])
        writer.writerow(['Staff', 'Revenue', 'Orders', 'Subscriptions', 'Appointments', 'Total Count'])
        for item in data['by_staff']:
            writer.writerow([
                item['staff_name'],
                f"£{item['revenue']:.2f}",
                item['order_count'],
                item['subscription_count'],
                item['appointment_count'],
                item['total_count'],
            ])
    
    return response


@api_view(['GET'])
@permission_classes([IsAdminOrManager])
def appointment_reports_view(request):
    """
    Day 3-4: Appointment analytics and performance metrics.
    GET /api/ad/reports/appointments/
    Query params: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD). Default: last 90 days.
    Returns: appointment statistics, booking trends, popular services, peak times,
             cancellation rates, conversion metrics.
    """
    from apps.appointments.models import Appointment

    now = timezone.now()
    end_date_str = request.query_params.get('end_date')
    start_date_str = request.query_params.get('start_date')
    try:
        end_date = timezone.make_aware(
            datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        ) if end_date_str else now
    except ValueError:
        end_date = now
    try:
        start_date = timezone.make_aware(
            datetime.strptime(start_date_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
        ) if start_date_str else (end_date - timedelta(days=90))
    except ValueError:
        start_date = end_date - timedelta(days=90)
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    base_qs = Appointment.objects.filter(
        start_time__gte=start_date,
        start_time__lte=end_date,
    ).select_related('service', 'staff')

    # 1. Appointment statistics (counts by status)
    by_status = list(
        base_qs.values('status').annotate(count=Count('id')).order_by('-count')
    )
    total = sum(s['count'] for s in by_status)
    appointment_statistics = {
        'by_status': by_status,
        'total': total,
        'period_start': start_date.isoformat(),
        'period_end': end_date.isoformat(),
    }

    # 2. Booking trends (appointments over time by day)
    trends_qs = (
        base_qs.annotate(day=TruncDate('start_time'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    booking_trends = [
        {'date': item['day'].isoformat() if item['day'] else None, 'count': item['count']}
        for item in trends_qs
    ]

    # 3. Popular services (top by appointment count)
    popular_services = list(
        base_qs.values('service__id', 'service__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:20]
    )
    popular_services = [
        {'service_id': s['service__id'], 'service_name': s['service__name'] or '—', 'count': s['count']}
        for s in popular_services
    ]

    # 4. Peak times: by hour of day (0-23), by day of week (0=Monday)
    by_hour = (
        base_qs.annotate(hour=TruncHour('start_time'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )
    hour_counts = {h['hour'].hour if h['hour'] else 0: h['count'] for h in by_hour}
    peak_times = {
        'by_hour': [{'hour': h, 'count': hour_counts.get(h, 0)} for h in range(24)],
        'by_day_of_week': [],
    }
    # Django week_day: 1=Sunday, 2=Monday, ..., 7=Saturday
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for dow in range(7):
        week_day = (dow + 2) if dow < 6 else 1
        cnt = base_qs.filter(start_time__week_day=week_day).count()
        peak_times['by_day_of_week'].append({'day_of_week': dow, 'day_name': day_names[dow], 'count': cnt})

    # 5. Cancellation rates
    cancelled = base_qs.filter(status='cancelled').count()
    cancellation_rates = {
        'cancelled_count': cancelled,
        'total_count': total,
        'cancellation_rate_pct': round((cancelled / total * 100), 2) if total else 0,
    }

    # 6. Conversion metrics (completed vs total, no_show rate)
    completed = base_qs.filter(status='completed').count()
    no_show = base_qs.filter(status='no_show').count()
    confirmed_or_pending = base_qs.filter(status__in=['confirmed', 'pending']).count()
    conversion_metrics = {
        'completed_count': completed,
        'completed_rate_pct': round((completed / total * 100), 2) if total else 0,
        'no_show_count': no_show,
        'no_show_rate_pct': round((no_show / total * 100), 2) if total else 0,
        'confirmed_or_pending_count': confirmed_or_pending,
    }

    return Response({
        'success': True,
        'data': {
            'appointment_statistics': appointment_statistics,
            'booking_trends': booking_trends,
            'popular_services': popular_services,
            'peak_times': peak_times,
            'cancellation_rates': cancellation_rates,
            'conversion_metrics': conversion_metrics,
        },
        'meta': {'generated_at': now.isoformat(), 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()},
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminOrManager])
def staff_performance_view(request):
    """
    Day 5: Staff performance reports.
    GET /api/ad/reports/staff-performance/
    Query params: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD). Default: last 90 days.
    Returns: jobs completed, revenue per staff, utilization rate, performance comparisons.
    Customer ratings: placeholder (no rating model yet).
    """
    from apps.appointments.models import Appointment
    from apps.staff.models import Staff

    now = timezone.now()
    end_date_str = request.query_params.get('end_date')
    start_date_str = request.query_params.get('start_date')
    try:
        end_date = timezone.make_aware(
            datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        ) if end_date_str else now
    except ValueError:
        end_date = now
    try:
        start_date = timezone.make_aware(
            datetime.strptime(start_date_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
        ) if start_date_str else (end_date - timedelta(days=90))
    except ValueError:
        start_date = end_date - timedelta(days=90)
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    staff_list = list(Staff.objects.filter(is_active=True).order_by('name').values('id', 'name', 'email'))

    # Jobs completed per staff (appointments with status=completed)
    completed_qs = (
        Appointment.objects.filter(
            start_time__gte=start_date,
            start_time__lte=end_date,
            status='completed',
            staff_id__isnull=False,
        )
        .values('staff_id')
        .annotate(jobs_completed=Count('id'))
    )
    jobs_by_staff = {item['staff_id']: item['jobs_completed'] for item in completed_qs}

    # Total appointments per staff (all statuses) for utilization
    total_qs = (
        Appointment.objects.filter(
            start_time__gte=start_date,
            start_time__lte=end_date,
            staff_id__isnull=False,
        )
        .values('staff_id')
        .annotate(total_appointments=Count('id'))
    )
    total_by_staff = {item['staff_id']: item['total_appointments'] for item in total_qs}

    # Revenue per staff (reuse revenue_utils)
    revenue_by_staff = calculate_revenue_by_staff(start_date, end_date)
    revenue_map = {item['staff_id']: item for item in revenue_by_staff}

    # Build per-staff performance (include all active staff)
    performance_list = []
    for s in staff_list:
        sid = s['id']
        jobs_completed = jobs_by_staff.get(sid, 0)
        total_appointments = total_by_staff.get(sid, 0)
        utilization_pct = round((jobs_completed / total_appointments * 100), 2) if total_appointments else 0
        rev_data = revenue_map.get(sid, {})
        revenue = float(rev_data.get('revenue', 0))
        performance_list.append({
            'staff_id': sid,
            'staff_name': s['name'],
            'email': s['email'],
            'jobs_completed': jobs_completed,
            'total_appointments': total_appointments,
            'utilization_rate_pct': utilization_pct,
            'revenue': revenue,
            'order_count': rev_data.get('order_count', 0),
            'subscription_count': rev_data.get('subscription_count', 0),
            'appointment_count': rev_data.get('appointment_count', 0),
            'avg_rating': None,
            'rating_count': 0,
        })
    performance_list.sort(key=lambda x: (x['jobs_completed'], x['revenue']), reverse=True)

    # Comparative rankings (1-based)
    for i, row in enumerate(performance_list):
        row['rank_by_jobs'] = i + 1
    performance_list.sort(key=lambda x: x['revenue'], reverse=True)
    for i, row in enumerate(performance_list):
        row['rank_by_revenue'] = i + 1
    performance_list.sort(key=lambda x: x['utilization_rate_pct'], reverse=True)
    for i, row in enumerate(performance_list):
        row['rank_by_utilization'] = i + 1
    performance_list.sort(key=lambda x: (x['jobs_completed'], x['revenue']), reverse=True)

    return Response({
        'success': True,
        'data': {
            'staff_performance': performance_list,
            'summary': {
                'total_staff': len(staff_list),
                'total_jobs_completed': sum(jobs_by_staff.values()),
                'total_revenue': sum(p['revenue'] for p in performance_list),
            },
        },
        'meta': {'generated_at': now.isoformat(), 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()},
    }, status=status.HTTP_200_OK)
