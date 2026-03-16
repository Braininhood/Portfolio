"""
Staff app views.
Staff, StaffSchedule, StaffService, and StaffArea viewsets.
"""
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.core.permissions import IsAdmin, IsAdminOrManager, IsStaff, IsStaffOrManager
from .models import Staff, StaffSchedule, StaffService, StaffArea
from .serializers import (
    StaffSerializer, StaffListSerializer, AdminStaffListSerializer,
    StaffScheduleSerializer, StaffServiceSerializer, StaffAreaSerializer
)
from apps.services.models import Service, Category
from apps.services.serializers import ServiceListSerializer, StaffServiceCreateUpdateSerializer, CategorySerializer


class StaffPublicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public Staff ViewSet (filtered by postcode/area).
    Public: GET (list by postcode, detail)
    GET /api/stf/
    GET /api/stf/by-postcode/?postcode=SW1A1AA
    """
    queryset = Staff.objects.filter(is_active=True)
    serializer_class = StaffListSerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        """List staff members (filtered by postcode if provided)."""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Filter by postcode if provided
        postcode = request.query_params.get('postcode')
        if postcode:
            # Find staff with service areas covering this postcode
            from apps.core.postcode_utils import get_staff_for_postcode
            queryset = get_staff_for_postcode(postcode)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'count': queryset.count(),
            }
        }, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve staff member detail (public)."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {}
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='by-postcode')
    def by_postcode(self, request):
        """
        Get staff available in a postcode area (public).
        GET /api/stf/by-postcode/?postcode=SW1A1AA
        IMPORTANT: Only accepts UK postcodes - MultiBook operates only in the UK.
        """
        postcode = request.query_params.get('postcode')
        if not postcode:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Postcode parameter is required',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate UK postcode (format + country check)
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
        
        # Use validated/formatted postcode
        validated_postcode = validation_result.get('formatted', postcode)
        
        # Get staff available for this postcode using StaffArea model
        from apps.core.postcode_utils import get_staff_for_postcode
        queryset = get_staff_for_postcode(validated_postcode)
        serializer = StaffListSerializer(queryset, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'postcode': validated_postcode,
                'count': queryset.count(),
            }
        }, status=status.HTTP_200_OK)


class StaffViewSet(viewsets.ModelViewSet):
    """
    Staff ViewSet (protected - admin/manager).
    GET, POST, PUT, PATCH, DELETE /api/ad/staff/ or /api/man/staff/
    """
    queryset = Staff.objects.select_related('user').prefetch_related(
        'schedules', 
        'staff_services__service__category',
        'service_areas__service'
    ).all()
    serializer_class = StaffSerializer
    permission_classes = [IsAdminOrManager]
    
    def get_serializer_class(self):
        """Use admin list serializer (includes user id for bulk sync) for list."""
        if self.action == 'list':
            return AdminStaffListSerializer
        return StaffSerializer
    
    def list(self, request, *args, **kwargs):
        """List all staff members."""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Filter by active status if provided
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'count': queryset.count(),
            }
        }, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve staff member detail."""
        try:
            instance = self.get_object()
            # Re-fetch with proper prefetching to avoid N+1 queries
            instance = Staff.objects.select_related('user').prefetch_related(
                'schedules',
                'staff_services__service__category',
                'service_areas__service'
            ).get(pk=instance.pk)
            serializer = self.get_serializer(instance)
            return Response({
                'success': True,
                'data': serializer.data,
                'meta': {}
            }, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error retrieving staff: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({
                'success': False,
                'error': {
                    'code': 'SERVER_ERROR',
                    'message': f'Failed to retrieve staff: {str(e)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request, *args, **kwargs):
        """Create a new staff member."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {'message': 'Staff member created successfully'}
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update a staff member."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {'message': 'Staff member updated successfully'}
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='performance')
    def performance(self, request, pk=None):
        """
        Get performance metrics for a staff member.
        GET /api/ad/staff/{id}/performance/ or /api/man/staff/{id}/performance/
        """
        try:
            from django.db.models import Count, Sum, Avg, Q
            from django.utils import timezone
            from datetime import timedelta
            from apps.appointments.models import Appointment
            from apps.orders.models import Order, OrderItem
            
            staff = self.get_object()
            
            # Date range filters (default: last 30 days)
            days = int(request.query_params.get('days', 30))
            start_date = timezone.now() - timedelta(days=days)
            
            # Jobs completed
            completed_appointments = Appointment.objects.filter(
                staff=staff,
                status='completed',
                end_time__gte=start_date
            )
            jobs_completed = completed_appointments.count()
            
            # Total appointments (all statuses)
            total_appointments = Appointment.objects.filter(
                staff=staff,
                start_time__gte=start_date
            ).count()
            
            # Revenue (from completed appointments with customer bookings)
            from apps.appointments.models import CustomerAppointment
            completed_with_bookings = completed_appointments.filter(
                customer_booking__isnull=False
            )
            revenue = completed_with_bookings.aggregate(
                total=Sum('customer_booking__total_price')
            )['total'] or 0
            
            # Average response time (time from appointment creation to confirmation)
            response_times = []
            confirmed_appointments = Appointment.objects.filter(
                staff=staff,
                status__in=['confirmed', 'completed', 'in_progress'],
                start_time__gte=start_date
            ).select_related('customer_booking')
            
            for appointment in confirmed_appointments:
                try:
                    if appointment.customer_booking and hasattr(appointment, 'created_at') and appointment.created_at:
                        if hasattr(appointment.customer_booking, 'created_at') and appointment.customer_booking.created_at:
                            response_time = (appointment.customer_booking.created_at - appointment.created_at).total_seconds() / 3600  # hours
                            if response_time >= 0:
                                response_times.append(response_time)
                except Exception:
                    # Skip appointments with missing or invalid dates
                    continue
            
            avg_response_time_hours = sum(response_times) / len(response_times) if response_times else None
            
            # Completion rate
            completion_rate = (jobs_completed / total_appointments * 100) if total_appointments > 0 else 0
            
            # Upcoming appointments
            upcoming_appointments = Appointment.objects.filter(
                staff=staff,
                status__in=['pending', 'confirmed'],
                start_time__gte=timezone.now()
            ).count()
            
            # Cancelled appointments
            cancelled_appointments = Appointment.objects.filter(
                staff=staff,
                status='cancelled',
                start_time__gte=start_date
            ).count()
            
            # No-show rate
            no_shows = Appointment.objects.filter(
                staff=staff,
                status='no_show',
                start_time__gte=start_date
            ).count()
            no_show_rate = (no_shows / total_appointments * 100) if total_appointments > 0 else 0
            
            # Services breakdown
            services_breakdown = completed_with_bookings.values('service__name').annotate(
                count=Count('id'),
                revenue=Sum('customer_booking__total_price')
            ).order_by('-count')
            
            return Response({
                'success': True,
                'data': {
                    'staff_id': staff.id,
                    'staff_name': staff.name,
                    'period_days': days,
                    'period_start': start_date.isoformat(),
                    'metrics': {
                        'jobs_completed': jobs_completed,
                        'total_appointments': total_appointments,
                        'upcoming_appointments': upcoming_appointments,
                        'cancelled_appointments': cancelled_appointments,
                        'no_shows': no_shows,
                        'completion_rate': round(completion_rate, 2),
                        'no_show_rate': round(no_show_rate, 2),
                        'revenue': float(revenue),
                        'avg_response_time_hours': round(avg_response_time_hours, 2) if avg_response_time_hours else None,
                    },
                    'services_breakdown': list(services_breakdown),
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in performance endpoint: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({
                'success': False,
                'error': {
                    'code': 'SERVER_ERROR',
                    'message': f'Failed to retrieve performance metrics: {str(e)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StaffScheduleViewSet(viewsets.ModelViewSet):
    """
    Staff Schedule ViewSet (protected - staff/admin/manager).
    GET, POST, PUT, PATCH, DELETE /api/st/schedule/ or /api/ad/staff/{id}/schedules/
    """
    queryset = StaffSchedule.objects.select_related('staff').all()
    serializer_class = StaffScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by current user's staff profile if staff, or all if admin/manager."""
        queryset = super().get_queryset()
        
        # Staff can only see their own schedule
        if self.request.user.role == 'staff':
            try:
                staff = Staff.objects.get(user=self.request.user)
                queryset = queryset.filter(staff=staff)
            except Staff.DoesNotExist:
                queryset = queryset.none()
        # Admin/Manager can see all
        elif self.request.user.role in ['admin', 'manager']:
            # Filter by staff_id if provided
            staff_id = self.request.query_params.get('staff_id')
            if staff_id:
                queryset = queryset.filter(staff_id=staff_id)
        
        return queryset
    
    def get_permissions(self):
        """Override permissions for write operations."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Admin can always update schedules
            # Staff can update their own schedules
            # Managers can update schedules for staff they manage
            if self.request.user.role == 'admin':
                return [IsAdminOrManager()]
            return [IsStaffOrManager()]
        return [IsAuthenticated()]


class StaffAreaViewSet(viewsets.ModelViewSet):
    """
    Staff Service Area ViewSet (protected - admin/manager).
    GET, POST, PUT, PATCH, DELETE /api/ad/staff/{id}/areas/ or /api/man/staff/{id}/areas/
    """
    queryset = StaffArea.objects.select_related('staff').all()
    serializer_class = StaffAreaSerializer
    permission_classes = [IsAdminOrManager]
    
    def get_queryset(self):
        """Filter by staff_id if provided."""
        queryset = super().get_queryset()
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            queryset = queryset.filter(staff_id=staff_id)
        return queryset


class StaffServiceViewSet(viewsets.ModelViewSet):
    """
    Staff-Service relationship ViewSet (protected - admin/manager).
    GET, POST, PUT, PATCH, DELETE /api/ad/staff-services/ or /api/ad/staff/{id}/services/
    """
    queryset = StaffService.objects.select_related('staff', 'service').all()
    serializer_class = StaffServiceSerializer
    permission_classes = [IsAdminOrManager]
    
    def get_queryset(self):
        """Filter by staff_id or service_id if provided."""
        queryset = super().get_queryset()
        staff_id = self.request.query_params.get('staff_id')
        service_id = self.request.query_params.get('service_id')
        if staff_id:
            queryset = queryset.filter(staff_id=staff_id)
        if service_id:
            queryset = queryset.filter(service_id=service_id)
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List staff-service relationships."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'count': queryset.count(),
            }
        }, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        """Create a staff-service relationship."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {'message': 'Staff assigned to service successfully'}
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update a staff-service relationship."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {'message': 'Staff-service relationship updated successfully'}
        }, status=status.HTTP_200_OK)


def _get_staff_from_request(request):
    """Get Staff instance for current user (staff role). Returns None if not staff or no profile."""
    if getattr(request.user, 'role', None) != 'staff':
        return None
    try:
        return Staff.objects.get(user=request.user)
    except Staff.DoesNotExist:
        return None


class StaffSelfServiceViewSet(viewsets.ModelViewSet):
    """
    Staff self-service: manage services (list assigned + created; add/edit/delete with approval).
    GET, POST, PATCH, DELETE /api/st/services/
    - List: services staff is assigned to + services they created (pending or approved).
    - Create: new service (approval_status=pending_approval, created_by_staff=me); also links staff via StaffService.
    - Update: only if staff created the service and it is still pending_approval; or update their StaffService overrides.
    - Delete: only if staff created the service and it is pending_approval.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StaffServiceCreateUpdateSerializer

    def get_queryset(self):
        staff = _get_staff_from_request(self.request)
        if not staff:
            return Service.objects.none()
        return Service.objects.filter(
            Q(staff_services__staff=staff) | Q(created_by_staff=staff)
        ).select_related('category', 'created_by_staff').prefetch_related('staff_services').distinct()

    def list(self, request, *args, **kwargs):
        staff = _get_staff_from_request(request)
        if not staff:
            return Response({'success': False, 'error': {'message': 'Staff profile not found'}}, status=status.HTTP_404_NOT_FOUND)
        queryset = self.get_queryset()
        # Include approval_status, created_by_me, and staff overrides
        from apps.services.serializers import ServiceListSerializer
        items = []
        for svc in queryset:
            data = ServiceListSerializer(svc).data
            data['approval_status'] = svc.approval_status
            data['extras'] = getattr(svc, 'extras', []) or []
            data['created_by_me'] = (svc.created_by_staff_id == staff.id)
            ss = StaffService.objects.filter(staff=staff, service=svc).first()
            data['my_price_override'] = float(ss.price_override) if ss and ss.price_override is not None else None
            data['my_duration_override'] = ss.duration_override if ss else None
            items.append(data)
        return Response({'success': True, 'data': items, 'meta': {'count': len(items)}})

    def create(self, request, *args, **kwargs):
        staff = _get_staff_from_request(request)
        if not staff:
            return Response({'success': False, 'error': {'message': 'Staff profile not found'}}, status=status.HTTP_404_NOT_FOUND)
        serializer = StaffServiceCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category_id = serializer.validated_data.pop('category_id')
        category = Category.objects.get(id=category_id)
        data = {k: v for k, v in serializer.validated_data.items() if k not in ('approval_status', 'created_by_staff')}
        service = Service.objects.create(
            category=category,
            created_by_staff=staff,
            approval_status='pending_approval',
            **data
        )
        StaffService.objects.get_or_create(staff=staff, service=service, defaults={'is_active': True})
        out = ServiceListSerializer(service).data
        out['approval_status'] = service.approval_status
        out['extras'] = getattr(service, 'extras', []) or []
        out['created_by_me'] = True
        return Response({'success': True, 'data': out}, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        staff = _get_staff_from_request(request)
        data = ServiceListSerializer(instance).data
        data['approval_status'] = instance.approval_status
        data['extras'] = getattr(instance, 'extras', []) or []
        data['created_by_me'] = (instance.created_by_staff_id == staff.id) if staff else False
        ss = StaffService.objects.filter(staff=staff, service=instance).first() if staff else None
        data['my_price_override'] = float(ss.price_override) if ss and ss.price_override is not None else None
        data['my_duration_override'] = ss.duration_override if ss else None
        return Response({'success': True, 'data': data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        staff = _get_staff_from_request(request)
        if not staff:
            return Response({'success': False, 'error': {'message': 'Staff profile not found'}}, status=status.HTTP_404_NOT_FOUND)
        if instance.created_by_staff_id == staff.id and instance.approval_status == 'pending_approval':
            serializer = StaffServiceCreateUpdateSerializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            category_id = serializer.validated_data.pop('category_id', None)
            if category_id is not None:
                instance.category = Category.objects.get(id=category_id)
            for k, v in serializer.validated_data.items():
                if k not in ('approval_status', 'created_by_staff'):
                    setattr(instance, k, v)
            instance.save()
            data = ServiceListSerializer(instance).data
            data['approval_status'] = instance.approval_status
            data['extras'] = getattr(instance, 'extras', []) or []
            data['created_by_me'] = True
            return Response({'success': True, 'data': data})
        # Update StaffService overrides only
        ss = StaffService.objects.filter(staff=staff, service=instance).first()
        if not ss:
            return Response({'success': False, 'error': {'message': 'You are not assigned to this service'}}, status=status.HTTP_403_FORBIDDEN)
        price_override = request.data.get('my_price_override')
        duration_override = request.data.get('my_duration_override')
        if price_override is not None:
            from decimal import Decimal
            ss.price_override = Decimal(str(price_override))
        if duration_override is not None:
            ss.duration_override = duration_override
        ss.save()
        data = ServiceListSerializer(instance).data
        data['approval_status'] = instance.approval_status
        data['extras'] = getattr(instance, 'extras', []) or []
        data['created_by_me'] = (instance.created_by_staff_id == staff.id)
        data['my_price_override'] = float(ss.price_override) if ss.price_override is not None else None
        data['my_duration_override'] = ss.duration_override
        return Response({'success': True, 'data': data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        staff = _get_staff_from_request(request)
        if not staff:
            return Response(
                {'success': False, 'error': {'message': 'Staff profile not found'}},
                status=status.HTTP_404_NOT_FOUND
            )
        ss = StaffService.objects.filter(staff=staff, service=instance).first()
        if not ss:
            return Response(
                {'success': False, 'error': {'message': 'You are not assigned to this service'}},
                status=status.HTTP_403_FORBIDDEN
            )
        if instance.created_by_staff_id == staff.id and instance.approval_status == 'pending_approval':
            instance.delete()
        else:
            ss.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StaffSelfAreaViewSet(viewsets.ModelViewSet):
    """
    Staff self-service: manage own service areas (postcode + radius, optional per-service).
    GET, POST, PATCH, DELETE /api/st/areas/
    """
    serializer_class = StaffAreaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        staff = _get_staff_from_request(self.request)
        if not staff:
            return StaffArea.objects.none()
        return StaffArea.objects.filter(staff=staff).select_related('service')

    def list(self, request, *args, **kwargs):
        staff = _get_staff_from_request(request)
        if not staff:
            return Response({'success': False, 'error': {'message': 'Staff profile not found'}}, status=status.HTTP_404_NOT_FOUND)
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data, 'meta': {'count': queryset.count()}})

    def perform_create(self, serializer):
        staff = _get_staff_from_request(self.request)
        if not staff:
            raise PermissionError('Staff profile not found')
        serializer.save(staff=staff)

    def create(self, request, *args, **kwargs):
        staff = _get_staff_from_request(request)
        if not staff:
            return Response({'success': False, 'error': {'message': 'Staff profile not found'}}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(staff=staff)
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)


class StaffCategoriesListView(viewsets.ReadOnlyModelViewSet):
    """
    Staff: list active categories (for dropdown when creating a service).
    GET /api/st/categories/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(is_active=True).order_by('position', 'name')

    def list(self, request, *args, **kwargs):
        staff = _get_staff_from_request(request)
        if not staff:
            return Response({'success': False, 'error': {'message': 'Staff profile not found'}}, status=status.HTTP_404_NOT_FOUND)
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data, 'meta': {'count': queryset.count()}})
