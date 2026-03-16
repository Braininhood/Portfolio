"""
Accounts app serializers.
User, Profile, Manager, and Invitation serializers.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from .models import User, Profile, Manager, Invitation


class UserSerializer(serializers.ModelSerializer):
    """
    User serializer for basic user information.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'first_name', 'last_name', 
                  'is_active', 'is_verified', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    User creation serializer (for registration).
    - Customers can register without invitation
    - Staff/Managers/Admins require invitation token
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=False, allow_blank=True)
    name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    invitation_token = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'role', 
                  'first_name', 'last_name', 'name', 'phone', 'invitation_token']
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'required': False, 'allow_blank': True},
            'role': {'default': 'customer'},
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
        }
    
    def validate(self, attrs):
        # Normalize email to lowercase
        if 'email' in attrs and attrs['email']:
            attrs['email'] = attrs['email'].lower().strip()
        
        # Check for duplicate email (case-insensitive)
        if 'email' in attrs:
            email = attrs['email']
            existing_user = User.objects.filter(email__iexact=email).first()
            if existing_user and (not self.instance or existing_user.id != self.instance.id):
                raise serializers.ValidationError({
                    "email": "A user with this email address already exists."
                })
        
        # Validate password confirmation if provided
        password_confirm = attrs.get('password_confirm')
        if password_confirm and attrs['password'] != password_confirm:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Validate role
        role = attrs.get('role', 'customer')
        valid_roles = ['admin', 'manager', 'staff', 'customer']
        if role not in valid_roles:
            raise serializers.ValidationError({
                "role": f"Invalid role. Must be one of: {', '.join(valid_roles)}."
            })
        
        # For non-customer roles, invitation token is required
        if role != 'customer':
            invitation_token = attrs.get('invitation_token')
            if not invitation_token:
                raise serializers.ValidationError({
                    "invitation_token": f"Invitation token is required for {role} registration."
                })
            
            # Validate invitation token
            try:
                invitation = Invitation.objects.get(token=invitation_token, is_active=True)
                if invitation.is_expired():
                    raise serializers.ValidationError({
                        "invitation_token": "This invitation has expired."
                    })
                if invitation.used_at:
                    raise serializers.ValidationError({
                        "invitation_token": "This invitation has already been used."
                    })
                if invitation.role != role:
                    raise serializers.ValidationError({
                        "invitation_token": f"This invitation is for {invitation.role}, not {role}."
                    })
                # Case-insensitive email comparison
                if invitation.email.lower() != attrs.get('email', '').lower():
                    raise serializers.ValidationError({
                        "invitation_token": f"This invitation is for {invitation.email}, not {attrs.get('email')}."
                    })
                
                # Store invitation in context for later use
                attrs['_invitation'] = invitation
            except Invitation.DoesNotExist:
                raise serializers.ValidationError({
                    "invitation_token": "Invalid or expired invitation token."
                })
        
        return attrs
    
    def create(self, validated_data):
        # Remove password_confirm, name, phone, and invitation_token (we'll handle them separately)
        validated_data.pop('password_confirm', None)
        invitation_token = validated_data.pop('invitation_token', None)
        invitation = validated_data.pop('_invitation', None)
        name = validated_data.pop('name', '')
        phone = validated_data.pop('phone', None)
        password = validated_data.pop('password')
        
        # Split name into first_name and last_name if provided
        if name:
            name_parts = name.strip().split(' ', 1)
            if len(name_parts) == 1:
                validated_data['first_name'] = name_parts[0]
                validated_data['last_name'] = ''
            else:
                validated_data['first_name'] = name_parts[0]
                validated_data['last_name'] = name_parts[1]
        
        # Generate username from email if not provided
        if not validated_data.get('username'):
            email = validated_data.get('email', '')
            if email:
                # Use email prefix as username, ensure uniqueness
                base_username = email.split('@')[0]
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                validated_data['username'] = username
            else:
                # Fallback: use timestamp
                validated_data['username'] = f"user_{int(timezone.now().timestamp())}"
        
        # Create user
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        # Mark invitation as used if it exists
        if invitation:
            invitation.used_at = timezone.now()
            invitation.save()
        
        # Create profile if phone is provided
        if phone:
            Profile.objects.get_or_create(
                user=user,
                defaults={'phone': phone}
            )
        
        return user


class InvitationSerializer(serializers.ModelSerializer):
    """
    Invitation serializer for creating and managing invitations.
    - Managers can only create invitations for staff
    - Admins can create invitations for staff, managers, and admins
    """
    invitation_link = serializers.SerializerMethodField()
    
    class Meta:
        model = Invitation
        fields = ['id', 'email', 'role', 'token', 'invited_by', 'expires_at', 
                  'used_at', 'is_active', 'invitation_link', 'created_at']
        read_only_fields = ['id', 'token', 'invited_by', 'used_at', 'created_at']
    
    def validate_role(self, value):
        """Validate role based on context (will be checked in view as well)."""
        valid_roles = ['staff', 'manager', 'admin']
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {', '.join(valid_roles)}."
            )
        return value
    
    def get_invitation_link(self, obj):
        if obj.token:
            role_prefix_map = {
                'staff': 'st',
                'manager': 'man',
                'admin': 'ad',
            }
            role_prefix = role_prefix_map.get(obj.role, 'st')
            from django.conf import settings
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return f"{frontend_url}/{role_prefix}/register?token={obj.token}&email={obj.email}"
        return None


class ProfileSerializer(serializers.ModelSerializer):
    """
    Profile serializer with calendar sync fields.
    """
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'user_id', 'phone', 'avatar', 'timezone', 'preferences',
                  'calendar_sync_enabled', 'calendar_provider', 'calendar_access_token',
                  'calendar_refresh_token', 'calendar_calendar_id', 'calendar_sync_settings',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'calendar_access_token': {'write_only': True},
            'calendar_refresh_token': {'write_only': True},
        }


class ManagerSerializer(serializers.ModelSerializer):
    """
    Manager serializer with permissions configuration.
    """
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    managed_staff = serializers.PrimaryKeyRelatedField(many=True, read_only=True, required=False)
    managed_customers = serializers.PrimaryKeyRelatedField(many=True, read_only=True, required=False)
    
    class Meta:
        model = Manager
        fields = ['id', 'user', 'user_id', 'permissions', 'can_manage_all',
                  'can_manage_customers', 'can_manage_staff', 'can_manage_appointments',
                  'can_view_reports', 'managed_locations', 'managed_staff', 'managed_customers',
                  'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ManagerPermissionsSerializer(serializers.Serializer):
    """
    Serializer for updating manager permissions.
    """
    can_manage_all = serializers.BooleanField(required=False)
    can_manage_customers = serializers.BooleanField(required=False)
    can_manage_staff = serializers.BooleanField(required=False)
    can_manage_appointments = serializers.BooleanField(required=False)
    can_view_reports = serializers.BooleanField(required=False)
    managed_locations = serializers.ListField(child=serializers.IntegerField(), required=False)
    permissions = serializers.DictField(required=False)
