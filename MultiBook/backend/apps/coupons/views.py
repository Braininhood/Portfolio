"""
Coupons app views.
Coupon validation and application endpoints.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from apps.core.permissions import IsAdminOrManager
from .models import Coupon, CouponUsage
from .serializers import (
    CouponSerializer, CouponListSerializer,
    CouponValidateSerializer, CouponUsageSerializer
)
from apps.customers.models import Customer
from apps.services.models import Service


class CouponViewSet(viewsets.ModelViewSet):
    """
    Coupon ViewSet.
    Public: GET (list active coupons, validate)
    Admin/Manager: Full CRUD
    GET /api/coupons/ (public - active coupons)
    GET /api/ad/coupons/ (admin - all coupons)
    POST /api/ad/coupons/ (admin - create coupon)
    """
    queryset = Coupon.objects.prefetch_related('applicable_services', 'excluded_services').all()
    serializer_class = CouponSerializer
    permission_classes = [AllowAny]  # Public read access
    
    def get_serializer_class(self):
        """Use simplified serializer for list views."""
        if self.action == 'list':
            return CouponListSerializer
        return CouponSerializer
    
    def list(self, request, *args, **kwargs):
        """Return list wrapped in { success, data } for app consistency."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {'count': queryset.count()},
        }, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        """Create coupon; return wrapped in { success, data }."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {'message': 'Coupon created successfully'},
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        """Return single coupon wrapped in { success, data }."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {},
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Update coupon; return wrapped in { success, data }."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {'message': 'Coupon updated successfully'},
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """Delete coupon; return wrapped { success }."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'data': None,
            'meta': {'message': 'Coupon deleted'},
        }, status=status.HTTP_200_OK)
    
    def get_queryset(self):
        """Filter active coupons for public, all for admin."""
        queryset = super().get_queryset()
        
        # Public users see only active coupons
        if not self.request.user.is_authenticated or self.request.user.role not in ['admin', 'manager']:
            now = timezone.now()
            queryset = queryset.filter(
                status='active',
                valid_from__lte=now
            )
            if queryset.filter(valid_until__isnull=False).exists():
                queryset = queryset.filter(
                    Q(valid_until__isnull=True) | Q(valid_until__gte=now)
                )
        
        # Apply filters
        code_filter = self.request.query_params.get('code')
        if code_filter:
            queryset = queryset.filter(code__iexact=code_filter)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def get_permissions(self):
        """Override permissions for write operations."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrManager()]
        return [AllowAny()]
    
    @action(detail=False, methods=['post'], url_path='validate', permission_classes=[AllowAny])
    def validate_coupon(self, request):
        """
        Validate and get discount amount for a coupon code.
        POST /api/coupons/validate/
        Body: {
            "code": "SAVE20",
            "order_amount": 100.00,
            "service_ids": [1, 2],
            "customer_id": 123 (optional)
        }
        """
        serializer = CouponValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        order_amount = serializer.validated_data['order_amount']
        service_ids = serializer.validated_data.get('service_ids', [])
        customer_id = serializer.validated_data.get('customer_id')
        
        # Get coupon
        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Coupon code not found',
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get customer if provided
        customer = None
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                pass
        
        # Validate coupon
        is_valid, error_message = coupon.is_valid(
            customer=customer,
            order_amount=order_amount,
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
        
        # Calculate discount
        discount_amount = coupon.calculate_discount(order_amount)
        final_amount = order_amount - discount_amount
        
        return Response({
            'success': True,
            'data': {
                'coupon': CouponSerializer(coupon).data,
                'discount_amount': str(discount_amount),
                'order_amount': str(order_amount),
                'final_amount': str(final_amount),
            },
            'meta': {
                'message': 'Coupon is valid',
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='active', permission_classes=[AllowAny])
    def active_coupons(self, request):
        """
        Get all active coupons.
        GET /api/coupons/active/
        """
        now = timezone.now()
        coupons = Coupon.objects.filter(
            status='active',
            valid_from__lte=now
        ).filter(
            Q(valid_until__isnull=True) | Q(valid_until__gte=now)
        ).prefetch_related('applicable_services', 'excluded_services')
        
        serializer = CouponListSerializer(coupons, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'count': coupons.count(),
            }
        }, status=status.HTTP_200_OK)


class CouponUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Coupon Usage ViewSet (read-only for analytics).
    Admin/Manager: View all usage
    GET /api/ad/coupons/usages/
    """
    queryset = CouponUsage.objects.select_related('coupon', 'customer', 'order', 'subscription', 'appointment').all()
    serializer_class = CouponUsageSerializer
    permission_classes = [IsAdminOrManager]
    
    def get_queryset(self):
        """Filter by coupon or customer if provided."""
        queryset = super().get_queryset()
        
        coupon_id = self.request.query_params.get('coupon_id')
        if coupon_id:
            queryset = queryset.filter(coupon_id=coupon_id)
        
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        return queryset.order_by('-created_at')
