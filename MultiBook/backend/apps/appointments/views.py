"""
Appointments app views.
Appointment and CustomerAppointment viewsets with guest checkout support.
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django.core.cache import cache
from datetime import datetime, timedelta
from apps.core.permissions import (
    IsCustomer, IsAdminOrManager, IsStaff, IsStaffOrManager, IsOwnerOrAdmin
)
from apps.core.utils import can_cancel_or_reschedule
from .models import Appointment, CustomerAppointment
from .serializers import (
    AppointmentSerializer, CustomerAppointmentSerializer, AppointmentCreateSerializer
)
from apps.customers.models import Customer


class AppointmentPublicViewSet(viewsets.ModelViewSet):
    """
    Public Appointment ViewSet (guest checkout supported).
    Public: POST (create appointment - NO LOGIN REQUIRED)
    GET, POST /api/bkg/
    """
    queryset = Appointment.objects.select_related('staff', 'service').all()
    serializer_class = AppointmentSerializer
    permission_classes = [AllowAny]  # Public write access for guest checkout
    
    def get_serializer_class(self):
        """Use create serializer for POST, detail serializer for GET."""
        if self.action == 'create':
            return AppointmentCreateSerializer
        return AppointmentSerializer
    
    def create(self, request, *args, **kwargs):
        """Create appointment (supports guest checkout)."""
        serializer = AppointmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract data
        service_id = serializer.validated_data['service_id']
        staff_id = serializer.validated_data.get('staff_id')
        start_time = serializer.validated_data['start_time']
        end_time = serializer.validated_data.get('end_time')
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
        
        # Import here to avoid circular imports
        from apps.services.models import Service
        from apps.staff.models import Staff
        
        try:
            service = Service.objects.get(id=service_id)
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
        
        if not staff:
            return Response({
                'success': False,
                'error': {
                    'code': 'NO_STAFF_AVAILABLE',
                    'message': 'No staff available for this service',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate end_time if not provided
        if not end_time:
            duration = service.duration
            end_time = start_time + timedelta(minutes=duration)
        
        # Create appointment
        appointment = Appointment.objects.create(
            staff=staff,
            service=service,
            start_time=start_time,
            end_time=end_time,
            status='pending',
            appointment_type='single',
        )
        
        # Create customer appointment
        if customer:
            customer_appointment = CustomerAppointment.objects.create(
                customer=customer,
                appointment=appointment,
                number_of_persons=serializer.validated_data.get('number_of_persons', 1),
                extras=serializer.validated_data.get('extras', []),
                custom_fields=serializer.validated_data.get('custom_fields', {}),
                total_price=service.price,  # TODO: Calculate total with extras
                payment_status='pending',
            )
            
            # Calculate cancellation deadline
            can_cancel_val, can_reschedule_val, deadline = can_cancel_or_reschedule(
                start_time,
                customer_appointment.cancellation_policy_hours
            )
            customer_appointment.can_cancel = can_cancel_val
            customer_appointment.can_reschedule = can_reschedule_val
            customer_appointment.cancellation_deadline = deadline
            customer_appointment.save()
        
        # Serialize response
        appointment_serializer = AppointmentSerializer(appointment)
        
        return Response({
            'success': True,
            'data': appointment_serializer.data,
            'meta': {
                'message': 'Appointment created successfully',
                'guest_checkout': customer is None or customer.user is None,
            }
        }, status=status.HTTP_201_CREATED)


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    Appointment ViewSet (protected - customer/staff/manager/admin).
    Customer: GET own appointments
    Staff: GET assigned appointments (confirmed+ only)
    Manager/Admin: GET all, PATCH/PUT to update (e.g. status).
    GET /api/cus/appointments/ or /api/st/jobs/ or /api/ad/appointments/
    PATCH /api/ad/appointments/{id}/ for admin/manager to change status.
    """
    queryset = Appointment.objects.select_related('staff', 'service', 'subscription', 'order').prefetch_related(
        'customer_booking'
    ).all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']
    
    def get_queryset(self):
        """Filter by user role."""
        queryset = super().get_queryset()
        
        # Customer can only see their own appointments (via CustomerAppointment, Order, or Subscription)
        if self.request.user.role == 'customer':
            try:
                customer = Customer.objects.get(user=self.request.user)
                # Include: linked by CustomerAppointment, or by Order, or by Subscription
                queryset = queryset.filter(
                    Q(customer_booking__customer=customer)
                    | Q(order__customer=customer)
                    | Q(subscription__customer=customer)
                ).distinct()
            except Customer.DoesNotExist:
                queryset = queryset.none()
        
        # Staff can see their assigned appointments (only confirmed and beyond)
        elif self.request.user.role == 'staff':
            from apps.staff.models import Staff
            try:
                staff = Staff.objects.get(user=self.request.user)
                # Staff can only see confirmed, in_progress, completed appointments
                queryset = queryset.filter(
                    staff=staff,
                    status__in=['confirmed', 'in_progress', 'completed']
                )
            except Staff.DoesNotExist:
                queryset = queryset.none()
        
        # Manager can see appointments within their scope
        elif self.request.user.role == 'manager':
            # TODO: Implement manager scope filtering
            # For now, return all appointments
            pass
        
        # Admin can see all appointments
        
        # Filter by staff_id if provided (for admin viewing staff appointments)
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            try:
                queryset = queryset.filter(staff_id=int(staff_id))
            except (ValueError, TypeError):
                pass
        
        # Apply filters (status can be comma-separated: pending,confirmed)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            statuses = [s.strip() for s in status_filter.split(',') if s.strip()]
            if statuses:
                queryset = queryset.filter(status__in=statuses)
        
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(start_time__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(start_time__lte=date_to)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List appointments with consistent response format."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'count': queryset.count(),
            }
        }, status=status.HTTP_200_OK)

    def _manager_can_manage_appointments(self, request):
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
        """Update appointment (admin/manager with permissions). Date/time validated against staff availability."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if not self._manager_can_manage_appointments(request):
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'You do not have permission to edit appointments.',
                }
            }, status=status.HTTP_403_FORBIDDEN)

        # Validate new start_time/end_time/staff against staff availability
        new_start = request.data.get('start_time')
        new_end = request.data.get('end_time')
        new_staff_id = request.data.get('staff_id')
        if new_start is not None or new_end is not None or new_staff_id is not None:
            from apps.appointments.slots_utils import is_staff_available_for_slot
            from django.utils.dateparse import parse_datetime
            start_dt = None
            end_dt = None
            staff_id = new_staff_id if new_staff_id is not None else (instance.staff_id if instance.staff_id else None)
            if new_start is not None:
                start_dt = parse_datetime(new_start) if isinstance(new_start, str) else new_start
            else:
                start_dt = instance.start_time
            if new_end is not None:
                end_dt = parse_datetime(new_end) if isinstance(new_end, str) else new_end
            else:
                end_dt = instance.end_time
            if start_dt and end_dt and staff_id:
                available, reason = is_staff_available_for_slot(
                    staff_id, start_dt, end_dt, exclude_appointment_id=instance.pk
                )
                if not available:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'SLOT_UNAVAILABLE',
                            'message': reason or 'Staff is not available at this time.',
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
                                        'message': 'You do not have permission to change appointment status.',
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
                                'message': 'Only admin or manager can change appointment status.',
                            }
                        }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {'message': 'Appointment updated successfully'}
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Delete appointment (admin/manager with can_manage_appointments)."""
        if not self._manager_can_manage_appointments(request):
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'You do not have permission to delete appointments.',
                }
            }, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'success': True, 'data': {}, 'meta': {'message': 'Appointment deleted successfully'}},
            status=status.HTTP_204_NO_CONTENT
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Return appointment detail wrapped as { success, data } for staff/customer consistency."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
        })
    
    def get_permissions(self):
        """Override permissions for write operations."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrManager()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'], url_path='checkin', permission_classes=[IsAuthenticated])
    def checkin(self, request, pk=None):
        """
        Check in to appointment (staff only).
        POST /api/st/jobs/{id}/checkin/
        """
        appointment = self.get_object()
        
        # Verify staff owns this appointment
        if request.user.role == 'staff':
            from apps.staff.models import Staff
            try:
                staff = Staff.objects.get(user=request.user)
                if appointment.staff != staff:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'PERMISSION_DENIED',
                            'message': 'You can only check in to your own appointments',
                        }
                    }, status=status.HTTP_403_FORBIDDEN)
            except Staff.DoesNotExist:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'STAFF_NOT_FOUND',
                        'message': 'Staff profile not found',
                    }
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'Only staff members can check in',
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Update status to in_progress
        if appointment.status not in ['pending', 'confirmed']:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': f'Cannot check in. Current status: {appointment.status}',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        appointment.status = 'in_progress'
        appointment.save(update_fields=['status'])
        
        serializer = self.get_serializer(appointment)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'message': 'Checked in successfully',
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='complete', permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        """
        Complete appointment (staff only).
        POST /api/st/jobs/{id}/complete/
        Body: { "notes": "...", "photos": [...] } (optional)
        """
        appointment = self.get_object()
        
        # Verify staff owns this appointment
        if request.user.role == 'staff':
            from apps.staff.models import Staff
            try:
                staff = Staff.objects.get(user=request.user)
                if appointment.staff != staff:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'PERMISSION_DENIED',
                            'message': 'You can only complete your own appointments',
                        }
                    }, status=status.HTTP_403_FORBIDDEN)
            except Staff.DoesNotExist:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'STAFF_NOT_FOUND',
                        'message': 'Staff profile not found',
                    }
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'Only staff members can complete jobs',
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Update status to completed
        if appointment.status not in ['in_progress', 'confirmed', 'pending']:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': f'Cannot complete. Current status: {appointment.status}',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update status to completed and notes if provided
        notes = request.data.get('notes')
        appointment.status = 'completed'
        if notes:
            appointment.internal_notes = notes
            appointment.save(update_fields=['status', 'internal_notes'])
        else:
            appointment.save(update_fields=['status'])

        # Send "cleaning complete" email to customer
        try:
            from apps.notifications.email_service import send_cleaning_complete
            send_cleaning_complete(appointment)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning('Failed to send cleaning complete email: %s', e)

        serializer = self.get_serializer(appointment)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'message': 'Job completed successfully',
            }
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='upload-photo', permission_classes=[IsAuthenticated])
    def upload_photo(self, request, pk=None):
        """
        Upload job completion photo(s) to Supabase Storage.
        POST /api/st/jobs/{id}/upload-photo/
        Body: multipart/form-data with one or more "file" fields (images).
        Requires Supabase bucket "job-photos" to exist (create in Supabase Dashboard > Storage if needed).
        """
        appointment = self.get_object()
        if request.user.role != 'staff':
            return Response({
                'success': False,
                'error': {'code': 'PERMISSION_DENIED', 'message': 'Only staff can upload job photos.'},
            }, status=status.HTTP_403_FORBIDDEN)
        from apps.staff.models import Staff
        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            return Response({
                'success': False,
                'error': {'code': 'STAFF_NOT_FOUND', 'message': 'Staff profile not found.'},
            }, status=status.HTTP_404_NOT_FOUND)
        if appointment.staff_id != staff.id:
            return Response({
                'success': False,
                'error': {'code': 'PERMISSION_DENIED', 'message': 'You can only upload photos for your own jobs.'},
            }, status=status.HTTP_403_FORBIDDEN)

        files = request.FILES.getlist('file') or ([request.FILES.get('file')] if request.FILES.get('file') else [])
        if not files:
            return Response({
                'success': False,
                'error': {'code': 'NO_FILE', 'message': 'No file(s) provided. Use multipart/form-data with "file" field(s).'},
            }, status=status.HTTP_400_BAD_REQUEST)

        from apps.core.supabase_storage import supabase_storage
        bucket = 'job-photos'
        folder = f'appointment_{appointment.id}'
        added = []
        for f in files:
            if not f or not getattr(f, 'name', None):
                continue
            if not (getattr(f, 'content_type', '') or '').startswith('image/'):
                continue
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{f.name}"
            file_path = f"{folder}/{filename}" if folder else filename
            file_data = f.read()
            result = supabase_storage.upload_file(
                bucket=bucket,
                file_path=file_path,
                file_data=file_data,
                content_type=f.content_type or 'image/jpeg',
                upsert=True,
            )
            if result.get('success') and result.get('url'):
                entry = {
                    'url': result['url'],
                    'path': result.get('path', file_path),
                    'uploaded_at': timezone.now().isoformat(),
                }
                added.append(entry)
                appointment.completion_photos = list(appointment.completion_photos or []) + [entry]
        if added:
            appointment.save(update_fields=['completion_photos'])

        serializer = self.get_serializer(appointment)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'message': f'Uploaded {len(added)} photo(s).',
                'added': len(added),
            },
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        Cancel appointment (customer can cancel if allowed by 24h policy).
        POST /api/cus/appointments/{id}/cancel/
        """
        appointment = self.get_object()
        
        # Check if customer owns this appointment
        if request.user.role == 'customer':
            try:
                customer = Customer.objects.get(user=request.user)
                customer_appointment = CustomerAppointment.objects.get(
                    customer=customer,
                    appointment=appointment
                )
                
                if not customer_appointment.can_cancel:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'CANCELLATION_NOT_ALLOWED',
                            'message': f'Cancellation deadline has passed. Deadline was {customer_appointment.cancellation_deadline}',
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except CustomerAppointment.DoesNotExist:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Appointment not found or you do not have permission',
                    }
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Cancel appointment
        appointment.status = 'cancelled'
        appointment.save()
        
        return Response({
            'success': True,
            'data': AppointmentSerializer(appointment).data,
            'meta': {
                'message': 'Appointment cancelled successfully',
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='available-slots')
    def available_slots(self, request, pk=None):
        """
        Get available time slots for rescheduling this appointment (same shape as /api/slots/).
        GET /api/cus/appointments/{id}/available-slots/?date=2024-01-15
        Uses appointment's service, optional staff, and postcode from order/subscription/customer.
        """
        appointment = self.get_object()
        date_param = request.query_params.get('date')
        if not date_param:
            return Response({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': 'date parameter is required (YYYY-MM-DD)'},
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'success': False,
                'error': {'code': 'INVALID_DATE', 'message': 'Invalid date format. Use YYYY-MM-DD.'},
            }, status=status.HTTP_400_BAD_REQUEST)
        today = timezone.now().date()
        if target_date < today:
            return Response({
                'success': False,
                'error': {'code': 'INVALID_DATE', 'message': 'Cannot reschedule to a past date.'},
            }, status=status.HTTP_400_BAD_REQUEST)
        postcode = None
        if appointment.order_id:
            order = appointment.order
            postcode = (getattr(order, 'postcode', None) or '') or (order.customer and order.customer.postcode) or ''
        elif appointment.subscription_id:
            sub = appointment.subscription
            postcode = (getattr(sub, 'postcode', None) or '') or (sub.customer and sub.customer.postcode) or ''
        if not postcode:
            ca = getattr(appointment, 'customer_booking', None)
            if ca and ca.customer_id:
                postcode = ca.customer.postcode or ''
        if not postcode or not postcode.strip():
            return Response({
                'success': False,
                'error': {
                    'code': 'NO_POSTCODE',
                    'message': 'No postcode on file for this booking. Please contact support to reschedule.',
                },
            }, status=status.HTTP_400_BAD_REQUEST)
        from apps.core.address import validate_postcode_with_google
        validation_result = validate_postcode_with_google(postcode.strip())
        if not validation_result.get('valid') or not validation_result.get('is_uk'):
            return Response({
                'success': False,
                'error': {'code': 'INVALID_POSTCODE', 'message': validation_result.get('error', 'Invalid UK postcode.')},
            }, status=status.HTTP_400_BAD_REQUEST)
        validated_postcode = validation_result.get('formatted', postcode.strip())
        try:
            from .slots_utils import get_available_slots
            staff_id = appointment.staff_id if appointment.staff_id else None
            slots = get_available_slots(
                postcode=validated_postcode,
                service_id=appointment.service_id,
                target_date=target_date,
                staff_id=staff_id,
            )
            return Response({
                'success': True,
                'data': {
                    'date': date_param,
                    'service_id': appointment.service_id,
                    'staff_id': staff_id,
                    'slots': slots,
                },
                'meta': {
                    'count': len(slots),
                    'available_count': sum(1 for s in slots if s.get('available')),
                },
            }, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception('available_slots for appointment %s', pk)
            return Response({
                'success': False,
                'error': {'code': 'SLOTS_ERROR', 'message': str(e)},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='reschedule')
    def reschedule(self, request, pk=None):
        """
        Reschedule appointment (customer can reschedule if allowed by 24h policy).
        POST /api/cus/appointments/{id}/reschedule/
        Body: {"start_time": "2024-01-15T10:00:00Z", "end_time": "2024-01-15T11:00:00Z"}
        """
        appointment = self.get_object()
        new_start_time = request.data.get('start_time')
        new_end_time = request.data.get('end_time')
        
        if not new_start_time:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'start_time is required',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if customer owns this appointment and can reschedule
        if request.user.role == 'customer':
            try:
                customer = Customer.objects.get(user=request.user)
                customer_appointment = CustomerAppointment.objects.get(
                    customer=customer,
                    appointment=appointment
                )
                
                if not customer_appointment.can_reschedule:
                    return Response({
                        'success': False,
                        'error': {
                            'code': 'RESCHEDULE_NOT_ALLOWED',
                            'message': f'Rescheduling deadline has passed. Deadline was {customer_appointment.cancellation_deadline}',
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except CustomerAppointment.DoesNotExist:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Appointment not found or you do not have permission',
                    }
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Reschedule appointment
        from django.utils.dateparse import parse_datetime
        appointment.start_time = parse_datetime(new_start_time)
        if new_end_time:
            appointment.end_time = parse_datetime(new_end_time)
        else:
            # Recalculate end_time based on service duration
            appointment.end_time = appointment.start_time + timedelta(minutes=appointment.service.duration)
        appointment.save()
        
        return Response({
            'success': True,
            'data': AppointmentSerializer(appointment).data,
            'meta': {
                'message': 'Appointment rescheduled successfully',
            }
        }, status=status.HTTP_200_OK)


# Slots response cached 2 min so new bookings appear quickly while reducing DB load
CACHE_TTL_SLOTS = 120


@api_view(['GET'])
@permission_classes([AllowAny])
def available_slots_view(request):
    """
    Get available time slots by postcode/service/staff (public). Cached 2 min per (postcode, service, date, staff).
    GET /api/slots/?postcode=SW1A1AA&service_id=1&date=2024-01-15&staff_id=1
    """
    postcode = request.query_params.get('postcode')
    service_id = request.query_params.get('service_id')
    date = request.query_params.get('date')
    staff_id = request.query_params.get('staff_id')

    if not postcode or not service_id or not date:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'postcode, service_id, and date parameters are required',
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    from apps.core.address import validate_postcode_with_google
    validation_result = validate_postcode_with_google(postcode)
    if not validation_result.get('valid') or not validation_result.get('is_uk'):
        error_msg = validation_result.get('error', 'Invalid UK postcode. MultiBook currently operates only in the UK.')
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_POSTCODE',
                'message': error_msg,
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    validated_postcode = validation_result.get('formatted', postcode)
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_DATE',
                'message': 'Invalid date format. Use YYYY-MM-DD format.',
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    today = timezone.now().date()
    if target_date < today:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_DATE',
                'message': 'Cannot book appointments in the past.',
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    parsed_staff_id = None
    if staff_id:
        try:
            parsed_staff_id = int(staff_id)
        except ValueError:
            pass

    norm_postcode = (validated_postcode or '').upper().replace(' ', '').strip()
    cache_key = f'slots_{norm_postcode}_{service_id}_{date}_{parsed_staff_id or "any"}'
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached, status=status.HTTP_200_OK)

    try:
        from .slots_utils import get_available_slots
        slots = get_available_slots(
            postcode=validated_postcode,
            service_id=int(service_id),
            target_date=target_date,
            staff_id=parsed_staff_id
        )
        payload = {
            'success': True,
            'data': {
                'postcode': validated_postcode,
                'service_id': int(service_id),
                'date': date,
                'staff_id': parsed_staff_id,
                'slots': slots,
            },
            'meta': {
                'count': len(slots),
                'available_count': sum(1 for slot in slots if slot['available']),
            }
        }
        cache.set(cache_key, payload, CACHE_TTL_SLOTS)
        return Response(payload, status=status.HTTP_200_OK)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating available slots: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'SLOTS_CALCULATION_ERROR',
                'message': f'Error calculating available slots: {str(e)}',
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
