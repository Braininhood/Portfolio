from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from .models import MasterKey, Vault, PasswordEntry
from .serializers import UserSerializer, MasterKeySerializer, VaultSerializer, PasswordEntrySerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def check_username(request):
    """
    Check if a username exists in the database
    """
    username = request.data.get('username', '')
    exists = User.objects.filter(username=username).exists()
    return Response({'exists': exists})

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user with username, email, and password
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = User.objects.create_user(
            username=request.data['username'],
            email=request.data['email'],
            password=request.data['password']
        )
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'email': user.email
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Authenticate a user and return a token
    """
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'email': user.email
        })
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_master_key(request):
    """
    Initialize a user's master key details
    """
    try:
        master_key, created = MasterKey.objects.get_or_create(user=request.user)
        
        master_key.salt = request.data.get('salt')
        master_key.verification_hash = request.data.get('verification_hash')
        master_key.save()
        
        return Response(MasterKeySerializer(master_key).data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_master_key_salt(request):
    """
    Get the salt for the master key to derive it client-side
    """
    try:
        master_key = MasterKey.objects.get(user=request.user)
        return Response({'salt': master_key.salt})
    except MasterKey.DoesNotExist:
        return Response({'error': 'Master key not set up'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_master_key(request):
    """
    Verify the master key by checking the verification hash
    """
    try:
        master_key = MasterKey.objects.get(user=request.user)
        if master_key.verification_hash == request.data.get('verification_hash'):
            return Response({'valid': True})
        return Response({'valid': False}, status=status.HTTP_401_UNAUTHORIZED)
    except MasterKey.DoesNotExist:
        return Response({'error': 'Master key not set up'}, status=status.HTTP_404_NOT_FOUND)

class VaultViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing the vault
    """
    serializer_class = VaultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Vault.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PasswordEntryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing password entries
    """
    serializer_class = PasswordEntrySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_vault = Vault.objects.get(user=self.request.user)
        return PasswordEntry.objects.filter(vault=user_vault)
    
    def perform_create(self, serializer):
        user_vault = Vault.objects.get(user=self.request.user)
        serializer.save(vault=user_vault)
