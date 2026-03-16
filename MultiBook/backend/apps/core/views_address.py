"""
Address API views (public endpoints).
Google Places API integration for address autocomplete and validation.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .address import (
    get_address_autocomplete,
    validate_postcode_with_google,
    geocode_postcode,
    get_place_details
)


@api_view(['GET'])
@permission_classes([AllowAny])
def address_autocomplete_view(request):
    """
    Get address suggestions using Google Places API autocomplete (public).
    GET /api/addr/autocomplete/?query=SW1A+1AA
    
    Args:
        query: Search query (postcode or address)
    
    Returns:
        {
            'success': true,
            'data': [
                {
                    'place_id': str,
                    'description': str,
                    'structured_formatting': dict,
                    'types': list,
                }
            ]
        }
    """
    query = request.query_params.get('query')
    
    if not query:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Query parameter is required',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get autocomplete suggestions
    try:
        import logging
        from django.conf import settings
        logger = logging.getLogger(__name__)
        logger.info(f"Address autocomplete request: query='{query}'")
        
        # Check if API key is configured
        api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', None) or getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
        if not api_key:
            logger.warning("Google Maps API key not configured")
            return Response({
                'success': False,
                'error': {
                    'code': 'API_KEY_MISSING',
                    'message': 'Google Maps API key is not configured. Please add GOOGLE_MAPS_API_KEY to backend/.env file.',
                },
                'data': []
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        suggestions = get_address_autocomplete(query)
        
        logger.info(f"Returning {len(suggestions)} suggestions for query '{query}'")
        
        return Response({
            'success': True,
            'data': suggestions,
            'meta': {
                'count': len(suggestions),
                'query': query,
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in address_autocomplete_view: {e}", exc_info=True)
        
        return Response({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': f'An error occurred while fetching address suggestions: {str(e)}',
            },
            'data': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def address_validate_view(request):
    """
    Validate and get full address details from place_id or postcode (public).
    GET /api/addr/validate/?place_id=xxx or GET /api/addr/validate/?postcode=SW1A1AA
    POST /api/addr/validate/ (with body)
    
    Query params (GET) or Body (POST):
        place_id: str (optional),
        postcode: str (optional),
    
    Returns:
        {
            'success': true,
            'data': {
                'address_line1': str,
                'address_line2': str,
                'city': str,
                'postcode': str,
                'country': str,
                'lat': float,
                'lng': float,
                'formatted_address': str,
            }
        }
    """
    # Support both GET (query params) and POST (body)
    if request.method == 'GET':
        place_id = request.query_params.get('place_id')
        postcode = request.query_params.get('postcode')
    else:
        place_id = request.data.get('place_id')
        postcode = request.data.get('postcode')
    
    if not place_id and not postcode:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Either place_id or postcode is required',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # If place_id provided, get place details
    if place_id:
        place_details = get_place_details(place_id)
        if place_details:
            return Response({
                'success': True,
                'data': place_details,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Place not found',
                }
            }, status=status.HTTP_404_NOT_FOUND)
    
    # If postcode provided, geocode it
    if postcode:
        validation_result = validate_postcode_with_google(postcode)
        
        if not validation_result.get('valid') or not validation_result.get('is_uk'):
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_POSTCODE',
                    'message': validation_result.get('error', 'Invalid UK postcode'),
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract address components from geocoding result
        components = validation_result.get('components', {})
        formatted_address = validation_result.get('formatted_address', '')
        
        # Try to extract address components (best effort)
        address_data = {
            'postcode': validation_result.get('formatted', postcode),
            'country': 'United Kingdom',
            'lat': validation_result.get('lat'),
            'lng': validation_result.get('lng'),
            'formatted_address': formatted_address,
            'address_line1': components.get('street_number', '') + ' ' + components.get('route', ''),
            'address_line2': '',
            'city': components.get('locality') or components.get('postal_town') or components.get('city', ''),
        }
        
        # Clean up address_line1
        address_data['address_line1'] = address_data['address_line1'].strip()
        if not address_data['address_line1']:
            address_data['address_line1'] = formatted_address.split(',')[0] if formatted_address else postcode
        
        return Response({
            'success': True,
            'data': address_data,
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'error': {
            'code': 'VALIDATION_ERROR',
            'message': 'Invalid request',
        }
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def address_config_view(request):
    """
    Get address/Google Maps configuration (public).
    Returns API key for frontend use (if configured).
    GET /api/addr/config/
    
    Returns:
        {
            'success': true,
            'data': {
                'api_key': str (if configured),
                'maps_enabled': bool,
            }
        }
    """
    from django.conf import settings
    
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None) or getattr(settings, 'GOOGLE_PLACES_API_KEY', None)
    
    return Response({
        'success': True,
        'data': {
            'api_key': api_key if api_key else None,
            'maps_enabled': bool(api_key),
        }
    }, status=status.HTTP_200_OK)
