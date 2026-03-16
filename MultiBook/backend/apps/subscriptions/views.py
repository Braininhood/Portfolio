"""
Subscriptions app views.
Subscription and SubscriptionAppointment viewsets with guest checkout support.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from datetime import datetime, timedelta, time as time_obj
from dateutil.relativedelta import relativedelta  # Requires python-dateutil (already in requirements.txt)
from apps.core.permissions import IsCustomer, IsAdminOrManager, IsOwnerOrAdmin
from apps.core.utils import can_cancel_or_reschedule
from .models import Subscription, SubscriptionAppointment, SubscriptionAppointmentChangeRequest
from .serializers import (
    SubscriptionSerializer, SubscriptionListSerializer,
    SubscriptionAppointmentSerializer, SubscriptionCreateSerializer
)
from apps.customers.models import Customer
from apps.services.models import Service
from apps.staff.models import Staff


class SubscriptionPublicViewSet(viewsets.ModelViewSet):
    """
    Public Subscription ViewSet (guest checkout supported).
    Public: POST (create subscription - NO LOGIN REQUIRED)
    GET (by subscription_number or tracking_token - guest access)
    POST /api/bkg/subscriptions/
    GET /api/bkg/guest/subscription/{subscription_number}/
    """
    queryset = Subscription.objects.select_related('service', 'staff', 'customer').prefetch_related(
        'subscription_appointments'
    ).all()
    serializer_class = SubscriptionSerializer
    permission_classes = [AllowAny]  # Public write access for guest checkout
    
    def get_serializer_class(self):
        """Use create serializer for POST, detail serializer for GET."""
        if self.action == 'create':
            return SubscriptionCreateSerializer
        return SubscriptionSerializer
    
    def create(self, request, *args, **kwargs):
        """Create subscription (supports guest checkout)."""
        serializer = SubscriptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract data
        service_id = serializer.validated_data['service_id']
        staff_id = serializer.validated_data.get('staff_id')
        frequency = serializer.validated_data['frequency']
        duration_months = serializer.validated_data['duration_months']
        start_date = serializer.validated_data['start_date']
        price_per_appointment = serializer.validated_data['price_per_appointment']
        customer_id = serializer.validated_data.get('customer_id')
        
        # Handle guest customer
        customer = None
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                pass
        elif serializer.validated_data.get('guest_email'):
            # Create or get guest customer
            guest_email = serializer.validated_data['guest_email']
            guest_name = serializer.validated_data.get('guest_name', '')
            guest_phone = serializer.validated_data.get('guest_phone', '')
            
            customer, created = Customer.objects.get_or_create(
                email=guest_email,
                defaults={
                    'name': guest_name,
                    'phone': guest_phone,
                    'user': None,  # Guest customer, no user account
                }
            )
        
        try:
            service = Service.objects.get(id=service_id, is_active=True)
        except Service.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Service not found',
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Assign staff or find available staff
        staff = None
        if staff_id:
            try:
                staff = Staff.objects.get(id=staff_id, is_active=True)
            except Staff.DoesNotExist:
                pass
        
        if not staff:
            # TODO: Auto-assign staff based on postcode/area
            # For now, get first available staff for this service
            staff = Staff.objects.filter(
                is_active=True,
                staff_services__service=service,
                staff_services__is_active=True
            ).first()
        
        # Calculate end_date
        end_date = start_date + relativedelta(months=duration_months)
        
        # Calculate total appointments based on frequency
        total_appointments = 0
        if frequency == 'weekly':
            total_appointments = duration_months * 4
        elif frequency == 'biweekly':
            total_appointments = duration_months * 2
        elif frequency == 'monthly':
            total_appointments = duration_months
        
        # Calculate total price
        total_price = price_per_appointment * total_appointments
        
        # Create subscription
        subscription = Subscription.objects.create(
            customer=customer,
            service=service,
            staff=staff,
            frequency=frequency,
            duration_months=duration_months,
            start_date=start_date,
            end_date=end_date,
            next_appointment_date=start_date,
            status='active',
            total_appointments=total_appointments,
            completed_appointments=0,
            price_per_appointment=price_per_appointment,
            total_price=total_price,
            payment_status='pending',
            cancellation_policy_hours=24,
            # Guest fields
            guest_email=serializer.validated_data.get('guest_email') if not customer or not customer.user else None,
            guest_name=serializer.validated_data.get('guest_name') if not customer or not customer.user else None,
            guest_phone=serializer.validated_data.get('guest_phone') if not customer or not customer.user else None,
            address_line1=serializer.validated_data.get('address_line1'),
            address_line2=serializer.validated_data.get('address_line2'),
            city=serializer.validated_data.get('city'),
            postcode=serializer.validated_data.get('postcode'),
            country=serializer.validated_data.get('country', 'United Kingdom'),
        )
        
        # Generate subscription appointments automatically
        try:
            from .subscription_utils import generate_subscription_appointments
            generate_subscription_appointments(subscription)
        except Exception as e:
            # Log error but don't fail subscription creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating subscription appointments: {str(e)}", exc_info=True)
        
        # Serialize response
        subscription_serializer = SubscriptionSerializer(subscription)
        
        return Response({
            'success': True,
            'data': subscription_serializer.data,
            'meta': {
                'message': 'Subscription created successfully',
                'guest_checkout': subscription.is_guest_subscription,
                'subscription_number': subscription.subscription_number,
                'tracking_token': subscription.tracking_token,
            }
        }, status=status.HTTP_201_CREATED)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    Subscription ViewSet (protected - customer/admin/manager).
    Customer: GET own subscriptions, pause, cancel
    Admin/Manager: Full CRUD
    GET, PUT, PATCH, DELETE /api/cus/subscriptions/ or /api/ad/subscriptions/
    """
    queryset = Subscription.objects.select_related('service', 'staff', 'customer').prefetch_related(
        'subscription_appointments'
    ).all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use simplified serializer for list views."""
        if self.action == 'list':
            return SubscriptionListSerializer
        return SubscriptionSerializer
    
    def get_queryset(self):
        """Filter by current user if customer, or all if admin/manager."""
        queryset = super().get_queryset()
        
        # Customer can only see their own subscriptions
        if self.request.user.role == 'customer':
            try:
                customer = Customer.objects.get(user=self.request.user)
                queryset = queryset.filter(customer=customer)
            except Customer.DoesNotExist:
                queryset = queryset.none()
        
        # Manager can see subscriptions within their scope
        elif self.request.user.role == 'manager':
            # TODO: Implement manager scope filtering
            pass
        
        # Admin can see all subscriptions
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

    def list(self, request, *args, **kwargs):
        """List subscriptions with response shape { success, data, meta } for frontend."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {'count': queryset.count()},
        }, status=status.HTTP_200_OK)

    def get_paginated_response(self, data):
        """Return paginated response in shape { success, data, meta }."""
        pagination = self.paginator
        return Response({
            'success': True,
            'data': data,
            'meta': {
                'count': pagination.page.paginator.count,
                'next': pagination.get_next_link(),
                'previous': pagination.get_previous_link(),
            },
        }, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        """Return subscription detail in shape { success, data } for frontend."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def get_permissions(self):
        """Override permissions for write operations."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            if self.request.user.role == 'customer':
                # Customer can only manage their own subscriptions
                return [IsAuthenticated()]
            return [IsAdminOrManager()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'], url_path='pause')
    def pause(self, request, pk=None):
        """Pause subscription (customer can pause their own subscription)."""
        subscription = self.get_object()
        
        if subscription.status != 'active':
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': 'Only active subscriptions can be paused',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subscription.status = 'paused'
        subscription.save()
        
        return Response({
            'success': True,
            'data': SubscriptionSerializer(subscription).data,
            'meta': {
                'message': 'Subscription paused successfully',
            }
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        """Activate (resume) a paused subscription (customer can activate their own)."""
        subscription = self.get_object()
        
        if subscription.status != 'paused':
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': 'Only paused subscriptions can be activated',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subscription.status = 'active'
        subscription.save()
        
        return Response({
            'success': True,
            'data': SubscriptionSerializer(subscription).data,
            'meta': {
                'message': 'Subscription activated successfully',
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Cancel subscription (customer can cancel their own subscription)."""
        subscription = self.get_object()
        
        if subscription.status in ['cancelled', 'completed']:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': 'Subscription is already cancelled or completed',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subscription.status = 'cancelled'
        subscription.save()
        
        return Response({
            'success': True,
            'data': SubscriptionSerializer(subscription).data,
            'meta': {
                'message': 'Subscription cancelled successfully',
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='appointments/(?P<appointment_id>[^/.]+)/cancel')
    def cancel_appointment(self, request, pk=None, appointment_id=None):
        """Cancel a specific subscription appointment (24h policy enforced)."""
        subscription = self.get_object()
        
        try:
            subscription_appointment = SubscriptionAppointment.objects.get(
                subscription=subscription,
                id=appointment_id
            )
        except SubscriptionAppointment.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Subscription appointment not found',
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if appointment can be cancelled (24h policy)
        if not subscription_appointment.can_cancel:
            return Response({
                'success': False,
                'error': {
                    'code': 'CANCELLATION_NOT_ALLOWED',
                    'message': f'Appointment cannot be cancelled within {subscription.cancellation_policy_hours} hours of scheduled time. Deadline was {subscription_appointment.cancellation_deadline}',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already cancelled
        if subscription_appointment.status == 'cancelled':
            return Response({
                'success': False,
                'error': {
                    'code': 'ALREADY_CANCELLED',
                    'message': 'Appointment is already cancelled',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cancel the appointment
        subscription_appointment.status = 'cancelled'
        subscription_appointment.save()
        
        # Also cancel the linked appointment if it exists
        if subscription_appointment.appointment:
            subscription_appointment.appointment.status = 'cancelled'
            subscription_appointment.appointment.save()
        
        return Response({
            'success': True,
            'data': SubscriptionAppointmentSerializer(subscription_appointment).data,
            'meta': {
                'message': 'Subscription appointment cancelled successfully',
            }
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='appointments/(?P<appointment_id>[^/.]+)/request-change')
    def request_change_appointment(self, request, pk=None, appointment_id=None):
        """Request a date/time change for a single subscription visit (24h policy enforced)."""
        subscription = self.get_object()
        try:
            subscription_appointment = SubscriptionAppointment.objects.get(
                subscription=subscription,
                id=appointment_id
            )
        except SubscriptionAppointment.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Subscription visit not found',
                }
            }, status=status.HTTP_404_NOT_FOUND)
        if request.user.role == 'customer':
            try:
                customer = Customer.objects.get(user=request.user)
                if subscription.customer != customer:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'PERMISSION_DENIED',
                            'message': 'You can only request changes for your own subscription',
                        }
                    }, status=status.HTTP_403_FORBIDDEN)
            except Customer.DoesNotExist:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Customer profile not found',
                    }
                }, status=status.HTTP_404_NOT_FOUND)
        if not subscription_appointment.can_reschedule:
            return Response({
                'success': False,
                'error': {
                    'code': 'RESCHEDULE_NOT_ALLOWED',
                    'message': f'Changes are not allowed within {subscription.cancellation_policy_hours} hours of the scheduled time.',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        if subscription_appointment.status == 'cancelled':
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': 'Cannot request change for a cancelled visit',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        new_date = request.data.get('scheduled_date')
        new_time = request.data.get('scheduled_time')
        reason = request.data.get('reason', '')
        if not new_date:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'scheduled_date is required',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        requested_time_parsed = None
        if new_time and isinstance(new_time, str):
            parts = new_time.strip().split(':')
            if len(parts) >= 2:
                try:
                    h, m = int(parts[0]), int(parts[1])
                    requested_time_parsed = time_obj(h, m, 0)
                except (ValueError, TypeError):
                    pass
        elif new_time:
            requested_time_parsed = new_time
        change_request = SubscriptionAppointmentChangeRequest.objects.create(
            subscription_appointment=subscription_appointment,
            requested_date=new_date,
            requested_time=requested_time_parsed,
            reason=reason or None,
            status='pending',
        )
        try:
            from apps.notifications.email_service import send_subscription_visit_change_request_submitted
            send_subscription_visit_change_request_submitted(change_request)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning('Failed to send subscription visit change request email: %s', e)
        return Response({
            'success': True,
            'data': SubscriptionAppointmentSerializer(subscription_appointment).data,
            'meta': {
                'message': 'Change request submitted. We will review and contact you.',
            }
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def guest_subscription_view(request, subscription_number):
    """
    Get guest subscription by subscription number (public).
    GET /api/bkg/guest/subscription/{subscription_number}/
    """
    try:
        subscription = Subscription.objects.get(subscription_number=subscription_number)
    except Subscription.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Subscription not found',
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = SubscriptionSerializer(subscription)
    return Response({
        'success': True,
        'data': serializer.data,
        'meta': {}
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def guest_subscription_by_token_view(request, tracking_token):
    """
    Get guest subscription by tracking token (public).
    GET /api/bkg/guest/subscription/token/{tracking_token}/
    """
    try:
        subscription = Subscription.objects.get(tracking_token=tracking_token)
    except Subscription.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Subscription not found',
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = SubscriptionSerializer(subscription)
    return Response({
        'success': True,
        'data': serializer.data,
        'meta': {}
    }, status=status.HTTP_200_OK)
