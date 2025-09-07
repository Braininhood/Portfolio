from rest_framework import serializers
from django.contrib.auth.models import User
from .models import MasterKey, Vault, PasswordEntry

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        extra_kwargs = {'password': {'write_only': True}}

class MasterKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterKey
        fields = ['id', 'salt', 'verification_hash', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class VaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vault
        fields = ['id', 'vault_key_encrypted', 'vault_salt', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class PasswordEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordEntry
        fields = ['id', 'encrypted_data', 'iv', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at'] 