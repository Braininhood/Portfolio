"""
Route optimization utilities.
Google Maps integration: geocode address, Distance Matrix API, greedy route ordering.
"""
import requests
from django.conf import settings


def geocode_address(address_line1, city=None, postcode=None, country='United Kingdom'):
    """
    Geocode a full address to lat/lng using Google Geocoding API.
    UK-focused; use components country:GB.

    Returns:
        dict: {'lat': float, 'lng': float, 'formatted_address': str} or None
    """
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None) or getattr(settings, 'GOOGLE_PLACES_API_KEY', None)
    if not api_key:
        return None
    parts = [p for p in [address_line1, city, postcode, country] if p]
    address = ', '.join(parts)
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'address': address, 'components': 'country:GB', 'key': api_key}
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'OK' and data.get('results'):
                loc = data['results'][0]['geometry']['location']
                return {
                    'lat': loc['lat'],
                    'lng': loc['lng'],
                    'formatted_address': data['results'][0].get('formatted_address', address),
                }
    except Exception:
        pass
    return None


def get_distance_matrix(origins, destinations, api_key=None):
    """
    Get travel time (seconds) and distance (meters) matrix via Google Distance Matrix API.
    origins: list of dicts [{'lat': float, 'lng': float}] or [{'address': str}]
    destinations: same format.
    Returns:
        list of lists: rows[origin_index][dest_index] = {'duration_seconds': int, 'distance_meters': int}
        or None on error. Missing cells as None.
    """
    api_key = api_key or getattr(settings, 'GOOGLE_MAPS_API_KEY', None) or getattr(settings, 'GOOGLE_PLACES_API_KEY', None)
    if not api_key:
        return None
    def to_str(pt):
        if isinstance(pt, dict):
            if 'lat' in pt and 'lng' in pt:
                return f"{pt['lat']},{pt['lng']}"
            return pt.get('address', '')
        return str(pt)
    origins_str = '|'.join(to_str(o) for o in origins)
    destinations_str = '|'.join(to_str(d) for d in destinations)
    url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
    params = {
        'origins': origins_str,
        'destinations': destinations_str,
        'key': api_key,
        'units': 'metric',
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get('status') != 'OK':
            return None
        rows = data.get('rows', [])
        result = []
        for row in rows:
            result_row = []
            for cell in row.get('elements', []):
                if cell.get('status') == 'OK':
                    d = cell.get('duration', {})
                    dist = cell.get('distance', {})
                    result_row.append({
                        'duration_seconds': d.get('value', 0),
                        'distance_meters': dist.get('value', 0),
                    })
                else:
                    result_row.append(None)
            result.append(result_row)
        return result
    except Exception:
        return None


def optimize_route_greedy(stops_lat_lng, start_index=0):
    """
    Greedy nearest-neighbour route optimization.
    stops_lat_lng: list of {'lat': float, 'lng': float}
    start_index: which stop to start at (default 0).
    Returns:
        order: list of indices in visit order
        leg_durations_seconds: list of travel times between consecutive stops (length = len(order)-1)
        total_duration_seconds: sum of leg_durations
    """
    n = len(stops_lat_lng)
    if n <= 1:
        return list(range(n)), [], 0
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None) or getattr(settings, 'GOOGLE_PLACES_API_KEY', None)
    if not api_key:
        return list(range(n)), [], 0
    matrix = get_distance_matrix(stops_lat_lng, stops_lat_lng, api_key)
    if not matrix or len(matrix) != n:
        return list(range(n)), [], 0
    order = [start_index]
    remaining = set(range(n)) - {start_index}
    leg_durations = []
    while remaining:
        i = order[-1]
        best_j = None
        best_dur = float('inf')
        for j in remaining:
            cell = matrix[i][j] if i < len(matrix) and j < len(matrix[i]) else None
            if cell and cell.get('duration_seconds', 0) < best_dur:
                best_dur = cell['duration_seconds']
                best_j = j
        if best_j is None:
            break
        order.append(best_j)
        remaining.discard(best_j)
        leg_durations.append(best_dur)
    total = sum(leg_durations)
    return order, leg_durations, total
