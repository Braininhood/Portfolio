"""
API URL routing with security prefixes.

All endpoints use shortened prefixes for security:
- Public endpoints: /api/svc/, /api/stf/, /api/bkg/, /api/addr/, /api/aut/, /api/slots/, /api/pay/
- Protected endpoints: /api/cus/, /api/st/, /api/man/, /api/ad/
"""
from django.urls import path, include
from . import views
from apps.core.views import upload_file
from apps.subscriptions.views import guest_subscription_view, guest_subscription_by_token_view
from apps.orders.views import (
    guest_order_view, 
    guest_order_by_token_view,
    guest_check_email_view,
    guest_order_link_login_view,
    guest_order_link_register_view,
    guest_order_cancel_view,
    guest_order_request_change_view,
)

app_name = 'api'

urlpatterns = [
    # API Root
    path('', views.api_root, name='root'),
    
    # Public Endpoints (Security prefixes)
    path('svc/', include('apps.services.urls')),  # Services (/api/svc/)
    path('aut/', include('apps.accounts.urls')),  # Authentication (/api/aut/)
    path('stf/', include('apps.staff.urls')),  # Staff public listing (/api/stf/)
    path('slots/', include('apps.appointments.urls_slots')),  # Available slots (/api/slots/)
    path('coupons/', include('apps.coupons.urls')),  # Coupons (/api/coupons/)
    
    # Bookings/Orders (Public - Guest Checkout Supported)
    # Note: All booking-related endpoints under /api/bkg/ prefix
    path('bkg/appointments/', include('apps.appointments.urls')),  # Appointments (/api/bkg/appointments/)
    path('bkg/subscriptions/', include('apps.subscriptions.urls')),  # Subscriptions (/api/bkg/subscriptions/)
    path('bkg/orders/', include('apps.orders.urls')),  # Orders (/api/bkg/orders/)
    
    # Guest access endpoints (for subscriptions and orders by number/token)
    path('bkg/guest/subscription/<str:subscription_number>/', 
         guest_subscription_view, name='guest-subscription-by-number'),
    path('bkg/guest/subscription/token/<str:tracking_token>/', 
         guest_subscription_by_token_view, name='guest-subscription-by-token'),
    path('bkg/guest/order/<str:order_number>/', 
         guest_order_view, name='guest-order-by-number'),
    path('bkg/guest/order/<str:order_number>/cancel/', 
         guest_order_cancel_view, name='guest-order-cancel'),
    path('bkg/guest/order/<str:order_number>/request-change/', 
         guest_order_request_change_view, name='guest-order-request-change'),
    path('bkg/guest/order/token/<str:tracking_token>/', 
         guest_order_by_token_view, name='guest-order-by-token'),
    
    # Guest account linking endpoints
    path('bkg/guest/check-email/', 
         guest_check_email_view, name='guest-check-email'),
    path('bkg/guest/order/<str:order_number>/link-login/', 
         guest_order_link_login_view, name='guest-order-link-login'),
    path('bkg/guest/order/<str:order_number>/link-register/', 
         guest_order_link_register_view, name='guest-order-link-register'),
    
    path('addr/', include('apps.core.urls_address')),  # Address (Google Places)
    path('calendar/', include('apps.calendar_sync.urls')),  # Calendar Sync (OAuth + .ics) (/api/calendar/)
    path('core/upload/', upload_file, name='upload-file'),  # File upload to Supabase Storage (/api/core/upload/)
    # path('pay/', include('apps.payments.urls_public')),  # Payments - TODO
    
    # Protected Endpoints (Role-based security prefixes)
    path('cus/', include('apps.customers.urls_protected')),  # Customer endpoints (/api/cus/)
    path('ad/', include('apps.customers.urls_admin')),  # Admin customer endpoints (/api/ad/customers/)
    path('ad/', include('apps.services.urls_admin')),  # Admin service endpoints (/api/ad/services/, /api/ad/categories/)
    path('ad/', include('apps.accounts.urls_admin')),  # Admin manager endpoints (/api/ad/managers/)
    path('ad/', include('apps.coupons.urls_admin')),  # Admin coupon endpoints (/api/ad/coupons/)
    path('ad/', include('apps.orders.urls_admin')),  # Admin order endpoints (/api/ad/orders/, /api/ad/change-requests/)
    path('ad/', include('apps.appointments.urls_admin')),  # Admin appointment endpoints (/api/ad/appointments/)
    path('ad/reports/', include('apps.reports.urls')),  # Admin reports endpoints (/api/ad/reports/)
    path('ad/routes/', include('apps.core.urls_route')),  # Route optimization (/api/ad/routes/)
    path('st/', include('apps.staff.urls_staff')),  # Staff self-service endpoints (/api/st/)
    path('', include('apps.staff.urls_protected')),  # Staff admin/manager endpoints (/api/ad/, /api/man/)
]
