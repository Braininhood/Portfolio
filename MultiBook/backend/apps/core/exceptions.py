"""
Custom exception handlers for Django REST Framework.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger('apps')


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    All errors follow the standard format:
    {
        "success": false,
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable message",
            "details": {...}
        },
        "meta": {
            "timestamp": "..."
        }
    }
    """
    from django.utils import timezone
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If response is None, it means Django raised an exception
    if response is not None:
        # Extract error details from response
        error_details = {}
        error_message = 'An error occurred'
        
        if isinstance(response.data, dict):
            # Handle DRF validation errors
            if 'detail' in response.data:
                error_message = str(response.data['detail'])
            elif 'non_field_errors' in response.data:
                error_message = str(response.data['non_field_errors'][0]) if response.data['non_field_errors'] else 'Validation error'
                error_details = response.data
            else:
                # Field-specific validation errors
                error_details = response.data
                if response.data:
                    first_error = list(response.data.values())[0]
                    if isinstance(first_error, list) and first_error:
                        error_message = str(first_error[0])
                    else:
                        error_message = 'Validation error'
        else:
            error_details = {'detail': str(response.data)}
            error_message = str(response.data)
        
        # Customize the response data structure
        custom_response_data = {
            'success': False,
            'error': {
                'code': f'HTTP_{response.status_code}',
                'message': error_message,
                'details': error_details,
            },
            'meta': {
                'timestamp': timezone.now().isoformat(),
            }
        }

        # Handle specific error codes with better messages
        if response.status_code == 400:
            custom_response_data['error']['code'] = 'VALIDATION_ERROR'
            if not error_message or error_message == 'An error occurred':
                custom_response_data['error']['message'] = 'Validation error. Please check your input.'
        elif response.status_code == 401:
            custom_response_data['error']['code'] = 'UNAUTHORIZED'
            custom_response_data['error']['message'] = 'Authentication required. Please login.'
        elif response.status_code == 403:
            custom_response_data['error']['code'] = 'FORBIDDEN'
            custom_response_data['error']['message'] = 'Permission denied. You do not have access to this resource.'
        elif response.status_code == 404:
            custom_response_data['error']['code'] = 'NOT_FOUND'
            custom_response_data['error']['message'] = 'Resource not found.'
        elif response.status_code == 405:
            custom_response_data['error']['code'] = 'METHOD_NOT_ALLOWED'
            custom_response_data['error']['message'] = 'HTTP method not allowed for this endpoint.'
        elif response.status_code == 429:
            custom_response_data['error']['code'] = 'RATE_LIMIT_EXCEEDED'
            custom_response_data['error']['message'] = 'Rate limit exceeded. Please try again later.'
        elif response.status_code == 500:
            custom_response_data['error']['code'] = 'SERVER_ERROR'
            custom_response_data['error']['message'] = 'Internal server error. Please try again later.'
            logger.error(f"Server error: {exc}", exc_info=True)
        elif response.status_code == 503:
            custom_response_data['error']['code'] = 'SERVICE_UNAVAILABLE'
            custom_response_data['error']['message'] = 'Service temporarily unavailable. Please try again later.'

        response.data = custom_response_data
    else:
        # Handle Django exceptions that don't have REST framework handlers
        from django.utils import timezone
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        response = Response(
            {
                'success': False,
                'error': {
                    'code': 'SERVER_ERROR',
                    'message': 'An unexpected error occurred',
                    'details': {'detail': str(exc)},
                },
                'meta': {
                    'timestamp': timezone.now().isoformat(),
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
