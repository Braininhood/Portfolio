"""
Revenue calculation utilities.
Aggregates revenue from orders, subscriptions, and appointments.
"""
from django.db.models import Sum, Count, Q, DecimalField
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal


def calculate_revenue_by_period(start_date, end_date, period='day'):
    """
    Calculate revenue by period (day/week/month).
    
    Args:
        start_date: Start date (datetime or date)
        end_date: End date (datetime or date)
        period: 'day', 'week', or 'month'
    
    Returns:
        List of dicts with period, revenue, order_count, subscription_count
    """
    from apps.orders.models import Order
    from apps.subscriptions.models import Subscription
    from apps.appointments.models import CustomerAppointment
    
    # Ensure dates are timezone-aware datetimes
    if isinstance(start_date, datetime) and timezone.is_naive(start_date):
        start_date = timezone.make_aware(start_date)
    elif not isinstance(start_date, datetime):
        start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    
    if isinstance(end_date, datetime) and timezone.is_naive(end_date):
        end_date = timezone.make_aware(end_date)
    elif not isinstance(end_date, datetime):
        end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    
    # Filter completed orders
    orders = Order.objects.filter(
        status='completed',
        payment_status__in=['paid', 'partial'],
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Filter active/completed subscriptions
    subscriptions = Subscription.objects.filter(
        status__in=['active', 'completed'],
        payment_status__in=['paid', 'partial'],
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Filter completed appointments with payments
    appointments = CustomerAppointment.objects.filter(
        appointment__status='completed',
        payment_status__in=['paid', 'partial'],
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Group by period
    if period == 'day':
        trunc_func = TruncDate('created_at')
    elif period == 'week':
        trunc_func = TruncWeek('created_at')
    else:  # month
        trunc_func = TruncMonth('created_at')
    
    # Aggregate orders
    order_data = orders.annotate(
        period=trunc_func
    ).values('period').annotate(
        revenue=Sum('total_price'),
        count=Count('id')
    ).order_by('period')
    
    # Aggregate subscriptions
    subscription_data = subscriptions.annotate(
        period=trunc_func
    ).values('period').annotate(
        revenue=Sum('total_price'),
        count=Count('id')
    ).order_by('period')
    
    # Aggregate appointments
    appointment_data = appointments.annotate(
        period=trunc_func
    ).values('period').annotate(
        revenue=Sum('total_price'),
        count=Count('id')
    ).order_by('period')
    
    # Combine data
    period_dict = {}
    
    for item in order_data:
        period_key = str(item['period'])
        if period_key not in period_dict:
            period_dict[period_key] = {
                'period': item['period'],
                'revenue': Decimal('0'),
                'order_count': 0,
                'subscription_count': 0,
                'appointment_count': 0,
            }
        period_dict[period_key]['revenue'] += Decimal(str(item['revenue'] or 0))
        period_dict[period_key]['order_count'] += item['count']
    
    for item in subscription_data:
        period_key = str(item['period'])
        if period_key not in period_dict:
            period_dict[period_key] = {
                'period': item['period'],
                'revenue': Decimal('0'),
                'order_count': 0,
                'subscription_count': 0,
                'appointment_count': 0,
            }
        period_dict[period_key]['revenue'] += Decimal(str(item['revenue'] or 0))
        period_dict[period_key]['subscription_count'] += item['count']
    
    for item in appointment_data:
        period_key = str(item['period'])
        if period_key not in period_dict:
            period_dict[period_key] = {
                'period': item['period'],
                'revenue': Decimal('0'),
                'order_count': 0,
                'subscription_count': 0,
                'appointment_count': 0,
            }
        period_dict[period_key]['revenue'] += Decimal(str(item['revenue'] or 0))
        period_dict[period_key]['appointment_count'] += item['count']
    
    # Convert to list and format
    result = []
    for period_key in sorted(period_dict.keys()):
        item = period_dict[period_key]
        result.append({
            'period': item['period'].isoformat() if hasattr(item['period'], 'isoformat') else str(item['period']),
            'revenue': float(item['revenue']),
            'order_count': item['order_count'],
            'subscription_count': item['subscription_count'],
            'appointment_count': item['appointment_count'],
            'total_count': item['order_count'] + item['subscription_count'] + item['appointment_count'],
        })
    
    return result


def calculate_revenue_by_service(start_date, end_date):
    """
    Calculate revenue by service.
    
    Args:
        start_date: Start date
        end_date: End date
    
    Returns:
        List of dicts with service_id, service_name, revenue, count
    """
    from apps.orders.models import Order, OrderItem
    from apps.subscriptions.models import Subscription
    from apps.appointments.models import CustomerAppointment
    
    # Ensure dates are timezone-aware
    if isinstance(start_date, datetime) and timezone.is_naive(start_date):
        start_date = timezone.make_aware(start_date)
    elif not isinstance(start_date, datetime):
        start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    
    if isinstance(end_date, datetime) and timezone.is_naive(end_date):
        end_date = timezone.make_aware(end_date)
    elif not isinstance(end_date, datetime):
        end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    
    # Revenue from order items
    order_items = OrderItem.objects.filter(
        order__status='completed',
        order__payment_status__in=['paid', 'partial'],
        order__created_at__gte=start_date,
        order__created_at__lte=end_date
    ).values('service__id', 'service__name').annotate(
        revenue=Sum('total_price'),
        count=Count('id')
    )
    
    # Revenue from subscriptions
    subscriptions = Subscription.objects.filter(
        status__in=['active', 'completed'],
        payment_status__in=['paid', 'partial'],
        created_at__gte=start_date,
        created_at__lte=end_date
    ).values('service__id', 'service__name').annotate(
        revenue=Sum('total_price'),
        count=Count('id')
    )
    
    # Revenue from appointments
    appointments = CustomerAppointment.objects.filter(
        appointment__status='completed',
        payment_status__in=['paid', 'partial'],
        appointment__service__isnull=False,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).values('appointment__service__id', 'appointment__service__name').annotate(
        revenue=Sum('total_price'),
        count=Count('id')
    )
    
    # Combine data
    service_dict = {}
    
    for item in order_items:
        service_id = item['service__id']
        if service_id not in service_dict:
            service_dict[service_id] = {
                'service_id': service_id,
                'service_name': item['service__name'],
                'revenue': Decimal('0'),
                'order_count': 0,
                'subscription_count': 0,
                'appointment_count': 0,
            }
        service_dict[service_id]['revenue'] += Decimal(str(item['revenue'] or 0))
        service_dict[service_id]['order_count'] += item['count']
    
    for item in subscriptions:
        service_id = item['service__id']
        if service_id not in service_dict:
            service_dict[service_id] = {
                'service_id': service_id,
                'service_name': item['service__name'],
                'revenue': Decimal('0'),
                'order_count': 0,
                'subscription_count': 0,
                'appointment_count': 0,
            }
        service_dict[service_id]['revenue'] += Decimal(str(item['revenue'] or 0))
        service_dict[service_id]['subscription_count'] += item['count']
    
    for item in appointments:
        service_id = item['appointment__service__id']
        if service_id not in service_dict:
            service_dict[service_id] = {
                'service_id': service_id,
                'service_name': item['appointment__service__name'],
                'revenue': Decimal('0'),
                'order_count': 0,
                'subscription_count': 0,
                'appointment_count': 0,
            }
        service_dict[service_id]['revenue'] += Decimal(str(item['revenue'] or 0))
        service_dict[service_id]['appointment_count'] += item['count']
    
    # Convert to list and sort by revenue
    result = []
    for service_id in service_dict:
        item = service_dict[service_id]
        result.append({
            'service_id': item['service_id'],
            'service_name': item['service_name'],
            'revenue': float(item['revenue']),
            'order_count': item['order_count'],
            'subscription_count': item['subscription_count'],
            'appointment_count': item['appointment_count'],
            'total_count': item['order_count'] + item['subscription_count'] + item['appointment_count'],
        })
    
    result.sort(key=lambda x: x['revenue'], reverse=True)
    return result


def calculate_revenue_by_staff(start_date, end_date):
    """
    Calculate revenue by staff member.
    
    Args:
        start_date: Start date
        end_date: End date
    
    Returns:
        List of dicts with staff_id, staff_name, revenue, count
    """
    from apps.orders.models import Order, OrderItem
    from apps.subscriptions.models import Subscription
    from apps.appointments.models import CustomerAppointment
    
    # Ensure dates are timezone-aware
    if isinstance(start_date, datetime) and timezone.is_naive(start_date):
        start_date = timezone.make_aware(start_date)
    elif not isinstance(start_date, datetime):
        start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    
    if isinstance(end_date, datetime) and timezone.is_naive(end_date):
        end_date = timezone.make_aware(end_date)
    elif not isinstance(end_date, datetime):
        end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    
    # Revenue from order items
    order_items = OrderItem.objects.filter(
        order__status='completed',
        order__payment_status__in=['paid', 'partial'],
        order__created_at__gte=start_date,
        order__created_at__lte=end_date,
        staff__isnull=False
    ).values('staff__id', 'staff__name').annotate(
        revenue=Sum('total_price'),
        count=Count('id')
    )
    
    # Revenue from subscriptions
    subscriptions = Subscription.objects.filter(
        status__in=['active', 'completed'],
        payment_status__in=['paid', 'partial'],
        created_at__gte=start_date,
        created_at__lte=end_date,
        staff__isnull=False
    ).values('staff__id', 'staff__name').annotate(
        revenue=Sum('total_price'),
        count=Count('id')
    )
    
    # Revenue from appointments
    appointments = CustomerAppointment.objects.filter(
        appointment__status='completed',
        payment_status__in=['paid', 'partial'],
        appointment__staff__isnull=False,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).values('appointment__staff__id', 'appointment__staff__name').annotate(
        revenue=Sum('total_price'),
        count=Count('id')
    )
    
    # Combine data
    staff_dict = {}
    
    for item in order_items:
        staff_id = item['staff__id']
        if staff_id not in staff_dict:
            staff_dict[staff_id] = {
                'staff_id': staff_id,
                'staff_name': item['staff__name'],
                'revenue': Decimal('0'),
                'order_count': 0,
                'subscription_count': 0,
                'appointment_count': 0,
            }
        staff_dict[staff_id]['revenue'] += Decimal(str(item['revenue'] or 0))
        staff_dict[staff_id]['order_count'] += item['count']
    
    for item in subscriptions:
        staff_id = item['staff__id']
        if staff_id not in staff_dict:
            staff_dict[staff_id] = {
                'staff_id': staff_id,
                'staff_name': item['staff__name'],
                'revenue': Decimal('0'),
                'order_count': 0,
                'subscription_count': 0,
                'appointment_count': 0,
            }
        staff_dict[staff_id]['revenue'] += Decimal(str(item['revenue'] or 0))
        staff_dict[staff_id]['subscription_count'] += item['count']
    
    for item in appointments:
        staff_id = item['appointment__staff__id']
        if staff_id not in staff_dict:
            staff_dict[staff_id] = {
                'staff_id': staff_id,
                'staff_name': item['appointment__staff__name'],
                'revenue': Decimal('0'),
                'order_count': 0,
                'subscription_count': 0,
                'appointment_count': 0,
            }
        staff_dict[staff_id]['revenue'] += Decimal(str(item['revenue'] or 0))
        staff_dict[staff_id]['appointment_count'] += item['count']
    
    # Convert to list and sort by revenue
    result = []
    for staff_id in staff_dict:
        item = staff_dict[staff_id]
        result.append({
            'staff_id': item['staff_id'],
            'staff_name': item['staff_name'],
            'revenue': float(item['revenue']),
            'order_count': item['order_count'],
            'subscription_count': item['subscription_count'],
            'appointment_count': item['appointment_count'],
            'total_count': item['order_count'] + item['subscription_count'] + item['appointment_count'],
        })
    
    result.sort(key=lambda x: x['revenue'], reverse=True)
    return result


def calculate_total_revenue(start_date, end_date):
    """
    Calculate total revenue for a date range.
    
    Args:
        start_date: Start date
        end_date: End date
    
    Returns:
        Dict with total_revenue, order_revenue, subscription_revenue, appointment_revenue
    """
    from apps.orders.models import Order
    from apps.subscriptions.models import Subscription
    from apps.appointments.models import CustomerAppointment
    
    # Ensure dates are timezone-aware
    if isinstance(start_date, datetime) and timezone.is_naive(start_date):
        start_date = timezone.make_aware(start_date)
    elif not isinstance(start_date, datetime):
        start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    
    if isinstance(end_date, datetime) and timezone.is_naive(end_date):
        end_date = timezone.make_aware(end_date)
    elif not isinstance(end_date, datetime):
        end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    
    # Calculate revenue from orders
    order_revenue = Order.objects.filter(
        status='completed',
        payment_status__in=['paid', 'partial'],
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(total=Sum('total_price'))['total'] or Decimal('0')
    
    # Calculate revenue from subscriptions
    subscription_revenue = Subscription.objects.filter(
        status__in=['active', 'completed'],
        payment_status__in=['paid', 'partial'],
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(total=Sum('total_price'))['total'] or Decimal('0')
    
    # Calculate revenue from appointments
    appointment_revenue = CustomerAppointment.objects.filter(
        appointment__status='completed',
        payment_status__in=['paid', 'partial'],
        created_at__gte=start_date,
        created_at__lte=end_date
    ).aggregate(total=Sum('total_price'))['total'] or Decimal('0')
    
    total_revenue = order_revenue + subscription_revenue + appointment_revenue
    
    return {
        'total_revenue': float(total_revenue),
        'order_revenue': float(order_revenue),
        'subscription_revenue': float(subscription_revenue),
        'appointment_revenue': float(appointment_revenue),
    }
