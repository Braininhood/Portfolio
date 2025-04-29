from django.db import models
from django.contrib.auth.models import User

class MasterKey(models.Model):
    """
    Store the salt and verification data for the master key.
    The actual master key is never stored, only derived client-side.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='master_key')
    salt = models.CharField(max_length=64)  # Salt for key derivation
    verification_hash = models.CharField(max_length=128)  # To verify correct master key
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Vault(models.Model):
    """
    The encrypted vault that contains all password entries.
    The vault is encrypted with a key derived from the master key.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vault')
    vault_key_encrypted = models.TextField()  # Vault key encrypted with the master key
    vault_salt = models.CharField(max_length=64)  # Salt for vault key
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PasswordEntry(models.Model):
    """
    A password entry that is encrypted client-side with the vault key.
    All sensitive data is encrypted and never stored in plaintext.
    """
    vault = models.ForeignKey(Vault, on_delete=models.CASCADE, related_name='entries')
    encrypted_data = models.TextField()  # Encrypted JSON containing website, username, password, etc.
    iv = models.CharField(max_length=32)  # Initialization vector for the encryption
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
