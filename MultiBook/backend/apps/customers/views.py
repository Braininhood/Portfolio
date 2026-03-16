"""
Customers app views.
Customer and Address viewsets.
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.core.permissions import IsCustomer, IsAdminOrManager, IsOwnerOrAdmin
from .models import Customer, Address
from .serializers import (
    CustomerSerializer, CustomerListSerializer, AddressSerializer,
    GuestCustomerSerializer
)


class CustomerViewSet(viewsets.ModelViewSet):
    """
    Customer ViewSet (protected - customer/admin/manager).
    Customer: GET own profile, PUT own profile
    Admin/Manager: Full CRUD
    GET, POST, PUT, PATCH, DELETE /api/cus/profile/ or /api/ad/customers/
    """
    queryset = Customer.objects.select_related('user').prefetch_related('addresses').all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use simplified serializer for list views."""
        if self.action == 'list':
            return CustomerListSerializer
        return CustomerSerializer
    
    def get_queryset(self):
        """Filter by current user if customer, or all if admin/manager."""
        queryset = super().get_queryset()
        
        # Customer can only see their own profile
        if self.request.user.role == 'customer':
            try:
                customer = Customer.objects.get(user=self.request.user)
                queryset = queryset.filter(id=customer.id)
            except Customer.DoesNotExist:
                queryset = queryset.none()
        # Admin/Manager can see all customers
        elif self.request.user.role in ['admin', 'manager']:
            # Apply filters if provided
            email = self.request.query_params.get('email')
            if email:
                queryset = queryset.filter(email__icontains=email)
            postcode = self.request.query_params.get('postcode')
            if postcode:
                queryset = queryset.filter(postcode__icontains=postcode)
        
        return queryset
    
    def get_permissions(self):
        """Override permissions for write operations."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            if self.request.user.role == 'customer':
                # Customer can only update their own profile
                return [IsAuthenticated()]
            return [IsAdminOrManager()]
        return [IsAuthenticated()]
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve customer details."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {}
        }, status=status.HTTP_200_OK)
    
    def list(self, request, *args, **kwargs):
        """List customers."""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Additional filters for admin/manager
        if request.user.role in ['admin', 'manager']:
            name = request.query_params.get('name')
            if name:
                queryset = queryset.filter(name__icontains=name)
            phone = request.query_params.get('phone')
            if phone:
                queryset = queryset.filter(phone__icontains=phone)
            tags = request.query_params.get('tags')
            if tags:
                # Filter by tags (JSON array search)
                queryset = queryset.filter(tags__contains=[tags])
            has_user_account = request.query_params.get('has_user_account')
            if has_user_account is not None:
                if has_user_account.lower() == 'true':
                    queryset = queryset.exclude(user__isnull=True)
                elif has_user_account.lower() == 'false':
                    queryset = queryset.filter(user__isnull=True)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'count': queryset.count(),
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='bookings')
    def bookings(self, request, pk=None):
        """Get customer booking history (appointments, orders, subscriptions)."""
        customer = self.get_object()
        
        from apps.appointments.models import Appointment, CustomerAppointment
        from apps.orders.models import Order
        from apps.subscriptions.models import Subscription
        
        # Get appointments (Appointment has OneToOne customer_booking -> CustomerAppointment, not customer_appointments)
        appointments = Appointment.objects.filter(
            customer_booking__customer=customer
        ).select_related('staff', 'service', 'customer_booking').order_by('-start_time')
        
        # Get orders
        orders = Order.objects.filter(customer=customer).prefetch_related('items').order_by('-created_at')
        
        # Get subscriptions
        subscriptions = Subscription.objects.filter(customer=customer).order_by('-created_at')
        
        from apps.appointments.serializers import AppointmentSerializer
        from apps.orders.serializers import OrderSerializer
        from apps.subscriptions.serializers import SubscriptionSerializer
        
        return Response({
            'success': True,
            'data': {
                'appointments': AppointmentSerializer(appointments, many=True).data,
                'orders': OrderSerializer(orders, many=True).data,
                'subscriptions': SubscriptionSerializer(subscriptions, many=True).data,
            },
            'meta': {
                'appointments_count': appointments.count(),
                'orders_count': orders.count(),
                'subscriptions_count': subscriptions.count(),
            }
        })
    
    @action(detail=True, methods=['get'], url_path='payments')
    def payments(self, request, pk=None):
        """Get customer payment history."""
        customer = self.get_object()
        
        from apps.orders.models import Order
        
        # Get orders with payment info
        orders = Order.objects.filter(customer=customer).order_by('-created_at')
        
        payments = []
        for order in orders:
            payments.append({
                'id': order.id,
                'order_number': order.order_number,
                'date': order.created_at,
                'amount': float(order.total_price),
                'status': order.payment_status,
                'order_status': order.status,
                'type': 'order',
            })
        
        # TODO: Add actual Payment model entries when payments app is implemented
        
        return Response({
            'success': True,
            'data': payments,
            'meta': {
                'total_paid': sum(float(order.total_price) for order in orders if order.payment_status == 'paid'),
                'total_pending': sum(float(order.total_price) for order in orders if order.payment_status == 'pending'),
                'count': len(payments),
            }
        })


class AddressViewSet(viewsets.ModelViewSet):
    """
    Address ViewSet (protected - customer/admin/manager).
    Customer: Own addresses CRUD
    Admin/Manager: All addresses CRUD
    GET, POST, PUT, PATCH, DELETE /api/cus/addresses/ or /api/ad/customers/{id}/addresses/
    """
    queryset = Address.objects.select_related('customer').all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by current user's customer profile if customer, or all if admin/manager."""
        queryset = super().get_queryset()
        
        # Customer can only see their own addresses
        if self.request.user.role == 'customer':
            try:
                customer = Customer.objects.get(user=self.request.user)
                queryset = queryset.filter(customer=customer)
            except Customer.DoesNotExist:
                queryset = queryset.none()
        # Admin/Manager can see all addresses
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
                # Customer can only manage their own addresses
                return [IsAuthenticated()]
            return [IsAdminOrManager()]
        return [IsAuthenticated()]
