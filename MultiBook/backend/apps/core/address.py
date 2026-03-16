"""
Address utilities and Google Places API integration.
Uses Django cache to reduce latency and API calls (transparent for all users).
"""
import requests
from django.conf import settings
from django.core.cache import cache


def _geocode_postcode_uncached(postcode):
    """
    Geocode a UK postcode to get latitude and longitude.
    Uses Google Geocoding API.
    IMPORTANT: Only accepts UK postcodes - validates country is GB.
    
    Args:
        postcode: UK postcode string (e.g., 'SW1A 1AA')
    
    Returns:
        dict: {'lat': float, 'lng': float, 'formatted_address': str, 'components': dict, 'is_uk': bool} or None
    """
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None) or getattr(settings, 'GOOGLE_PLACES_API_KEY', None)
    
    if not api_key:
        # If no API key, return basic validation (postcode format only)
        # Assume UK format means UK country
        return {
            'lat': None,
            'lng': None,
            'formatted_address': postcode.upper(),
            'valid': True,
            'is_uk': True,  # Assume UK if format matches
            'components': {
                'country': 'GB',
                'postal_code': postcode.upper(),
            }
        }
    
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'address': postcode,
        'components': 'country:GB',  # UK only - restrict to UK
        'key': api_key,
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK' and data.get('results'):
                result = data['results'][0]
                location = result['geometry']['location']
                
                # Extract address components
                components = {}
                country_code = None
                for component in result.get('address_components', []):
                    types = component.get('types', [])
                    if 'postal_code' in types:
                        components['postal_code'] = component.get('long_name')
                    if 'postal_town' in types or 'locality' in types:
                        components['town'] = component.get('long_name')
                    if 'administrative_area_level_2' in types:
                        components['county'] = component.get('long_name')
                    if 'country' in types:
                        components['country'] = component.get('long_name')
                        country_code = component.get('short_name')
                
                # CRITICAL: Check if country is UK (GB)
                is_uk = country_code == 'GB'
                
                return {
                    'lat': location.get('lat'),
                    'lng': location.get('lng'),
                    'formatted_address': result.get('formatted_address', postcode.upper()),
                    'valid': is_uk,  # Only valid if UK
                    'is_uk': is_uk,
                    'components': components,
                    'country_code': country_code,
                }
            elif data.get('status') in ['ZERO_RESULTS', 'INVALID_REQUEST']:
                # Postcode not found or invalid
                return {
                    'lat': None,
                    'lng': None,
                    'formatted_address': postcode.upper(),
                    'valid': False,
                    'is_uk': False,
                    'components': {},
                    'error': 'Postcode not found in UK',
                }
    except Exception as e:
        # Log error but don't break the flow
        # In production, use proper logging: logger.error(f"Geocoding error: {e}")
        pass
    
    # Fallback: return None if API call failed
    return None


def geocode_postcode(postcode):
    """
    Geocode a UK postcode (cached 24h). See _geocode_postcode_uncached for behaviour.
    """
    normalized = (postcode or '').upper().replace(' ', '').strip()
    if not normalized:
        return _geocode_postcode_uncached(postcode)
    cache_key = f'geocode_postcode_{normalized}'
    result = cache.get(cache_key)
    if result is not None:
        return result
    result = _geocode_postcode_uncached(postcode)
    if result is not None:
        cache.set(cache_key, result, 86400)  # 24h
    return result


def get_address_autocomplete(query, api_key=None):
    """
    Get address suggestions using Google Places API autocomplete (cached 1h by query).
    """
    api_key = api_key or getattr(settings, 'GOOGLE_PLACES_API_KEY', None) or getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
    if not query or not query.strip():
        return []
    cache_key = f'addr_autocomplete_{query.strip()[:80]}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    result = _get_address_autocomplete_uncached(query, api_key)
    if result is not None:
        cache.set(cache_key, result, 3600)  # 1h
    return result if result is not None else []


