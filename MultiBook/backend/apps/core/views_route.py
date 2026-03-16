"""
Route optimization API.
Week 11 Day 1-2: Distance calculation, route optimization, multi-stop routing, travel time estimates.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime
from apps.core.permissions import IsAdminOrManager
from apps.core.route_utils import geocode_address, optimize_route_greedy


@api_view(['POST'])
@permission_classes([IsAdminOrManager])
def route_optimize_view(request):
    """
    Optimize visit order for multiple stops (multi-stop routing).
    POST /api/ad/routes/optimize/
    Body: {
        "stops": [
            {"address_line1": "...", "city": "...", "postcode": "..."},
            ...
        ],
        "start_index": 0  // optional, which stop to start from (default 0)
    }
    Returns: ordered stop indices, leg travel times (seconds), total travel time, geocoded points for map.
    """
    stops = request.data.get('stops') or []
    start_index = max(0, min(int(request.data.get('start_index', 0)), len(stops) - 1)) if stops else 0
    if not stops:
        return Response({
            'success': False,
            'error': {'code': 'MISSING_STOPS', 'message': 'At least one stop is required'},
        }, status=status.HTTP_400_BAD_REQUEST)
    if len(stops) > 25:
        return Response({
            'success': False,
            'error': {'code': 'TOO_MANY_STOPS', 'message': 'Maximum 25 stops per request (Google API limit)'},
        }, status=status.HTTP_400_BAD_REQUEST)

    points = []
    for i, s in enumerate(stops):
        line1 = s.get('address_line1') or s.get('address') or ''
        city = s.get('city') or ''
        postcode = s.get('postcode') or ''
        if s.get('lat') is not None and s.get('lng') is not None:
            points.append({'lat': float(s['lat']), 'lng': float(s['lng']), 'label': s.get('label', f'Stop {i+1}')})
        else:
            geo = geocode_address(line1, city=city or None, postcode=postcode or None)
            if geo:
                points.append({
                    'lat': geo['lat'],
                    'lng': geo['lng'],
                    'formatted_address': geo.get('formatted_address', ''),
                    'label': s.get('label', f'Stop {i+1}'),
                })
            else:
                return Response({
                    'success': False,
                    'error': {'code': 'GEOCODE_FAILED', 'message': f'Could not geocode stop {i+1}. Check address and GOOGLE_MAPS_API_KEY.'},
                }, status=status.HTTP_400_BAD_REQUEST)

    stops_lat_lng = [{'lat': p['lat'], 'lng': p['lng']} for p in points]
    order, leg_durations, total_duration = optimize_route_greedy(stops_lat_lng, start_index=start_index)

    ordered_stops = []
    for idx, pos in enumerate(order):
        pt = points[pos]
        leg_sec = leg_durations[idx] if idx < len(leg_durations) else None
        ordered_stops.append({
            'index': pos,
            'order_position': idx + 1,
            'lat': pt['lat'],
            'lng': pt['lng'],
            'label': pt.get('label', f'Stop {pos+1}'),
            'formatted_address': pt.get('formatted_address', ''),
            'travel_time_to_next_seconds': leg_sec,
            'travel_time_to_next_minutes': round(leg_sec / 60, 1) if leg_sec is not None else None,
        })

    return Response({
        'success': True,
        'data': {
            'ordered_stops': ordered_stops,
            'order_indices': order,
            'leg_durations_seconds': leg_durations,
            'total_duration_seconds': total_duration,
            'total_duration_minutes': round(total_duration / 60, 1),
            'points': [{'lat': p['lat'], 'lng': p['lng'], 'label': p.get('label', '')} for p in points],
        },
        'meta': {'generated_at': timezone.now().isoformat()},
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminOrManager])
def route_staff_day_view(request):
    """
    Get appointments for a staff member on a date and return addresses for route optimization.
    GET /api/ad/routes/staff-day/?staff_id=1&date=2026-02-01
    Returns: list of stops (address_line1, city, postcode) from orders linked to those appointments.
    """
    staff_id = request.query_params.get('staff_id')
    date_str = request.query_params.get('date')
    if not staff_id or not date_str:
        return Response({
            'success': False,
            'error': {'code': 'MISSING_PARAMS', 'message': 'staff_id and date (YYYY-MM-DD) are required'},
        }, status=status.HTTP_400_BAD_REQUEST)
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({
            'success': False,
            'error': {'code': 'INVALID_DATE', 'message': 'date must be YYYY-MM-DD'},
        }, status=status.HTTP_400_BAD_REQUEST)

    from apps.appointments.models import Appointment

    start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
    end = timezone.make_aware(datetime.combine(date, datetime.max.time()))
    appointments = (
        Appointment.objects.filter(
            staff_id=int(staff_id),
            start_time__gte=start,
            start_time__lte=end,
        )
        .select_related('order')
        .order_by('start_time')
    )
    stops = []
    for apt in appointments:
        if apt.order_id and apt.order:
            o = apt.order
            stops.append({
                'appointment_id': apt.id,
                'start_time': apt.start_time.isoformat() if apt.start_time else None,
                'address_line1': o.address_line1 or '',
                'city': o.city or '',
                'postcode': o.postcode or '',
                'label': f"#{apt.id} {o.address_line1 or 'No address'}",
            })
        else:
            stops.append({
                'appointment_id': apt.id,
                'start_time': apt.start_time.isoformat() if apt.start_time else None,
                'address_line1': '',
                'city': '',
                'postcode': '',
                'label': f'Appointment #{apt.id} (no order address)',
            })

    return Response({
        'success': True,
        'data': {
            'staff_id': int(staff_id),
            'date': date_str,
            'stops': stops,
        },
        'meta': {'generated_at': timezone.now().isoformat()},
    }, status=status.HTTP_200_OK)
