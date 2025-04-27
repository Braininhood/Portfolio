import os
import base64
import hashlib
import tempfile
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

class Crypto:
    """Handles file encryption and decryption operations"""
    
    ITERATIONS = 100000
    KEY_LENGTH = 32  # 256 bits
    SALT_LENGTH = 16
    IV_LENGTH = 16
    
    @staticmethod
    def derive_key(password, salt):
        """Derive an encryption key from a password and salt using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=Crypto.KEY_LENGTH,
            salt=salt,
            iterations=Crypto.ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(password.encode())
    
    @staticmethod
    def encrypt_file(file_path, password, output_path=None):
        """
        Encrypt a file using AES-256-CBC with a password-derived key
        Returns: (output_path, salt, iv, file_hash)
        """
        # Generate a random salt and IV
        salt = os.urandom(Crypto.SALT_LENGTH)
        iv = os.urandom(Crypto.IV_LENGTH)
        
        # Derive key from password and salt
        key = Crypto.derive_key(password, salt)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Default output path
        if output_path is None:
            output_path = file_path + ".enc"
        
        # Calculate original file hash
        file_hash = Crypto.calculate_file_hash(file_path)
        
        # Encrypt file
        with open(file_path, 'rb') as f_in:
            plaintext = f_in.read()
            
            # Apply padding to make length a multiple of 16 bytes (AES block size)
            padding_length = 16 - (len(plaintext) % 16)
            padded_plaintext = plaintext + bytes([padding_length]) * padding_length
            
            # Encrypt the padded plaintext
            ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
            
            # Write salt, iv, and ciphertext to the output file
            with open(output_path, 'wb') as f_out:
                f_out.write(salt)
                f_out.write(iv)
                f_out.write(ciphertext)
        
        return output_path, salt, iv, file_hash
    
    @staticmethod
    def decrypt_file(encrypted_file_path, password, output_path=None):
        """
        Decrypt a file using AES-256-CBC with a password-derived key
        Returns: (output_path, success)
        """
        # Default output path (remove .enc extension if present)
        if output_path is None:
            if encrypted_file_path.endswith('.enc'):
                output_path = encrypted_file_path[:-4]
            else:
                output_path = encrypted_file_path + ".dec"
        
        try:
            with open(encrypted_file_path, 'rb') as f_in:
                # Read salt and IV from the file
                salt = f_in.read(Crypto.SALT_LENGTH)
                iv = f_in.read(Crypto.IV_LENGTH)
                
                # Derive key from password and salt
                key = Crypto.derive_key(password, salt)
                
                # Create cipher
                cipher = Cipher(
                    algorithms.AES(key),
                    modes.CBC(iv),
                    backend=default_backend()
                )
                decryptor = cipher.decryptor()
                
                # Read and decrypt the ciphertext
                ciphertext = f_in.read()
                padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
                
                # Remove padding
                padding_length = padded_plaintext[-1]
                plaintext = padded_plaintext[:-padding_length]
                
                # Write plaintext to output file
                with open(output_path, 'wb') as f_out:
                    f_out.write(plaintext)
                
                return output_path, True
                
        except Exception as e:
            # If decryption fails, return failure
            return None, False
    
    @staticmethod
    def calculate_file_hash(file_path):
        """Calculate SHA-256 hash of a file"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # Read and update hash in chunks to avoid loading large files into memory
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    @staticmethod
    def verify_file_hash(file_path, expected_hash):
        """Verify file integrity by comparing hash"""
        current_hash = Crypto.calculate_file_hash(file_path)
        return current_hash == expected_hash

def encrypt_key_with_password(file_key, password, salt=None):
    """Encrypt the file encryption key with a user's password"""
    derived_key, salt = Crypto.derive_key(password, salt)
    
    # Initialize AES cipher with the derived key
    iv = os.urandom(16)  # Initialization vector
    cipher = Cipher(algorithms.AES(derived_key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # Encrypt the file key
    encrypted_key = encryptor.update(file_key) + encryptor.finalize()
    
    # Return both the encrypted key and the IV used for encryption
    return base64.b64encode(encrypted_key + iv).decode('utf-8'), base64.b64encode(salt).decode('utf-8')

def decrypt_key_with_password(encrypted_key_b64, password, salt_b64):
    """Decrypt the file encryption key with a user's password"""
    # Decode and extract encrypted key and IV
    combined = base64.b64decode(encrypted_key_b64)
    encrypted_key = combined[:-16]  # Last 16 bytes are the IV
    iv = combined[-16:]
    
    salt = base64.b64decode(salt_b64)
    
    # Derive the key from the password and salt
    derived_key, _ = Crypto.derive_key(password, salt)
    
    # Initialize AES cipher for decryption
    cipher = Cipher(algorithms.AES(derived_key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    # Decrypt and return the file key
    return decryptor.update(encrypted_key) + decryptor.finalize()

def calculate_file_hash(file_path):
    """Calculate the SHA-256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def calculate_hash_from_data(data):
    """Calculate the SHA-256 hash of data in memory"""
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()

def encrypt_file(input_file_path, output_file_path, key):
    """
    Encrypt a file using AES-256 in CFB mode
    Can work with file objects or file paths
    """
    # Generate a random IV
    iv = os.urandom(16)
    
    # Initialize AES cipher
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # Write IV to output file
    with open(output_file_path, 'wb') as out_file:
        out_file.write(iv)
        
        # Read input file in chunks and encrypt
        with open(input_file_path, 'rb') as in_file:
            while True:
                chunk = in_file.read(8192)
                if not chunk:
                    break
                encrypted_chunk = encryptor.update(chunk)
                out_file.write(encrypted_chunk)
            
            # Finalize encryption
            out_file.write(encryptor.finalize())
    
    return output_file_path

def decrypt_file(input_file_path, output_file_path, key):
    """
    Decrypt a file encrypted with AES-256 in CFB mode
    Can work with file objects or file paths
    """
    with open(input_file_path, 'rb') as in_file:
        # Read the IV from the beginning of the file
        iv = in_file.read(16)
        
        # Initialize AES cipher for decryption
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        # Create output file
        with open(output_file_path, 'wb') as out_file:
            while True:
                chunk = in_file.read(8192)
                if not chunk:
                    break
                decrypted_chunk = decryptor.update(chunk)
                out_file.write(decrypted_chunk)
            
            # Finalize decryption
            out_file.write(decryptor.finalize())
    
    return output_file_path

def create_temp_decrypted_file(encrypted_file_path, key, original_filename):
    """
    Create a temporary decrypted version of the file
    Used for downloading or viewing files
    """
    # Create a temporary file with the original extension
    suffix = os.path.splitext(original_filename)[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_path = temp_file.name
    
    # Decrypt to the temporary file
    decrypt_file(encrypted_file_path, temp_path, key)
    
    return temp_path 