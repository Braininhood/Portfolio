"""
Postcode utilities for area-based filtering.
Includes distance calculation and postcode-to-area mapping logic.
"""
import math
from typing import List, Optional, Dict, Any, Set
from django.db.models import Q, Prefetch
from django.core.cache import cache
from apps.core.address import geocode_postcode, validate_postcode_with_google
from apps.staff.models import StaffArea, Staff


def calculate_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    Returns distance in miles (UK standard).
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
    
    Returns:
        Distance in miles
    """
    # Earth's radius in miles
    R = 3959.0  # miles
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


# Keep old function name for backward compatibility (converts to miles)
def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    DEPRECATED: Use calculate_distance_miles instead.
    This function now returns miles, not kilometers.
    Kept for backward compatibility.
    """
    return calculate_distance_miles(lat1, lon1, lat2, lon2)


def _geocode_postcode_cached(postcode: str) -> Optional[Dict[str, Any]]:
    """
    Geocode a postcode with caching to avoid repeated API calls.
    Cache key: 'geocode_postcode_{normalized_postcode}'
    Cache duration: 24 hours (postcodes don't change)
    """
    # Normalize postcode for cache key
    normalized = postcode.upper().replace(' ', '').strip()
    cache_key = f'geocode_postcode_{normalized}'
    
    # Try cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Geocode via API
    result = geocode_postcode(postcode)
    
    # Cache for 24 hours (86400 seconds)
    if result:
        cache.set(cache_key, result, 86400)
    
    return result


def get_staff_for_postcode(postcode: str, service_id: Optional[int] = None, 
                           validation_result: Optional[Dict] = None,
                           area_coords_cache: Optional[Dict[str, Dict]] = None) -> List[Staff]:
    """
    Get staff members who can service a given postcode.
    Uses StaffArea model to check if postcode is within any staff member's service radius.
    When service_id is provided, only areas that apply to that service (or to all services) are considered.
    
    OPTIMIZED: Accepts pre-validated postcode and area coordinates cache to avoid redundant API calls.
    
    Args:
        postcode: UK postcode string (e.g., 'SW1A 1AA')
        service_id: Optional. If set, only staff with an area covering this postcode for this service are returned.
        validation_result: Optional pre-validated postcode result (to avoid re-validation)
        area_coords_cache: Optional dict mapping postcode -> {lat, lng} to avoid re-geocoding
    
    Returns:
        List of Staff objects that can service this postcode
    """
    # Validate postcode if not provided
    if validation_result is None:
        validation_result = validate_postcode_with_google(postcode)
    
    if not validation_result.get('valid') or not validation_result.get('is_uk'):
        return []
    
    validated_postcode = validation_result.get('formatted', postcode)
    target_lat = validation_result.get('lat')
    target_lng = validation_result.get('lng')
    
    # Base filter: active areas, active staff
    area_filter = dict(is_active=True, staff__is_active=True)
    if service_id is not None:
        # Area applies if service_id is null (all services) or matches this service
        areas_qs = StaffArea.objects.filter(**area_filter).filter(
            Q(service_id__isnull=True) | Q(service_id=service_id)
        ).select_related('staff')
    else:
        areas_qs = StaffArea.objects.filter(**area_filter).select_related('staff')
    
    # If we don't have coordinates, we can't calculate distance
    if target_lat is None or target_lng is None:
        validated_normalized = validated_postcode.upper().replace(' ', '').strip()
        matching_staff_ids = set()
        for area in areas_qs:
            area_normalized = area.postcode.upper().replace(' ', '').strip()
            if area_normalized == validated_normalized:
                matching_staff_ids.add(area.staff_id)
        return Staff.objects.filter(id__in=matching_staff_ids, is_active=True)
    
    # Initialize cache if not provided
    if area_coords_cache is None:
        area_coords_cache = {}
    
    available_staff_ids = set()
    for area in areas_qs:
        # Use cache or geocode with caching
        area_postcode_normalized = area.postcode.upper().replace(' ', '').strip()
        
        if area_postcode_normalized not in area_coords_cache:
            area_geocode = _geocode_postcode_cached(area.postcode)
            if area_geocode and area_geocode.get('lat') and area_geocode.get('lng'):
                area_coords_cache[area_postcode_normalized] = {
                    'lat': area_geocode['lat'],
                    'lng': area_geocode['lng']
                }
            else:
                area_coords_cache[area_postcode_normalized] = None
        
        coords = area_coords_cache.get(area_postcode_normalized)
        if coords and coords.get('lat') and coords.get('lng'):
            area_lat = coords['lat']
            area_lng = coords['lng']
            distance_miles = calculate_distance_miles(target_lat, target_lng, area_lat, area_lng)
            if distance_miles <= float(area.radius_miles):
                available_staff_ids.add(area.staff_id)
        else:
            # Fallback: exact postcode match
            validated_postcode_normalized = validated_postcode.upper().replace(' ', '').strip()
            if area_postcode_normalized == validated_postcode_normalized:
                available_staff_ids.add(area.staff_id)
    
    return Staff.objects.filter(id__in=available_staff_ids, is_active=True).distinct()


