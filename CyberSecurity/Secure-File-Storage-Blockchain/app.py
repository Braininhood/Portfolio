import os
import uuid
import json
from datetime import datetime
from blockchain import Blockchain
from crypto import Crypto

class SecureFileStorage:
    """Main application class that integrates blockchain and cryptography modules"""
    
    def __init__(self, storage_dir="secure_storage", blockchain_file="blockchain.json"):
        self.storage_dir = storage_dir
        self.blockchain_file = blockchain_file
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            os.makedirs(os.path.join(storage_dir, "encrypted"))
        
        # Initialize blockchain file if it doesn't exist
        if not os.path.exists(blockchain_file):
            with open(blockchain_file, 'w') as f:
                json.dump({"chain": []}, f)
    
    def store_file(self, file_path, password):
        """Encrypt and store a file, recording its hash in the blockchain"""
        try:
            # Generate a unique file ID
            file_id = str(uuid.uuid4())
            file_name = os.path.basename(file_path)
            encrypted_path = os.path.join(self.storage_dir, "encrypted", f"{file_id}_{file_name}.enc")
            
            # Derive encryption key from password
            key = Crypto.derive_key(password, Crypto.SALT_LENGTH * b'\0')
            
            # Encrypt the file and get original file hash
            file_hash = Crypto.calculate_file_hash(file_path)
            Crypto.encrypt_file(file_path, password, encrypted_path)
            
            # Store the file metadata
            metadata = {
                "file_id": file_id,
                "original_name": file_name,
                "encrypted_path": encrypted_path,
                "timestamp": datetime.now().isoformat()
            }
            
            metadata_path = os.path.join(self.storage_dir, f"{file_id}.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            # Add file info to blockchain
            Blockchain.create_block(file_id, file_hash)
            
            return {
                "status": "success",
                "file_id": file_id,
                "message": f"File encrypted and stored with ID: {file_id}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to store file: {str(e)}"
            }
    
    def retrieve_file(self, file_id, password, output_path=None):
        """Retrieve and decrypt a file, verifying its integrity against the blockchain"""
        try:
            # Get file metadata
            metadata_path = os.path.join(self.storage_dir, f"{file_id}.json")
            if not os.path.exists(metadata_path):
                return {
                    "status": "error",
                    "message": f"File with ID {file_id} not found"
                }
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Set output path if not provided
            if output_path is None:
                output_path = os.path.join(self.storage_dir, metadata["original_name"])
            
            # Decrypt the file
            output_path, success = Crypto.decrypt_file(metadata["encrypted_path"], password, output_path)
            
            if not success:
                return {
                    "status": "error",
                    "message": "Failed to decrypt file. Check your password."
                }
            
            # Verify file integrity against blockchain
            file_hash = Crypto.calculate_file_hash(output_path)
            is_valid = Blockchain.verify_file_integrity(file_id, file_hash)
            
            if not is_valid:
                # If integrity check fails, delete the output file
                os.remove(output_path)
                return {
                    "status": "error",
                    "message": "File integrity check failed! The file may have been tampered with."
                }
            
            return {
                "status": "success",
                "message": f"File successfully retrieved and verified",
                "output_path": output_path
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to retrieve file: {str(e)}"
            }
    
    def verify_blockchain(self):
        """Verify the integrity of the entire blockchain"""
        try:
            is_valid = Blockchain.verify_chain_integrity()
            
            if is_valid:
                return {
                    "status": "success",
                    "message": "Blockchain integrity verified successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": "Blockchain integrity check failed! The chain may have been tampered with."
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to verify blockchain: {str(e)}"
            }
    
    def list_files(self):
        """List all files stored in the system"""
        files = []
        
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    file_id = filename.split('.')[0]
                    
                    with open(os.path.join(self.storage_dir, filename), 'r') as f:
                        metadata = json.load(f)
                    
                    files.append({
                        "file_id": file_id,
                        "original_name": metadata["original_name"],
                        "timestamp": metadata["timestamp"]
                    })
            
            return {
                "status": "success",
                "files": files
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to list files: {str(e)}"
            }

# Simple CLI interface
def display_menu():
    print("\n====== Secure File Storage System ======")
    print("1. Store a file")
    print("2. Retrieve a file")
    print("3. List all files")
    print("4. Verify blockchain integrity")
    print("5. Exit")
    return input("Enter your choice (1-5): ")

def main():
    secure_storage = SecureFileStorage()
    
    while True:
        choice = display_menu()
        
        if choice == '1':
            file_path = input("Enter the path to the file: ")
            password = input("Enter encryption password: ")
            result = secure_storage.store_file(file_path, password)
            print(f"\nResult: {result['status']}")
            print(result['message'])
            
        elif choice == '2':
            file_id = input("Enter the file ID: ")
            password = input("Enter decryption password: ")
            output_path = input("Enter output path (leave blank for default): ")
            
            if not output_path.strip():
                output_path = None
                
            result = secure_storage.retrieve_file(file_id, password, output_path)
            print(f"\nResult: {result['status']}")
            print(result['message'])
            
            if result['status'] == 'success':
                print(f"File saved to: {result.get('output_path')}")
                
        elif choice == '3':
            result = secure_storage.list_files()
            
            if result['status'] == 'success':
                files = result.get('files', [])
                
                if not files:
                    print("\nNo files found.")
                else:
                    print(f"\nFound {len(files)} files:")
                    for file in files:
                        print(f"ID: {file['file_id']}")
                        print(f"Name: {file['original_name']}")
                        print(f"Timestamp: {file['timestamp']}")
                        print("-" * 30)
            else:
                print(f"\nError: {result['message']}")
                
        elif choice == '4':
            result = secure_storage.verify_blockchain()
            print(f"\nResult: {result['status']}")
            print(result['message'])
            
        elif choice == '5':
            print("\nExiting the application. Goodbye!")
            break
            
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main() 