"""
Orders app views.
Order and OrderItem viewsets with guest checkout support.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from datetime import datetime, timedelta, time as time_obj
from django.contrib.auth import get_user_model
from apps.core.permissions import (
    IsCustomer, IsAdminOrManager, IsStaff, IsStaffOrManager, IsOwnerOrAdmin
)
from apps.core.utils import can_cancel_or_reschedule
from .models import Order, OrderItem, ChangeRequest
from .serializers import (
    OrderSerializer, OrderItemSerializer, OrderCreateSerializer, ChangeRequestSerializer
)
from apps.services.models import Service
from apps.staff.models import Staff
from apps.customers.models import Customer

User = get_user_model()


class OrderPublicViewSet(viewsets.ModelViewSet):
    """
    Public Order ViewSet (guest checkout supported - multi-service orders).
    Public: POST (create order - NO LOGIN REQUIRED)
    GET (by order_number or tracking_token - guest access)
    POST /api/bkg/orders/
    GET /api/bkg/guest/order/{order_number}/
    """
    queryset = Order.objects.prefetch_related('items', 'appointments').all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]  # Public write access for guest checkout
    
    def get_serializer_class(self):
        """Use create serializer for POST, detail serializer for GET."""
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        """Create multi-service order (supports guest checkout)."""
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract data
        items_data = serializer.validated_data['items']
        scheduled_date = serializer.validated_data['scheduled_date']
        scheduled_time = serializer.validated_data.get('scheduled_time')
        customer_id = serializer.validated_data.get('customer_id')
        
        # Handle guest customer
        customer = None
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                pass
        elif serializer.validated_data.get('guest_email'):
            # Create or get guest customer; update address when completing booking
            guest_email = serializer.validated_data['guest_email']
            guest_name = serializer.validated_data.get('guest_name', '')
            guest_phone = serializer.validated_data.get('guest_phone', '')
            addr1 = serializer.validated_data.get('address_line1', '')
            addr2 = serializer.validated_data.get('address_line2', '')
            city = serializer.validated_data.get('city', '')
            postcode = serializer.validated_data.get('postcode', '')
            country = serializer.validated_data.get('country', 'United Kingdom')
            
            customer, created = Customer.objects.get_or_create(
                email=guest_email,
                defaults={
                    'name': guest_name,
                    'phone': guest_phone,
                    'user': None,
                    'address_line1': addr1,
                    'address_line2': addr2 or None,
                    'city': city,
                    'postcode': postcode,
                    'country': country,
                }
            )
            if not created and (addr1 or city or postcode):
                customer.name = guest_name or customer.name
                customer.phone = guest_phone or customer.phone
                customer.address_line1 = addr1 or customer.address_line1
                customer.address_line2 = addr2 or customer.address_line2
                customer.city = city or customer.city
                customer.postcode = postcode or customer.postcode
                customer.country = country or customer.country
                customer.save(update_fields=['name', 'phone', 'address_line1', 'address_line2', 'city', 'postcode', 'country'])
        
        # Validate and apply coupon if provided
        coupon_code = serializer.validated_data.get('coupon_code', '').strip().upper()
        coupon = None
        discount_amount = 0
        
        if coupon_code:
            try:
                from apps.coupons.models import Coupon
                coupon = Coupon.objects.get(code__iexact=coupon_code)
                
                # Get service IDs for validation
                service_ids = [item['service_id'] for item in items_data]
                
                # Validate coupon (will calculate discount later after we know total)
                is_valid, error_message = coupon.is_valid(
                    customer=customer,
                    order_amount=0,  # Will validate again after calculating total
                    service_ids=service_ids
                )
                
                if not is_valid:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'INVALID_COUPON',
                            'message': error_message,
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Coupon.DoesNotExist:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'COUPON_NOT_FOUND',
                        'message': 'Coupon code not found',
                    }
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate total price
        total_price = 0
        order_items = []
        
        for item_data in items_data:
            service_id = item_data['service_id']
            quantity = item_data.get('quantity', 1)
            staff_id = item_data.get('staff_id')
            
            try:
                service = Service.objects.get(id=service_id, is_active=True)
            except Service.DoesNotExist:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': f'Service with id {service_id} not found',
                    }
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get staff or find available staff
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
            
            unit_price = service.price
            item_total = unit_price * quantity
            total_price += item_total
            
            order_items.append({
                'service': service,
                'staff': staff,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': item_total,
            })
        
        # Apply coupon discount if valid
        if coupon:
            # Re-validate with actual order amount
            is_valid, error_message = coupon.is_valid(
                customer=customer,
                order_amount=total_price,
                service_ids=[item['service'].id for item in order_items]
            )
            
            if is_valid:
                discount_amount = coupon.calculate_discount(total_price)
                total_price = total_price - discount_amount
            else:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_COUPON',
                        'message': error_message,
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Guest/display fields: always store from payload when provided (for invoices & display)
        # When customer_id is sent (logged-in user), still save guest_* so order has full info
        guest_email = serializer.validated_data.get('guest_email') or (customer.email if customer else None)
        guest_name = serializer.validated_data.get('guest_name') or (customer.name if customer else None)
        guest_phone = serializer.validated_data.get('guest_phone') or (getattr(customer, 'phone', None) if customer else None)
        if guest_email and not guest_name and customer:
            guest_name = customer.name
        if guest_email and not guest_phone and customer:
            guest_phone = getattr(customer, 'phone', None)

        # Create order (pending first so we have pk for signal)
        order = Order.objects.create(
            customer=customer,
            status='pending',
            total_price=total_price,
            deposit_paid=0,
            payment_status='pending',
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            cancellation_policy_hours=24,
            # Guest/display fields (always set so order has full info)
            guest_email=guest_email,
            guest_name=guest_name,
            guest_phone=guest_phone,
            address_line1=serializer.validated_data['address_line1'],
            address_line2=serializer.validated_data.get('address_line2'),
            city=serializer.validated_data['city'],
            postcode=serializer.validated_data['postcode'],
            country=serializer.validated_data.get('country', 'United Kingdom'),
            notes=serializer.validated_data.get('notes'),
        )
        
        # Create order items
        for item_data in order_items:
            OrderItem.objects.create(
                order=order,
                service=item_data['service'],
                staff=item_data['staff'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price'],
                status='pending',
            )
        
        # Calculate cancellation deadline
        if scheduled_date and scheduled_time:
            scheduled_datetime = timezone.make_aware(
                datetime.combine(scheduled_date, scheduled_time)
            )
            can_cancel_val, can_reschedule_val, deadline = can_cancel_or_reschedule(
                scheduled_datetime,
                order.cancellation_policy_hours
            )
            order.can_cancel = can_cancel_val
            order.can_reschedule = can_reschedule_val
            order.cancellation_deadline = deadline
            order.save()
        
        # Order remains 'pending' - admin/manager will confirm it later
        # When order status changes to 'confirmed', the signal handler will:
        # - Create appointments for order items
        # - Send confirmation email
        
        # Track coupon usage if coupon was applied
        if coupon and discount_amount > 0:
            from apps.coupons.models import CouponUsage
            CouponUsage.objects.create(
                coupon=coupon,
                customer=customer,
                guest_email=serializer.validated_data.get('guest_email') if not customer else None,
                order=order,
                discount_amount=discount_amount,
                order_amount=total_price + discount_amount,  # Original amount before discount
                final_amount=total_price,
            )
            # Update coupon used count
            coupon.used_count += 1
            coupon.save(update_fields=['used_count'])
        
        # Serialize response
        order_serializer = OrderSerializer(order)
        
        return Response({
            'success': True,
            'data': order_serializer.data,
            'meta': {
                'message': 'Order created successfully',
                'guest_checkout': order.is_guest_order,
                'order_number': order.order_number,
                'tracking_token': order.tracking_token,
            }
        }, status=status.HTTP_201_CREATED)


class ChangeRequestViewSet(viewsets.ModelViewSet):
    """
    Change request ViewSet (admin/manager only).
    For approving/rejecting order change requests.
    """
    queryset = ChangeRequest.objects.select_related('order', 'reviewed_by').all()
    serializer_class = ChangeRequestSerializer
    permission_classes = [IsAdminOrManager]
    
    def get_queryset(self):
        """Filter by order if provided."""
        queryset = super().get_queryset()
        order_id = self.request.query_params.get('order_id')
        status = self.request.query_params.get('status')
        
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Approve change request (admin/manager)."""
        change_request = self.get_object()
        
        if change_request.status != 'pending':
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': f'Change request is already {change_request.status}',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order = change_request.order
        
        # Check if order can still be rescheduled
        if not order.can_reschedule:
            return Response({
                'success': False,
                'error': {
                    'code': 'RESCHEDULE_NOT_ALLOWED',
                    'message': f'Order cannot be rescheduled within {order.cancellation_policy_hours} hours of scheduled time.',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update order
        order.scheduled_date = change_request.requested_date
        if change_request.requested_time:
            order.scheduled_time = change_request.requested_time
        
        # Recalculate cancellation deadline
        if order.scheduled_date and order.scheduled_time:
            scheduled_datetime = timezone.make_aware(
                datetime.combine(order.scheduled_date, order.scheduled_time)
            )
            can_cancel_val, can_reschedule_val, deadline = can_cancel_or_reschedule(
                scheduled_datetime,
                order.cancellation_policy_hours
            )
            order.can_cancel = can_cancel_val
            order.can_reschedule = can_reschedule_val
            order.cancellation_deadline = deadline
        
        order.save()
        
        # Update each order item's appointment to new date/time (first at new time, then + duration + padding)
        new_time = change_request.requested_time or order.scheduled_time or time_obj(9, 0)
        current_start = timezone.make_aware(
            datetime.combine(change_request.requested_date, new_time)
        )
        for item in order.items.select_related('appointment', 'service').all():
            if item.appointment and item.service:
                duration_minutes = item.service.duration
                padding = getattr(item.service, 'padding_time', None) or 0
                end_dt = current_start + timedelta(minutes=duration_minutes)
                item.appointment.start_time = current_start
                item.appointment.end_time = end_dt
                item.appointment.save()
                current_start = end_dt + timedelta(minutes=padding)

        # Update change request
        change_request.status = 'approved'
        change_request.reviewed_by = request.user
        change_request.reviewed_at = timezone.now()
        change_request.review_notes = request.data.get('review_notes', '')
        change_request.save()
        
        try:
            from apps.notifications.email_service import send_change_request_approved
            send_change_request_approved(change_request)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to send change request approved email: {e}")
        
        return Response({
            'success': True,
            'data': OrderSerializer(order).data,
            'meta': {
                'message': 'Change request approved and order updated',
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Reject change request (admin/manager)."""
        change_request = self.get_object()
        
        if change_request.status != 'pending':
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': f'Change request is already {change_request.status}',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update change request
        change_request.status = 'rejected'
        change_request.reviewed_by = request.user
        change_request.reviewed_at = timezone.now()
        change_request.review_notes = request.data.get('review_notes', '')
        change_request.save()
        
        try:
            from apps.notifications.email_service import send_change_request_rejected
            send_change_request_rejected(change_request)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to send change request rejected email: {e}")
        
        return Response({
            'success': True,
            'data': {
                'id': change_request.id,
                'status': change_request.status,
                'reviewed_by': change_request.reviewed_by.email if change_request.reviewed_by else None,
                'reviewed_at': change_request.reviewed_at,
            },
            'meta': {
                'message': 'Change request rejected',
            }
        }, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.ModelViewSet):
    """
    Order ViewSet (protected - customer/admin/manager).
    Customer: GET own orders, cancel, request change
    Admin/Manager: Full CRUD, approve change requests
    GET, PUT, PATCH, DELETE /api/cus/orders/ or /api/ad/orders/
    """
    queryset = Order.objects.select_related('customer').prefetch_related(
        'items', 'appointments'
    ).all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use simplified serializer for list views."""
        if self.action == 'list':
            return OrderSerializer
        return OrderSerializer
    
    def get_queryset(self):
        """Filter by current user's customer profile if customer, or all if admin/manager."""
        queryset = super().get_queryset()
        
        # Customer can only see their own orders
        if self.request.user.role == 'customer':
            try:
                customer = Customer.objects.get(user=self.request.user)
                queryset = queryset.filter(customer=customer)
            except Customer.DoesNotExist:
                queryset = queryset.none()
        # Staff can only see confirmed orders (they don't see pending orders)
        elif self.request.user.role == 'staff':
            queryset = queryset.filter(status__in=['confirmed', 'in_progress', 'completed'])
        # Admin/Manager can see all orders
        elif self.request.user.role in ['admin', 'manager']:
            # Filter by customer_id if provided
            customer_id = self.request.query_params.get('customer_id')
            if customer_id:
                queryset = queryset.filter(customer_id=customer_id)
        
        return queryset
    
    def get_permissions(self):
        """Override permissions for write operations."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            if self.request.user.role == 'customer':
                # Customer can only cancel their own orders
                return [IsAuthenticated()]
            return [IsAdminOrManager()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        """List orders with response shape { success, data, meta } for frontend."""
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

    def _manager_can_manage_orders(self, request):
        """Return True if admin or manager with can_manage_appointments."""
        if getattr(request.user, 'role', None) == 'admin':
            return True
        if request.user.role == 'manager':
            from apps.accounts.models import Manager
            try:
                manager = Manager.objects.get(user=request.user)
                return manager.is_active and manager.can_manage_appointments
            except Manager.DoesNotExist:
                return False
        return False

    def update(self, request, *args, **kwargs):
        """Update order (admin/manager with permissions). Date/time validated against available staff slots."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if not self._manager_can_manage_orders(request):
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'You do not have permission to edit orders.',
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate new date/time against available staff slots if date or time is being changed
        new_date = request.data.get('scheduled_date')
        new_time = request.data.get('scheduled_time')
        if (new_date is not None or new_time is not None) and instance.items.exists():
            from apps.appointments.slots_utils import get_available_slots
            from datetime import date as date_type, time as time_type
            use_date = new_date if new_date is not None else instance.scheduled_date
            if isinstance(use_date, str):
                try:
                    use_date = date_type.fromisoformat(use_date)
                except (ValueError, TypeError):
                    use_date = instance.scheduled_date
            elif not isinstance(use_date, date_type):
                use_date = instance.scheduled_date
            use_time = new_time if new_time is not None else (instance.scheduled_time or time_type(9, 0))
            if hasattr(use_time, 'strftime'):
                time_str = use_time.strftime('%H:%M') if use_time else '09:00'
            else:
                time_str = str(use_time)[:5] if use_time else '09:00'
            postcode = (getattr(instance, 'postcode', None) or request.data.get('postcode') or '').strip()
            if not postcode:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Order postcode is required to validate availability.',
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            for item in instance.items.select_related('service', 'staff').all():
                if not item.staff_id or not item.service_id:
                    continue
                slots = get_available_slots(
                    postcode, item.service_id, use_date, item.staff_id
                )
                slot_found = any(
                    s.get('available') and s.get('time') == time_str and item.staff_id in (s.get('staff_ids') or [])
                    for s in slots
                )
                if not slot_found:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'SLOT_UNAVAILABLE',
                            'message': f'Staff is not available at {time_str} on {use_date} for service "{item.service.name}". Choose a time from available slots.',
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if status is being changed - only admin/manager can change status
        if 'status' in request.data:
            new_status = request.data.get('status')
            if new_status != instance.status:
                # Admin can always change status
                if request.user.role != 'admin':
                    # Manager needs can_manage_appointments permission
                    if request.user.role == 'manager':
                        from apps.accounts.models import Manager
                        try:
                            manager = Manager.objects.get(user=request.user)
                            if not (manager.is_active and manager.can_manage_appointments):
                                return Response({
                                    'success': False,
                                    'error': {
                                        'code': 'PERMISSION_DENIED',
                                        'message': 'You do not have permission to change order status.',
                                    }
                                }, status=status.HTTP_403_FORBIDDEN)
                        except Manager.DoesNotExist:
                            return Response({
                                'success': False,
                                'error': {
                                    'code': 'PERMISSION_DENIED',
                                    'message': 'Manager profile not found.',
                                }
                            }, status=status.HTTP_403_FORBIDDEN)
                    else:
                        return Response({
                            'success': False,
                            'error': {
                                'code': 'PERMISSION_DENIED',
                                'message': 'Only admin or manager can change order status.',
                            }
                        }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {'message': 'Order updated successfully'}
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Delete order (admin/manager with can_manage_appointments)."""
        if not self._manager_can_manage_orders(request):
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'You do not have permission to delete orders.',
                }
            }, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'success': True, 'data': {}, 'meta': {'message': 'Order deleted successfully'}},
            status=status.HTTP_204_NO_CONTENT
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Return order detail in shape { success, data } for frontend."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='send-reminder')
    def send_reminder(self, request, pk=None):
        """Send reminder email for order (admin/manager)."""
        order = self.get_object()
        
        try:
            from apps.notifications.email_service import send_booking_confirmation
            # Reuse confirmation email template for reminders
            send_booking_confirmation(order)
            return Response({
                'success': True,
                'data': self.get_serializer(order).data,
                'meta': {
                    'message': 'Reminder email sent successfully'
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending reminder email for order {order.order_number}: {e}")
            return Response({
                'success': False,
                'error': {
                    'code': 'EMAIL_ERROR',
                    'message': f'Failed to send reminder email: {str(e)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Cancel order (customer/admin/manager)."""
        order = self.get_object()
        
        # Check permissions
        if request.user.role == 'customer':
            try:
                customer = Customer.objects.get(user=request.user)
                if order.customer != customer:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'PERMISSION_DENIED',
                            'message': 'You can only cancel your own orders',
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
        
        # Check if order can be cancelled
        if not order.can_cancel:
            return Response({
                'success': False,
                'error': {
                    'code': 'CANCELLATION_NOT_ALLOWED',
                    'message': f'Orders cannot be cancelled within {order.cancellation_policy_hours} hours of the scheduled time.',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cancel order
        order.status = 'cancelled'
        order.save()
        
        try:
            from apps.notifications.email_service import send_booking_cancellation
            send_booking_cancellation(order)
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.warning(f"Could not send cancellation email for order {order.order_number}: {e}")
        
        serializer = self.get_serializer(order)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'message': 'Order cancelled successfully',
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='request-change')
    def request_change(self, request, pk=None):
        """Request order change (customer)."""
        order = self.get_object()
        
        # Check permissions
        if request.user.role == 'customer':
            try:
                customer = Customer.objects.get(user=request.user)
                if order.customer != customer:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'PERMISSION_DENIED',
                            'message': 'You can only request changes to your own orders',
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
        
        # Validate request data
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
        
        # Check if order can be rescheduled
        if not order.can_reschedule:
            return Response({
                'success': False,
                'error': {
                    'code': 'RESCHEDULE_NOT_ALLOWED',
                    'message': f'Orders cannot be rescheduled within {order.cancellation_policy_hours} hours of the scheduled time.',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if order status allows changes
        if order.status in ['completed', 'cancelled']:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': f'Cannot request changes for orders with status: {order.status}',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create change request
        change_request = ChangeRequest.objects.create(
            order=order,
            requested_date=new_date,
            requested_time=new_time,
            reason=reason,
            status='pending'
        )
        
        try:
            from apps.notifications.email_service import send_change_request_submitted
            send_change_request_submitted(change_request)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to send change request submitted email: {e}")
        
        return Response({
            'success': True,
            'data': OrderSerializer(order).data,
            'meta': {
                'message': 'Change request submitted. A manager will review your request and contact you.',
            }
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def guest_order_view(request, order_number):
    """
    Get guest order by order number (public).
    GET /api/bkg/guest/order/{order_number}/
    """
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Order not found',
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = OrderSerializer(order)
    return Response({
        'success': True,
        'data': serializer.data,
        'meta': {}
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def guest_order_by_token_view(request, tracking_token):
    """
    Get guest order by tracking token (public).
    GET /api/bkg/guest/order/token/{tracking_token}/
    """
    try:
        order = Order.objects.get(tracking_token=tracking_token)
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Order not found',
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = OrderSerializer(order)
    return Response({
        'success': True,
        'data': serializer.data,
        'meta': {}
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def guest_check_email_view(request):
    """
    Check if email exists for account linking (public).
    POST /api/bkg/guest/check-email/
    Body: { 'email': 'user@example.com' }
    """
    email = request.data.get('email')
    if not email:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Email is required',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Normalize email
    email = email.lower().strip()
    
    # Check if user exists
    email_exists = User.objects.filter(email__iexact=email).exists()
    
    # Check if customer exists (with or without user account)
    customer_exists = Customer.objects.filter(email__iexact=email).exists()
    
    return Response({
        'success': True,
        'data': {
            'email': email,
            'email_exists': email_exists,
            'customer_exists': customer_exists,
            'has_account': email_exists,  # User account exists
            'suggestion': 'Login to link your order to your account' if email_exists else 'Register to create an account and link your order'
        },
        'meta': {}
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def guest_order_cancel_view(request, order_number):
    """
    Cancel guest order by order number (public).
    POST /api/bkg/guest/order/{order_number}/cancel/
    """
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Order not found',
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if order can be cancelled
    if not order.can_cancel:
        return Response({
            'success': False,
            'error': {
                'code': 'CANCELLATION_NOT_ALLOWED',
                'message': f'Orders cannot be cancelled within {order.cancellation_policy_hours} hours of the scheduled time.',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if order status allows cancellation
    if order.status in ['completed', 'cancelled']:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_STATUS',
                'message': f'Cannot cancel order with status: {order.status}',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Cancel order
    order.status = 'cancelled'
    order.save()
    
    try:
        from apps.notifications.email_service import send_booking_cancellation
        send_booking_cancellation(order)
    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.warning(f"Could not send cancellation email for order {order.order_number}: {e}")
    
    return Response({
        'success': True,
        'data': OrderSerializer(order).data,
        'meta': {
            'message': 'Order cancelled successfully',
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def guest_order_request_change_view(request, order_number):
    """
    Request order change by order number (public).
    POST /api/bkg/guest/order/{order_number}/request-change/
    Body: { 'scheduled_date': '2024-01-20', 'scheduled_time': '10:00:00', 'reason': 'Need to reschedule' }
    """
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Order not found',
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Validate request data
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
    
    # Check if order can be rescheduled
    if not order.can_reschedule:
        return Response({
            'success': False,
            'error': {
                'code': 'RESCHEDULE_NOT_ALLOWED',
                'message': f'Orders cannot be rescheduled within {order.cancellation_policy_hours} hours of the scheduled time.',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if order status allows changes
    if order.status in ['completed', 'cancelled']:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_STATUS',
                'message': f'Cannot request changes for orders with status: {order.status}',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create change request
    change_request = ChangeRequest.objects.create(
        order=order,
        requested_date=new_date,
        requested_time=new_time,
        reason=reason,
        status='pending'
    )
    
    # TODO: Send notification to manager/admin
    
    return Response({
        'success': True,
        'data': OrderSerializer(order).data,
        'meta': {
            'message': 'Change request submitted. A manager will review your request and contact you.',
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def guest_order_link_login_view(request, order_number):
    """
    Link guest order to existing account via login (public).
    POST /api/bkg/guest/order/{order_number}/link-login/
    Body: { 'email': 'user@example.com', 'password': 'password' }
    """
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Order not found',
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if order is already linked
    if order.customer and order.customer.user:
        return Response({
            'success': False,
            'error': {
                'code': 'ALREADY_LINKED',
                'message': 'This order is already linked to an account',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Email and password are required',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Authenticate user
    from django.contrib.auth import authenticate
    user = authenticate(request, email=email.lower().strip(), password=password)
    
    if not user:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': 'Invalid email or password',
            }
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Verify email matches order email
    if order.guest_email and order.guest_email.lower() != email.lower():
        return Response({
            'success': False,
            'error': {
                'code': 'EMAIL_MISMATCH',
                'message': 'Email does not match the order email',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get or create customer for this user
    customer, created = Customer.objects.get_or_create(
        user=user,
        defaults={
            'email': user.email,
            'name': f'{user.first_name} {user.last_name}'.strip() or user.email,
        }
    )
    
    # Link order to customer
    order.customer = customer
    order.account_linked_at = timezone.now()
    order.is_guest_order = False
    order.save()
    
    serializer = OrderSerializer(order)
    return Response({
        'success': True,
        'data': serializer.data,
        'meta': {
            'message': 'Order successfully linked to your account',
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role,
            }
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def guest_order_link_register_view(request, order_number):
    """
    Link guest order to new account via registration (public).
    POST /api/bkg/guest/order/{order_number}/link-register/
    Body: { 'email': 'user@example.com', 'password': 'password', 'password_confirm': 'password' }
    """
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Order not found',
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if order is already linked
    if order.customer and order.customer.user:
        return Response({
            'success': False,
            'error': {
                'code': 'ALREADY_LINKED',
                'message': 'This order is already linked to an account',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = request.data.get('email')
    password = request.data.get('password')
    password_confirm = request.data.get('password_confirm')
    
    if not email or not password or not password_confirm:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Email, password, and password confirmation are required',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify email matches order email
    if order.guest_email and order.guest_email.lower() != email.lower():
        return Response({
            'success': False,
            'error': {
                'code': 'EMAIL_MISMATCH',
                'message': 'Email does not match the order email',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if email already exists
    if User.objects.filter(email__iexact=email).exists():
        return Response({
            'success': False,
            'error': {
                'code': 'EMAIL_EXISTS',
                'message': 'An account with this email already exists. Please login instead.',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate password
    if password != password_confirm:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Passwords do not match',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(password) < 8:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Password must be at least 8 characters long',
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate username from email if not provided
    email_clean = email.lower().strip()
    base_username = email_clean.split('@')[0]
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    # Create user account
    user = User.objects.create_user(
        username=username,
        email=email_clean,
        password=password,
        role='customer',
        is_verified=True,  # Auto-verify for account linking
    )
    
    # Set name from order if available
    if order.guest_name:
        name_parts = order.guest_name.split(' ', 1)
        user.first_name = name_parts[0]
        if len(name_parts) > 1:
            user.last_name = name_parts[1]
        user.save()
    
    # Get or create customer for this user
    customer, created = Customer.objects.get_or_create(
        user=user,
        defaults={
            'email': user.email,
            'name': order.guest_name or f'{user.first_name} {user.last_name}'.strip() or user.email,
            'phone': order.guest_phone or '',
        }
    )
    
    # Link order to customer
    order.customer = customer
    order.account_linked_at = timezone.now()
    order.is_guest_order = False
    order.save()
    
    serializer = OrderSerializer(order)
    return Response({
        'success': True,
        'data': serializer.data,
        'meta': {
            'message': 'Account created and order successfully linked',
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role,
            },
            'tokens': {
                'access': '',  # Will be generated by login endpoint
                'refresh': '',
            }
        }
    }, status=status.HTTP_201_CREATED)