def _get_address_autocomplete_uncached(query, api_key=None):
    api_key = api_key or getattr(settings, 'GOOGLE_PLACES_API_KEY', None) or getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
    if not api_key:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Google Maps API key not configured. Please add GOOGLE_MAPS_API_KEY or GOOGLE_PLACES_API_KEY to your .env file.")
        return []
    
    url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
    params = {
        'input': query,
        'key': api_key,
        'components': 'country:gb',  # UK only
        # Remove types restriction to get all results (addresses, establishments, etc.)
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        # Log request details
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Google Places Autocomplete request: query='{query}', url={url}")
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Log API response for debugging
            logger.info(f"Google Places Autocomplete response: status={data.get('status')}, predictions={len(data.get('predictions', []))}")
            
            if data.get('status') == 'OK':
                predictions = data.get('predictions', [])
                # Format results for easier use
                formatted_results = []
                for prediction in predictions:
                    formatted_results.append({
                        'place_id': prediction.get('place_id'),
                        'description': prediction.get('description'),
                        'structured_formatting': prediction.get('structured_formatting', {}),
                        'types': prediction.get('types', []),
                    })
                logger.info(f"Returning {len(formatted_results)} formatted results")
                return formatted_results
            elif data.get('status') == 'ZERO_RESULTS':
                logger.info(f"No results found for query: {query}")
                return []
            else:
                # Log other statuses (INVALID_REQUEST, OVER_QUERY_LIMIT, etc.)
                error_msg = data.get('error_message', 'No error message')
                logger.warning(f"Google Places Autocomplete status: {data.get('status')}, error_message: {error_msg}")
                return []
        else:
            logger.error(f"Google Places API returned non-200 status: {response.status_code}")
            logger.error(f"Response text: {response.text[:500]}")
            return []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Autocomplete error: {e}", exc_info=True)
    return []


def get_place_details(place_id, api_key=None):
    """
    Get full address details from Google Places API (cached 24h by place_id).
    """
    if not place_id:
        return None
    cache_key = f'place_details_{place_id}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    result = _get_place_details_uncached(place_id, api_key)
    if result is not None:
        cache.set(cache_key, result, 86400)  # 24h
    return result


def _get_place_details_uncached(place_id, api_key=None):
    api_key = api_key or getattr(settings, 'GOOGLE_PLACES_API_KEY', None) or getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
    if not api_key:
        return None
    url = 'https://maps.googleapis.com/maps/api/place/details/json'
    params = {
        'place_id': place_id,
        'key': api_key,
        'fields': 'formatted_address,address_components,geometry',
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK' and data.get('result'):
                result = data['result']
                components = {}
                
                # Extract address components
                for component in result.get('address_components', []):
                    types = component.get('types', [])
                    if 'street_number' in types:
                        components['street_number'] = component.get('long_name')
                    if 'route' in types:
                        components['route'] = component.get('long_name')
                    if 'locality' in types or 'postal_town' in types:
                        components['city'] = component.get('long_name')
                    if 'postal_code' in types:
                        components['postcode'] = component.get('long_name')
                    if 'country' in types:
                        components['country'] = component.get('long_name')
                
                location = result.get('geometry', {}).get('location', {})
                
                # Build address
                address_line1 = ''
                if components.get('street_number'):
                    address_line1 += components['street_number'] + ' '
                if components.get('route'):
                    address_line1 += components['route']
                address_line1 = address_line1.strip()
                
                return {
                    'address_line1': address_line1 or result.get('formatted_address', '').split(',')[0],
                    'address_line2': '',
                    'city': components.get('city', ''),
                    'postcode': components.get('postcode', ''),
                    'country': components.get('country', 'United Kingdom'),
                    'lat': location.get('lat'),
                    'lng': location.get('lng'),
                    'formatted_address': result.get('formatted_address', ''),
                }
    except Exception:
        pass
    return None


def validate_postcode_with_google(postcode):
    """
    Validate UK postcode using Google Maps API.
    This provides both format validation and existence verification.
    IMPORTANT: Only accepts UK postcodes - rejects non-UK locations.
    
    Args:
        postcode: UK postcode string
    
    Returns:
        dict: {
            'valid': bool,
            'formatted': str,
            'lat': float or None,
            'lng': float or None,
            'formatted_address': str or None,
            'is_uk': bool,
            'error': str or None,
        }
    """
    from .validators import validate_uk_postcode
    
    # First, validate format (UK postcode format)
    try:
        formatted_postcode = validate_uk_postcode(postcode)
    except Exception:
        return {
            'valid': False,
            'formatted': postcode.upper(),
            'lat': None,
            'lng': None,
            'formatted_address': None,
            'is_uk': False,
            'error': 'Invalid UK postcode format. MultiBook currently operates only in the UK.',
        }
    
    # Then, verify with Google Maps API (check country is UK)
    geocode_result = geocode_postcode(formatted_postcode)
    
    if geocode_result and geocode_result.get('valid') and geocode_result.get('is_uk'):
        # Valid UK postcode
        return {
            'valid': True,
            'formatted': formatted_postcode,
            'lat': geocode_result.get('lat'),
            'lng': geocode_result.get('lng'),
            'formatted_address': geocode_result.get('formatted_address'),
            'components': geocode_result.get('components', {}),
            'is_uk': True,
        }
    elif geocode_result and not geocode_result.get('is_uk'):
        # Postcode found but not in UK
        country = geocode_result.get('country_code', 'Unknown')
        return {
            'valid': False,
            'formatted': formatted_postcode,
            'lat': None,
            'lng': None,
            'formatted_address': geocode_result.get('formatted_address'),
            'is_uk': False,
            'error': f'This postcode is not in the UK. MultiBook currently operates only in the UK. Please enter a UK postcode.',
        }
    elif geocode_result is None:
        # API call failed, but format is valid - accept it (assume UK)
        return {
            'valid': True,
            'formatted': formatted_postcode,
            'lat': None,
            'lng': None,
            'formatted_address': formatted_postcode,
            'is_uk': True,
            'note': 'Format validated, but could not verify with Google Maps API',
        }
    else:
        # Format valid but not found in Google Maps
        return {
            'valid': False,
            'formatted': formatted_postcode,
            'lat': None,
            'lng': None,
            'formatted_address': None,
            'is_uk': False,
            'error': 'Postcode not found. MultiBook currently operates only in the UK. Please enter a valid UK postcode.',
        }


def validate_address(address_data):
    """
    Validate address using Google Places API.
    
    Args:
        address_data: Address dictionary with fields like:
            {
                'address_line1': str,
                'address_line2': str,
                'city': str,
                'postcode': str,
                'country': str (default: GB),
            }
    
    Returns:
        dict: Validated address data or original data if validation fails
    """
    # For Week 3, basic validation - can be enhanced later
    # The address validation can use Google Places API Place Details
    # if a place_id is provided from autocomplete
    
    postcode = address_data.get('postcode')
    if postcode:
        validation_result = validate_postcode_with_google(postcode)
        address_data['postcode_validated'] = validation_result.get('valid', False)
        if validation_result.get('formatted'):
            address_data['postcode'] = validation_result['formatted']
    
    return address_data
