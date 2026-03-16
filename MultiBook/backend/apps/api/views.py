"""
API root view and guest access endpoints.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
# Import guest access views for URL routing
from apps.subscriptions.views import guest_subscription_view, guest_subscription_by_token_view
from apps.orders.views import guest_order_view, guest_order_by_token_view

# Export guest views for URL routing
__all__ = [
    'api_root',
    'guest_subscription_view',
    'guest_subscription_by_token_view',
    'guest_order_view',
    'guest_order_by_token_view',
]


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """
    API root endpoint showing available API versions and endpoints.
    GET /api/
    """
    from django.utils import timezone
    
    return Response({
        'success': True,
        'data': {
            'name': 'MultiBook API',
            'version': '1.0.0',
            'api_version': 'v1',
            'documentation': {
                'swagger': '/api/docs/',
                'redoc': '/api/redoc/',
                'schema': '/api/schema/',
            },
            'endpoints': {
                'public': {
                    'services': {
                        'list': '/api/svc/',
                        'detail': '/api/svc/{id}/',
                        'by_postcode': '/api/svc/by-postcode/?postcode=SW1A1AA',
                    },
                    'staff': {
                        'list': '/api/stf/',
                        'detail': '/api/stf/{id}/',
                        'by_postcode': '/api/stf/by-postcode/?postcode=SW1A1AA',
                    },
                    'bookings': {
                        'appointments': '/api/bkg/appointments/',
                        'subscriptions': '/api/bkg/subscriptions/',
                        'orders': '/api/bkg/orders/',
                    },
                    'guest_access': {
                        'description': 'Guest order/subscription access (NO AUTH REQUIRED)',
                        'orders': {
                            'get_by_number': '/api/bkg/guest/order/{order_number}/',
                            'get_by_token': '/api/bkg/guest/order/token/{tracking_token}/',
                        },
                        'subscriptions': {
                            'get_by_number': '/api/bkg/guest/subscription/{subscription_number}/',
                            'get_by_token': '/api/bkg/guest/subscription/token/{tracking_token}/',
                        },
                        'account_linking': {
                            'check_email': '/api/bkg/guest/check-email/',
                            'link_order_login': '/api/bkg/guest/order/{order_number}/link-login/',
                            'link_order_register': '/api/bkg/guest/order/{order_number}/link-register/',
                            'link_subscription_login': '/api/bkg/guest/subscription/{subscription_number}/link-login/',
                            'link_subscription_register': '/api/bkg/guest/subscription/{subscription_number}/link-register/',
                            'description': 'Optional post-order account linking (Day 6 feature)',
                        },
                    },
                    'slots': '/api/slots/',
                    'address': {
                        'autocomplete': '/api/addr/autocomplete/?query=10+Downing+Street',
                        'validate': '/api/addr/validate/',
                        'description': 'Google Places API integration for address autocomplete',
                    },
                    'auth': {
                        'register': '/api/aut/register/',
                        'login': '/api/aut/login/',
                        'logout': '/api/aut/logout/',
                        'token_refresh': '/api/aut/token/refresh/',
                        'password_reset': '/api/aut/password-reset/request/',
                        'email_verification': '/api/aut/verify-email/request/',
                    },
                },
                'protected': {
                    'customer': {
                        'profile': '/api/cus/profile/',
                        'appointments': '/api/cus/appointments/',
                        'subscriptions': '/api/cus/subscriptions/',
                        'orders': '/api/cus/orders/',
                        'addresses': '/api/cus/addresses/',
                    },
                    'staff': {
                        'dashboard': '/api/st/dashboard/',
                        'jobs': '/api/st/jobs/',
                        'schedule': '/api/st/schedule/',
                    },
                    'manager': {
                        'dashboard': '/api/man/dashboard/',
                        'appointments': '/api/man/appointments/',
                        'staff': '/api/man/staff/',
                        'customers': '/api/man/customers/',
                    },
                    'admin': {
                        'dashboard': '/api/ad/dashboard/',
                        'appointments': '/api/ad/appointments/',
                        'staff': '/api/ad/staff/',
                        'customers': '/api/ad/customers/',
                        'managers': '/api/ad/managers/',
                    },
                }
            }
        },
        'meta': {
            'timestamp': timezone.now().isoformat(),
        }
    })