def get_services_for_postcode(postcode: str):
    """
    Get services available in a postcode area (cached 10 min per postcode).
    Only approved services are returned.
    """
    from apps.services.models import Service
    from apps.staff.models import StaffService

    normalized = (postcode or '').upper().replace(' ', '').strip()
    if not normalized:
        return Service.objects.none()
    cache_key = f'services_for_postcode_{normalized}'
    cached_ids = cache.get(cache_key)
    if cached_ids is not None:
        return Service.objects.filter(id__in=cached_ids, is_active=True, approval_status='approved').select_related('category').order_by('position', 'id')
    validation_result = validate_postcode_with_google(postcode)
    
    if not validation_result.get('valid') or not validation_result.get('is_uk'):
        return Service.objects.none()
    
    validated_postcode = validation_result.get('formatted', postcode)
    target_lat = validation_result.get('lat')
    target_lng = validation_result.get('lng')
    
    # Pre-fetch all active staff areas and geocode them once (with caching)
    all_areas_qs = StaffArea.objects.filter(
        is_active=True,
        staff__is_active=True
    ).select_related('staff', 'service')
    
    # Get unique postcodes and geocode them once (with caching)
    unique_postcodes = set(all_areas_qs.values_list('postcode', flat=True).distinct())
    area_coords_cache = {}
    for area_postcode in unique_postcodes:
        normalized = area_postcode.upper().replace(' ', '').strip()
        if normalized not in area_coords_cache:
            geocode_result = _geocode_postcode_cached(area_postcode)
            if geocode_result and geocode_result.get('lat') and geocode_result.get('lng'):
                area_coords_cache[normalized] = {
                    'lat': geocode_result['lat'],
                    'lng': geocode_result['lng']
                }
            else:
                area_coords_cache[normalized] = None
    
    # Find staff IDs that can service this postcode
    available_staff_ids = set()
    validated_normalized = validated_postcode.upper().replace(' ', '').strip()
    
    for area in all_areas_qs:
        area_normalized = area.postcode.upper().replace(' ', '').strip()
        
        if target_lat and target_lng:
            # Check distance-based coverage
            coords = area_coords_cache.get(area_normalized)
            if coords and coords.get('lat') and coords.get('lng'):
                distance_miles = calculate_distance_miles(
                    target_lat, target_lng,
                    coords['lat'], coords['lng']
                )
                if distance_miles <= float(area.radius_miles):
                    available_staff_ids.add(area.staff_id)
            elif area_normalized == validated_normalized:
                # Exact postcode match fallback
                available_staff_ids.add(area.staff_id)
        else:
            # No coordinates - exact postcode match only
            if area_normalized == validated_normalized:
                available_staff_ids.add(area.staff_id)
    
    if not available_staff_ids:
        return Service.objects.none()
    
    # Get services that have at least one available staff member
    # A service is available if:
    # 1. Staff provides the service (StaffService)
    # 2. Staff has an area covering the postcode (already checked above)
    # 3. The area is either per-service (service_id matches) or global (service_id is null)
    
    # Get all areas for available staff
    staff_areas = StaffArea.objects.filter(
        staff_id__in=available_staff_ids,
        is_active=True,
        staff__is_active=True
    )
    
    # Find services where staff has coverage
    service_ids_with_coverage = set()
    
    for area in staff_areas:
        # Check if this area covers the postcode
        area_normalized = area.postcode.upper().replace(' ', '').strip()
        covers_postcode = False
        
        if target_lat and target_lng:
            coords = area_coords_cache.get(area_normalized)
            if coords and coords.get('lat') and coords.get('lng'):
                distance_miles = calculate_distance_miles(
                    target_lat, target_lng,
                    coords['lat'], coords['lng']
                )
                covers_postcode = distance_miles <= float(area.radius_miles)
            else:
                covers_postcode = area_normalized == validated_normalized
        else:
            covers_postcode = area_normalized == validated_normalized
        
        if covers_postcode:
            # If area is per-service, add that service
            # If area is global (service_id is null), get all services for this staff
            if area.service_id:
                service_ids_with_coverage.add(area.service_id)
            else:
                # Global area - get all services this staff provides
                staff_services = StaffService.objects.filter(
                    staff_id=area.staff_id,
                    is_active=True
                ).values_list('service_id', flat=True)
                service_ids_with_coverage.update(staff_services)
    
    qs = Service.objects.filter(
        id__in=service_ids_with_coverage,
        is_active=True,
        approval_status='approved'
    ).select_related('category').distinct()
    cache.set(cache_key, list(qs.values_list('id', flat=True)), 600)  # 10 min
    return qs


def check_postcode_in_area(customer_postcode: str, staff_area: StaffArea) -> bool:
    """
    Check if a customer postcode is within a staff member's service area.
    
    Args:
        customer_postcode: Customer's postcode
        staff_area: StaffArea object with center postcode and radius
    
    Returns:
        True if customer postcode is within staff area, False otherwise
    """
    # Validate customer postcode
    validation_result = validate_postcode_with_google(customer_postcode)
    
    if not validation_result.get('valid') or not validation_result.get('is_uk'):
        return False
    
    customer_lat = validation_result.get('lat')
    customer_lng = validation_result.get('lng')
    
    # Geocode staff area center postcode
    area_geocode = geocode_postcode(staff_area.postcode)
    
    if not area_geocode or not area_geocode.get('lat') or not area_geocode.get('lng'):
        # Fallback: exact postcode match
        return staff_area.postcode.upper().replace(' ', '') == customer_postcode.upper().replace(' ', '')
    
    area_lat = area_geocode['lat']
    area_lng = area_geocode['lng']
    
    # Calculate distance
    if customer_lat is None or customer_lng is None:
        return False
    
    distance_miles = calculate_distance_miles(customer_lat, customer_lng, area_lat, area_lng)
    
    # Check if within radius (radius_miles is stored in miles)
    return distance_miles <= float(staff_area.radius_miles)
