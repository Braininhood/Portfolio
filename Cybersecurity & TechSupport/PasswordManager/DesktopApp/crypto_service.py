#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CryptoService - Cryptography service for secure password management.
"""

import os
import json
import base64
import secrets
import hashlib
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

class CryptoService:
    """Provides cryptographic operations for secure password management"""
    
    def __init__(self):
        """Initialize the crypto service"""
        # PBKDF2 iterations - adjust for balance of security and performance
        self.iterations = 100000 
        # Salt size in bytes
        self.salt_size = 32
        # Key size in bytes
        self.key_size = 32  # 256 bits
        # Current salt for decryption
        self.current_salt = None
    
    def generate_salt(self):
        """Generate a random salt for password hashing
        
        Returns:
            bytes: Random salt
        """
        return os.urandom(self.salt_size)
    
    def hash_password(self, password, salt):
        """Hash a password using PBKDF2-HMAC-SHA256
        
        Args:
            password (str): Password to hash
            salt (bytes): Salt for password hashing
            
        Returns:
            str: Base64-encoded password hash
        """
        if not password or not salt:
            raise ValueError("Password and salt must be provided")
        
        # Convert password string to bytes
        password_bytes = password.encode('utf-8')
        
        # Use PBKDF2 with SHA-256
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_size,
            salt=salt,
            iterations=self.iterations,
        )
        
        # Derive key
        key = kdf.derive(password_bytes)
        
        # Return base64 encoded hash
        return base64.b64encode(key).decode('utf-8')
    
    def verify_password(self, password, stored_hash, salt):
        """Verify a password against a stored hash
        
        Args:
            password (str): Password to verify
            stored_hash (str): Base64-encoded stored hash
            salt (bytes): Salt used for hashing
            
        Returns:
            bool: True if password matches
        """
        if not password or not stored_hash or not salt:
            return False
        
        # Hash the provided password
        new_hash = self.hash_password(password, salt)
        
        # Compare hashes using constant-time comparison
        return secrets.compare_digest(new_hash, stored_hash)
    
    def derive_encryption_key(self, password, salt):
        """Derive an encryption key from password
        
        Args:
            password (str): Password
            salt (bytes): Salt
            
        Returns:
            bytes: Encryption key
        """
        # Convert password string to bytes
        password_bytes = password.encode('utf-8')
        
        # Use PBKDF2 with SHA-256
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_size,
            salt=salt,
            iterations=self.iterations,
        )
        
        # Derive and return key
        return kdf.derive(password_bytes)
    
    def encrypt_vault(self, vault_data, master_password):
        """Encrypt vault data with a master password
        
        Args:
            vault_data (dict): Vault data to encrypt
            master_password (str): Master password
            
        Returns:
            str: Base64-encoded encrypted data
        """
        if not vault_data or not master_password:
            raise ValueError("Vault data and master password must be provided")
        
        # Generate a random nonce
        nonce = os.urandom(12)  # 96 bits for AES-GCM
        
        # Convert vault data to JSON string then to bytes
        plain_data = json.dumps(vault_data).encode('utf-8')
        
        # Use the current salt if available, otherwise generate a new one
        if not hasattr(self, 'current_salt') or self.current_salt is None:
            self.current_salt = self.generate_salt()
        
        # Derive encryption key with the current salt
        encryption_key = self.derive_encryption_key(master_password, self.current_salt)
        
        # Create an AES-GCM cipher with the key
        aesgcm = AESGCM(encryption_key)
        
        # Encrypt the data
        encrypted_data = aesgcm.encrypt(nonce, plain_data, None)
        
        # Combine nonce and encrypted data for storage
        encrypted_data_with_nonce = nonce + encrypted_data
        
        # Return Base64 encoded encrypted data
        return base64.b64encode(encrypted_data_with_nonce).decode('utf-8')
    
    def decrypt_vault(self, encrypted_data, master_password):
        """Decrypt vault data with a master password
        
        Args:
            encrypted_data (str): Base64-encoded encrypted data
            master_password (str): Master password
            
        Returns:
            dict: Decrypted vault data
            
        Raises:
            ValueError: If decryption fails (wrong password or corrupted data)
        """
        if not encrypted_data or not master_password:
            raise ValueError("Encrypted data and master password must be provided")
        
        try:
            # Decode Base64 string to bytes
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]
            
            # Derive encryption key
            # BUG: We're generating a new salt each time, so the key will be different
            # encryption_key = self.derive_encryption_key(master_password, self.generate_salt())
            
            # Use the salt from the vault file
            if not hasattr(self, 'current_salt') or self.current_salt is None:
                raise ValueError("Salt is not available for decryption")
            
            encryption_key = self.derive_encryption_key(master_password, self.current_salt)
            
            # Create an AES-GCM cipher with the key
            aesgcm = AESGCM(encryption_key)
            
            # Decrypt the data
            decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
            
            # Parse JSON data
            return json.loads(decrypted_data.decode('utf-8'))
        except (ValueError, InvalidTag, json.JSONDecodeError) as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def generate_password(self, options):
        """Generate a random password based on options
        
        Args:
            options (dict): Password generation options
                - length (int): Password length
                - include_lowercase (bool): Include lowercase letters
                - include_uppercase (bool): Include uppercase letters
                - include_numbers (bool): Include numbers
                - include_symbols (bool): Include symbols
                - exclude_similar_chars (bool): Exclude similar chars (e.g. 1, l, I)
                - exclude_ambiguous (bool): Exclude ambiguous symbols
            
        Returns:
            str: Generated password
        """
        # Default options
        length = options.get('length', 16)
        include_lowercase = options.get('include_lowercase', True)
        include_uppercase = options.get('include_uppercase', True)
        include_numbers = options.get('include_numbers', True)
        include_symbols = options.get('include_symbols', True)
        exclude_similar = options.get('exclude_similar_chars', False)
        exclude_ambiguous = options.get('exclude_ambiguous', False)
        
        # Character sets
        lowercase_chars = "abcdefghijklmnopqrstuvwxyz"
        uppercase_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        number_chars = "0123456789"
        symbol_chars = "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?"
        similar_chars = "il1Lo0O"
        ambiguous_chars = "{}[]()/\\'\"`~,;:.<>"
        
        # Build character set based on options
        charset = ""
        
        if include_lowercase:
            charset += lowercase_chars
        if include_uppercase:
            charset += uppercase_chars
        if include_numbers:
            charset += number_chars
        if include_symbols:
            charset += symbol_chars
        
        # Remove excluded characters
        if exclude_similar:
            for char in similar_chars:
                charset = charset.replace(char, '')
        
        if exclude_ambiguous:
            for char in ambiguous_chars:
                charset = charset.replace(char, '')
        
        # Ensure we have at least one character type
        if not charset:
            charset = lowercase_chars
        
        # Generate password
        password = ''.join(secrets.choice(charset) for _ in range(length))
        
        return password
    
    def buffer_to_hex(self, buffer):
        """Convert a buffer to hex string for storage
        
        Args:
            buffer (bytes): Buffer to convert
            
        Returns:
            str: Hex string
        """
        return buffer.hex()
    
    def hex_to_buffer(self, hex_string):
        """Convert hex string back to buffer
        
        Args:
            hex_string (str): Hex string
            
        Returns:
            bytes: Buffer
        """
        return bytes.fromhex(hex_string)
    
    def analyze_password_strength(self, password):
        """Analyze password strength
        
        Args:
            password (str): Password to analyze
            
        Returns:
            dict: Analysis results
                - score (int): 0-4 score (0=very weak, 4=very strong)
                - feedback (list): List of feedback messages
                - estimated_time_to_crack (str): Estimated time to crack
                - strength (str): Text representation of strength
        """
        if not password:
            return {
                'score': 0,
                'feedback': ['No password provided'],
                'estimated_time_to_crack': 'Instant',
                'strength': 'Very Weak'
            }
        
        # Initialize score and feedback
        score = 0
        feedback = []
        
        # Check length
        if len(password) < 8:
            feedback.append('Password is too short')
        elif len(password) >= 12:
            score += 1
            if len(password) >= 16:
                score += 1
        
        # Check character diversity
        has_lowercase = any(c.islower() for c in password)
        has_uppercase = any(c.isupper() for c in password)
        has_digits = any(c.isdigit() for c in password)
        has_symbols = any(not c.isalnum() for c in password)
        
        diversity_count = sum([has_lowercase, has_uppercase, has_digits, has_symbols])
        score += min(diversity_count, 3)
        
        if not has_lowercase:
            feedback.append('Add lowercase letters')
        if not has_uppercase:
            feedback.append('Add uppercase letters')
        if not has_digits:
            feedback.append('Add numbers')
        if not has_symbols:
            feedback.append('Add symbols')
        
        # Check for common patterns
        if password.lower() in ['password', '123456', 'qwerty', 'admin']:
            score = 0
            feedback.append('Extremely common password')
        
        # Check for sequential characters
        if any(password[i] == password[i+1] == password[i+2] for i in range(len(password)-2)):
            score -= 1
            feedback.append('Avoid repeating characters')
        
        # Normalize score to 0-4 range
        score = max(0, min(4, score))
        
        # Determine strength text
        strength_texts = ['Very Weak', 'Weak', 'Moderate', 'Strong', 'Very Strong']
        strength = strength_texts[score]
        
        # Estimate time to crack (simplified)
        crack_times = [
            'Instant',
            'Minutes to Hours',
            'Days to Weeks',
            'Months to Years',
            'Centuries or more'
        ]
        estimated_time = crack_times[score]
        
        # If no feedback, provide a positive message
        if not feedback and score >= 3:
            feedback.append('Good password!')
        
        return {
            'score': score,
            'feedback': feedback,
            'estimated_time_to_crack': estimated_time,
            'strength': strength
        } 