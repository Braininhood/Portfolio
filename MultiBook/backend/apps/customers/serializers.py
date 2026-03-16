"""
Customers app serializers.
Customer and Address serializers.
"""
from rest_framework import serializers
from .models import Customer, Address
from apps.accounts.serializers import UserSerializer


class AddressSerializer(serializers.ModelSerializer):
    """
    Customer address serializer.
    """
    class Meta:
        model = Address
        fields = ['id', 'customer', 'type', 'address_line1', 'address_line2',
                  'city', 'postcode', 'country', 'is_default', 'address_validated',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomerSerializer(serializers.ModelSerializer):
    """
    Customer serializer with user and addresses.
    """
    user = UserSerializer(read_only=True, allow_null=True)
    user_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    addresses = AddressSerializer(many=True, read_only=True)
    
    class Meta:
        model = Customer
        fields = ['id', 'user', 'user_id', 'name', 'email', 'phone',
                  'address_line1', 'address_line2', 'city', 'postcode', 'country',
                  'address_validated', 'notes', 'tags', 'addresses',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomerListSerializer(serializers.ModelSerializer):
    """
    Simplified customer serializer for list views.
    """
    user_id = serializers.IntegerField(source='user.id', read_only=True, allow_null=True)
    has_user_account = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone', 'postcode', 'city', 'user_id', 'has_user_account', 'created_at']
    
    def get_has_user_account(self, obj):
        """Check if customer has a user account."""
        return obj.user is not None


class GuestCustomerSerializer(serializers.Serializer):
    """
    Serializer for guest customer information (no account required).
    Used for guest checkout in orders and subscriptions.
    """
    name = serializers.CharField(max_length=200, required=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address_line1 = serializers.CharField(max_length=255, required=True)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=True)
    postcode = serializers.CharField(max_length=20, required=True)
    country = serializers.CharField(max_length=100, default='United Kingdom', required=False)
