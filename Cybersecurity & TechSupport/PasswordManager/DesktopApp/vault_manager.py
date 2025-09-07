#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vault Manager - Handles password vault operations.
"""

import os
import json
import uuid
import csv
import io
from datetime import datetime

class VaultManager:
    """Manages password vaults and entries"""
    
    def __init__(self, crypto_service):
        """Initialize the vault manager
        
        Args:
            crypto_service (CryptoService): Cryptography service
        """
        self.crypto_service = crypto_service
        self.current_vault = None
        self.is_locked = True
        self.master_password_hash = None
        self.salt = None
        
        self.app_data_dir = os.path.join(os.path.expanduser('~'), '.secure_vault')
        self.vaults_dir = os.path.join(self.app_data_dir, 'vaults')
        
        # Create vaults directory if it doesn't exist
        if not os.path.exists(self.vaults_dir):
            os.makedirs(self.vaults_dir)
    
    def create_vault(self, user_id, master_password):
        """Create a new vault for a user
        
        Args:
            user_id (str): User ID
            master_password (str): Master password
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If master password is too weak
        """
        if not master_password or len(master_password) < 8:
            raise ValueError("Master password must be at least 8 characters long")
        
        # Generate salt for password hashing
        self.salt = self.crypto_service.generate_salt()
        
        # Set the current salt in the crypto service
        self.crypto_service.current_salt = self.salt
        
        # Hash the master password
        self.master_password_hash = self.crypto_service.hash_password(master_password, self.salt)
        
        # Create empty vault structure
        new_vault = {
            'created': datetime.utcnow().isoformat(),
            'last_modified': datetime.utcnow().isoformat(),
            'version': '1.0',
            'entries': [],
            'settings': {
                'auto_lock_timeout': 5,  # minutes
                'password_generator_defaults': {
                    'length': 16,
                    'include_lowercase': True,
                    'include_uppercase': True,
                    'include_numbers': True,
                    'include_symbols': True,
                    'exclude_similar_chars': False,
                    'exclude_ambiguous': False
                }
            }
        }
        
        # Set as current vault
        self.current_vault = new_vault
        self.is_locked = False
        
        # Save the vault
        return self.save_vault(user_id, master_password)
    
    def save_vault(self, user_id, master_password):
        """Save the current vault to storage
        
        Args:
            user_id (str): User ID
            master_password (str): Master password for encryption
            
        Returns:
            bool: True if successful
        """
        if not self.current_vault:
            raise ValueError("No vault is currently open")
        
        if self.is_locked:
            raise ValueError("Vault is locked. Unlock it first.")
        
        # Update the last_modified timestamp
        self.current_vault['last_modified'] = datetime.utcnow().isoformat()
        
        # Ensure the crypto service has the current salt
        self.crypto_service.current_salt = self.salt
        
        # Encrypt the vault with the master password
        encrypted_vault = self.crypto_service.encrypt_vault(self.current_vault, master_password)
        
        # Prepare the storage object
        vault_data = {
            'salt': self.crypto_service.buffer_to_hex(self.salt),
            'master_password_hash': self.master_password_hash,
            'encrypted_vault': encrypted_vault
        }
        
        # Save to file
        vault_file = os.path.join(self.vaults_dir, f"{user_id}.vault")
        try:
            with open(vault_file, 'w') as f:
                json.dump(vault_data, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving vault: {e}")
            return False
    
    def load_vault(self, user_id, master_password):
        """Load and decrypt a vault from storage
        
        Args:
            user_id (str): User ID
            master_password (str): Master password
            
        Returns:
            bool: True if successful
        """
        vault_file = os.path.join(self.vaults_dir, f"{user_id}.vault")
        
        if not os.path.exists(vault_file):
            raise ValueError("Vault not found")
        
        try:
            with open(vault_file, 'r') as f:
                vault_data = json.load(f)
            
            if not vault_data or not vault_data.get('salt') or not vault_data.get('master_password_hash') or not vault_data.get('encrypted_vault'):
                raise ValueError("Invalid vault data structure")
            
            # Convert salt from hex string to buffer
            self.salt = self.crypto_service.hex_to_buffer(vault_data['salt'])
            
            # Set the current_salt in the crypto_service before decryption
            self.crypto_service.current_salt = self.salt
            
            # Store the password hash for future verification
            self.master_password_hash = vault_data['master_password_hash']
            
            # Verify the master password
            is_password_valid = self.crypto_service.verify_password(
                master_password,
                self.master_password_hash,
                self.salt
            )
            
            if not is_password_valid:
                raise ValueError("Invalid master password")
            
            # Decrypt the vault
            self.current_vault = self.crypto_service.decrypt_vault(
                vault_data['encrypted_vault'],
                master_password
            )
            
            self.is_locked = False
            return True
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error loading vault: {e}")
            return False
    
    def lock_vault(self):
        """Lock the vault (keep encrypted data but require password to access)
        
        Returns:
            bool: True if successful
        """
        self.is_locked = True
        return True
    
    def unlock_vault(self, user_id, master_password):
        """Unlock the vault with the master password
        
        Args:
            user_id (str): User ID
            master_password (str): Master password
            
        Returns:
            bool: True if successful
        """
        try:
            # Reset the lock status to ensure we properly attempt to unlock
            self.is_locked = True
            
            # Attempt to load and unlock the vault
            result = self.load_vault(user_id, master_password)
            
            if not result:
                # If load_vault failed but didn't raise an exception, raise one here
                if self.is_locked:
                    print("Debug: Vault remains locked after load_vault")
                raise ValueError("Failed to unlock the vault with the provided password")
            
            return result
        except ValueError as e:
            print(f"Error unlocking vault: {e}")
            return False
    
    def vault_exists(self, user_id):
        """Check if a vault exists for a user
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: True if vault exists
        """
        vault_file = os.path.join(self.vaults_dir, f"{user_id}.vault")
        return os.path.exists(vault_file)
    
    def is_vault_locked(self):
        """Check if the vault is locked
        
        Returns:
            bool: True if locked
        """
        return self.is_locked
    
    def add_entry(self, entry_data):
        """Add a new entry to the vault
        
        Args:
            entry_data (dict): Entry data
            
        Returns:
            dict: Added entry with ID
        """
        if not self.current_vault:
            raise ValueError("No vault is currently open")
        
        if self.is_locked:
            raise ValueError("Vault is locked. Unlock it first.")
        
        # Validate required fields
        if 'title' not in entry_data or not entry_data['title']:
            raise ValueError("Entry title is required")
        
        # Generate unique ID
        entry_id = str(uuid.uuid4())
        
        # Create the entry with metadata
        new_entry = {
            'id': entry_id,
            'title': entry_data.get('title', ''),
            'username': entry_data.get('username', ''),
            'password': entry_data.get('password', ''),
            'url': entry_data.get('url', ''),
            'notes': entry_data.get('notes', ''),
            'category': entry_data.get('category', 'login'),
            'tags': entry_data.get('tags', []),
            'favorite': entry_data.get('favorite', False),
            'created': datetime.utcnow().isoformat(),
            'last_modified': datetime.utcnow().isoformat()
        }
        
        # Add to vault
        self.current_vault['entries'].append(new_entry)
        
        return new_entry
    
    def get_entry(self, entry_id):
        """Get a password entry by ID
        
        Args:
            entry_id (str): Entry ID
            
        Returns:
            dict: Entry or None if not found
        """
        if not self.current_vault:
            raise ValueError("No vault is currently open")
        
        if self.is_locked:
            raise ValueError("Vault is locked. Unlock it first.")
        
        for entry in self.current_vault['entries']:
            if entry['id'] == entry_id:
                return entry
        
        return None
    
    def update_entry(self, entry_id, updated_data):
        """Update an existing entry in the vault
        
        Args:
            entry_id (str): Entry ID
            updated_data (dict): Updated entry data
            
        Returns:
            dict: Updated entry or None if not found
        """
        if not self.current_vault:
            raise ValueError("No vault is currently open")
        
        if self.is_locked:
            raise ValueError("Vault is locked. Unlock it first.")
        
        for i, entry in enumerate(self.current_vault['entries']):
            if entry['id'] == entry_id:
                # Update the entry with new data, preserving fields not included in the update
                updated_entry = entry.copy()
                updated_entry.update(updated_data)
                updated_entry['id'] = entry_id  # Ensure ID doesn't change
                updated_entry['last_modified'] = datetime.utcnow().isoformat()
                
                # Replace the entry in the vault
                self.current_vault['entries'][i] = updated_entry
                
                return updated_entry
        
        return None
    
    def delete_entry(self, entry_id):
        """Delete an entry from the vault
        
        Args:
            entry_id (str): Entry ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if not self.current_vault:
            raise ValueError("No vault is currently open")
        
        if self.is_locked:
            raise ValueError("Vault is locked. Unlock it first.")
        
        for i, entry in enumerate(self.current_vault['entries']):
            if entry['id'] == entry_id:
                # Remove the entry
                del self.current_vault['entries'][i]
                return True
        
        return False
    
    def get_all_entries(self):
        """Get all entries in the vault
        
        Returns:
            list: All entries
        """
        if not self.current_vault:
            raise ValueError("No vault is currently open")
        
        if self.is_locked:
            raise ValueError("Vault is locked. Unlock it first.")
        
        return self.current_vault['entries']
    
    def search_entries(self, query, fields=None):
        """Search entries in the vault
        
        Args:
            query (str): Search query
            fields (list, optional): Fields to search in
            
        Returns:
            list: Matching entries
        """
        if not self.current_vault:
            raise ValueError("No vault is currently open")
        
        if self.is_locked:
            raise ValueError("Vault is locked. Unlock it first.")
        
        if not query:
            return self.current_vault['entries']
        
        if fields is None:
            fields = ['title', 'username', 'url', 'notes']
        
        query = query.lower()
        results = []
        
        for entry in self.current_vault['entries']:
            for field in fields:
                value = entry.get(field, '')
                if value and isinstance(value, str) and query in value.lower():
                    results.append(entry)
                    break
        
        return results
    
    def filter_entries(self, filters):
        """Filter entries by category or tags
        
        Args:
            filters (dict): Filter criteria
            
        Returns:
            list: Filtered entries
        """
        if not self.current_vault:
            raise ValueError("No vault is currently open")
        
        if self.is_locked:
            raise ValueError("Vault is locked. Unlock it first.")
        
        entries = self.current_vault['entries']
        
        # Filter by category
        if filters.get('category'):
            entries = [e for e in entries if e.get('category') == filters['category']]
        
        # Filter by tags (match any)
        if filters.get('tags') and isinstance(filters['tags'], list) and filters['tags']:
            entries = [e for e in entries if any(tag in e.get('tags', []) for tag in filters['tags'])]
        
        # Filter favorites
        if filters.get('favorite') is True:
            entries = [e for e in entries if e.get('favorite') is True]
        
        return entries
    
    def export_vault(self, format='json'):
        """Export vault data
        
        Args:
            format (str): Export format ('json' or 'csv')
            
        Returns:
            str: Exported data as string
        """
        if not self.current_vault:
            raise ValueError("No vault is currently open")
        
        if self.is_locked:
            raise ValueError("Vault is locked. Unlock it first.")
        
        if format == 'json':
            # Export as JSON
            export_data = {
                'entries': self.current_vault['entries'],
                'created': self.current_vault['created'],
                'last_modified': datetime.utcnow().isoformat(),
                'version': self.current_vault['version']
            }
            return json.dumps(export_data, indent=2)
        
        elif format == 'csv':
            # Export as CSV
            fieldnames = ['title', 'username', 'password', 'url', 'notes', 'category', 'tags', 'favorite', 'created', 'last_modified']
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in self.current_vault['entries']:
                row = {field: entry.get(field, '') for field in fieldnames}
                
                # Convert tags list to string
                if 'tags' in row and isinstance(row['tags'], list):
                    row['tags'] = ';'.join(row['tags'])
                
                writer.writerow(row)
            
            return output.getvalue()
        
        else:
            raise ValueError("Unsupported export format")
    
    def import_vault(self, data, format='json', merge=True):
        """Import data into the vault
        
        Args:
            data (str): Data to import
            format (str): Import format ('json' or 'csv')
            merge (bool): Whether to merge with existing data
            
        Returns:
            int: Number of entries imported
        """
        if not self.current_vault:
            raise ValueError("No vault is currently open")
        
        if self.is_locked:
            raise ValueError("Vault is locked. Unlock it first.")
        
        imported_entries = []
        
        if format == 'json':
            # Import from JSON
            try:
                import_data = json.loads(data)
                
                if isinstance(import_data, list):
                    # Assuming array of entries
                    imported_entries = import_data
                elif isinstance(import_data, dict) and 'entries' in import_data and isinstance(import_data['entries'], list):
                    # Assuming full vault structure
                    imported_entries = import_data['entries']
                    
                    # Import settings if available and merging
                    if merge and 'settings' in import_data:
                        self.current_vault['settings'].update(import_data['settings'])
                else:
                    raise ValueError("Invalid JSON import format")
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON data")
        
        elif format == 'csv':
            # Import from CSV
            try:
                reader = csv.DictReader(io.StringIO(data))
                
                for row in reader:
                    entry = {
                        'id': str(uuid.uuid4()),
                        'title': row.get('title', ''),
                        'username': row.get('username', ''),
                        'password': row.get('password', ''),
                        'url': row.get('url', ''),
                        'notes': row.get('notes', ''),
                        'category': row.get('category', 'login'),
                        'favorite': row.get('favorite', '').lower() == 'true',
                        'created': row.get('created', datetime.utcnow().isoformat()),
                        'last_modified': row.get('last_modified', datetime.utcnow().isoformat())
                    }
                    
                    # Convert tags string to list
                    if 'tags' in row and row['tags']:
                        entry['tags'] = [tag.strip() for tag in row['tags'].split(';') if tag.strip()]
                    else:
                        entry['tags'] = []
                    
                    imported_entries.append(entry)
            except csv.Error:
                raise ValueError("Invalid CSV data")
        
        else:
            raise ValueError("Unsupported import format")
        
        # Add imported entries to vault
        if merge:
            # Generate new IDs for imported entries to avoid conflicts
            for entry in imported_entries:
                new_entry = entry.copy()
                new_entry['id'] = str(uuid.uuid4())
                self.current_vault['entries'].append(new_entry)
        else:
            # Replace all entries
            self.current_vault['entries'] = [
                {**entry, 'id': entry.get('id', str(uuid.uuid4()))}
                for entry in imported_entries
            ]
        
        return len(imported_entries)
    
    def delete_user_vault(self, user_id):
        """Delete a user's vault file
        
        Args:
            user_id (str): User ID of the vault to delete
            
        Returns:
            bool: True if successfully deleted, False if not found or error
        """
        vault_file = os.path.join(self.vaults_dir, f"{user_id}.vault")
        
        # Check if the vault exists
        if not os.path.exists(vault_file):
            print(f"No vault found for user {user_id}")
            return False
        
        try:
            # Delete the vault file
            os.remove(vault_file)
            
            # Reset instance variables if the deleted vault was the current one
            if self.current_vault is not None:
                self.current_vault = None
                self.is_locked = True
                self.master_password_hash = None
                self.salt = None
                
            print(f"Vault for user {user_id} has been deleted")
            return True
        except Exception as e:
            print(f"Error deleting vault for user {user_id}: {e}")
            return False 