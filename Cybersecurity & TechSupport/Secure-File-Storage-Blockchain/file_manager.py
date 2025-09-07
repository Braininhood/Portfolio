import os
import uuid
import tempfile
import json
from datetime import datetime
import base64
from crypto import Crypto
from blockchain import Blockchain

class FileManager:
    """
    Manages secure file operations with blockchain tracking
    """
    
    def __init__(self, storage_dir="secure_storage", metadata_file="file_metadata.json"):
        """Initialize the file manager with storage directory and metadata file"""
        self.storage_dir = storage_dir
        self.metadata_file = os.path.join(storage_dir, metadata_file)
        self.blockchain = Blockchain()
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            
        # Create metadata file if it doesn't exist
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'w') as f:
                json.dump({}, f)
    
    def get_metadata(self):
        """Load file metadata from JSON file"""
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Reset metadata if file is missing or corrupted
            return {}
    
    def save_metadata(self, metadata):
        """Save file metadata to JSON file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)
    
    def store_file(self, file_path, password, description=""):
        """
        Store a file securely in the storage directory
        - Encrypts the file
        - Records the file in the blockchain
        - Updates metadata
        Returns: file_id (for future reference)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Generate a unique file ID based on filename and timestamp
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_id = f"{filename}_{timestamp}"
        
        # Create encrypted file path
        encrypted_path = os.path.join(self.storage_dir, f"{file_id}.enc")
        
        # Encrypt the file
        _, salt, iv, original_hash = Crypto.encrypt_file(file_path, password, encrypted_path)
        
        # Add file to blockchain
        self.blockchain.create_block(file_id, original_hash)
        
        # Update metadata
        metadata = self.get_metadata()
        metadata[file_id] = {
            "original_filename": filename,
            "encrypted_path": encrypted_path,
            "description": description,
            "timestamp": timestamp,
            "salt": base64.b64encode(salt).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8')
        }
        self.save_metadata(metadata)
        
        return file_id
    
    def retrieve_file(self, file_id, password, output_dir=None):
        """
        Retrieve and decrypt a file from secure storage
        Returns: (output_path, integrity_verified)
        """
        # Get metadata for the file
        metadata = self.get_metadata()
        
        if file_id not in metadata:
            raise ValueError(f"File ID not found: {file_id}")
            
        file_info = metadata[file_id]
        encrypted_path = file_info["encrypted_path"]
        
        if not os.path.exists(encrypted_path):
            raise FileNotFoundError(f"Encrypted file not found: {encrypted_path}")
        
        # Determine output directory and path
        if output_dir is None:
            output_dir = os.getcwd()
            
        output_path = os.path.join(output_dir, file_info["original_filename"])
        
        # Decrypt the file
        decrypted_path, success = Crypto.decrypt_file(encrypted_path, password, output_path)
        
        if not success:
            return None, False
            
        # Verify file integrity using blockchain
        current_hash = Crypto.calculate_file_hash(decrypted_path)
        integrity_verified = self.blockchain.verify_file_integrity(file_id, current_hash)
        
        return decrypted_path, integrity_verified
    
    def delete_file(self, file_id):
        """
        Delete a file from secure storage and update metadata
        Returns: success (boolean)
        """
        metadata = self.get_metadata()
        
        if file_id not in metadata:
            return False
            
        # Get file path from metadata
        encrypted_path = metadata[file_id]["encrypted_path"]
        
        # Delete the file if it exists
        if os.path.exists(encrypted_path):
            os.remove(encrypted_path)
            
        # Update metadata
        del metadata[file_id]
        self.save_metadata(metadata)
        
        return True
    
    def list_files(self):
        """
        List all files in secure storage with metadata
        Returns: dictionary of file metadata
        """
        return self.get_metadata()
    
    def verify_all_files(self):
        """
        Verify the integrity of all files in the blockchain
        Returns: dictionary with file_id -> integrity status
        """
        # Verify blockchain integrity first
        chain_valid = self.blockchain.verify_chain_integrity()
        
        if not chain_valid:
            return {"blockchain_valid": False}
        
        results = {"blockchain_valid": True}
        
        # No need to verify individual files here since we don't have 
        # the decrypted files or the password to decrypt them
        # This just confirms the blockchain itself is valid
        
        return results
    
    def get_file_history(self, file_id):
        """
        Get the history of a file from the blockchain
        Returns: list of history entries
        """
        return self.blockchain.get_file_history(file_id) 