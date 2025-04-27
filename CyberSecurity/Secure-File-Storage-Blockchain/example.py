#!/usr/bin/env python3
"""
Secure File Storage CLI - Command-line interface for secure file operations with blockchain verification.
This tool enables secure storage, retrieval, and verification of files using strong encryption
and blockchain-based integrity verification.
"""

import os
import sys
import argparse
import logging
import getpass
from datetime import datetime
from pathlib import Path
from colorama import init, Fore, Style
from tabulate import tabulate

# Initialize colorama for cross-platform colored terminal output
init()

# Import core modules
try:
    from crypto import Crypto
    from file_manager import FileManager
    from blockchain import Blockchain
except ImportError as e:
    print(f"{Fore.RED}Error importing core modules: {e}{Style.RESET_ALL}")
    print("Make sure the application is installed correctly and you're running from the correct directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("secure_storage.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("secure_storage")

class SecureStorageCLI:
    """Command-line interface for the Secure File Storage system."""
    
    def __init__(self):
        """Initialize the CLI with FileManager and set up argument parser."""
        try:
            self.file_manager = FileManager()
            self.storage_dir = self.file_manager.storage_dir
            
            # Ensure storage directory exists
            os.makedirs(self.storage_dir, exist_ok=True)
            
            logger.debug("Initialized CLI with FileManager")
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            print(f"{Fore.RED}Failed to initialize the application: {e}{Style.RESET_ALL}")
            sys.exit(1)
    
    def setup_parser(self):
        """Configure the argument parser with supported commands."""
        parser = argparse.ArgumentParser(
            description=f"{Fore.CYAN}Secure File Storage with Blockchain Verification{Style.RESET_ALL}",
            epilog="For more information, see README.md"
        )
        
        # Create subparsers for different commands
        subparsers = parser.add_subparsers(dest="command", help="Command to execute")
        
        # Store file command
        store_parser = subparsers.add_parser("store", help="Store and encrypt a file")
        store_parser.add_argument("file_path", help="Path to the file to store")
        store_parser.add_argument("--password", help="Password for encryption (not recommended, use prompt instead)")
        store_parser.add_argument("--description", help="Description of the file", default="")
        
        # Retrieve file command
        retrieve_parser = subparsers.add_parser("retrieve", help="Retrieve and decrypt a file")
        retrieve_parser.add_argument("file_id", help="ID of the file to retrieve")
        retrieve_parser.add_argument("--password", help="Password for decryption (not recommended, use prompt instead)")
        retrieve_parser.add_argument("--output-dir", help="Directory to save the decrypted file")
        
        # List files command
        subparsers.add_parser("list", help="List all stored files")
        
        # Delete file command
        delete_parser = subparsers.add_parser("delete", help="Delete a stored file")
        delete_parser.add_argument("file_id", help="ID of the file to delete")
        delete_parser.add_argument("--force", action="store_true", help="Delete without confirmation")
        
        # Verify blockchain command
        subparsers.add_parser("verify", help="Verify the blockchain integrity")
        
        # File details command
        details_parser = subparsers.add_parser("details", help="Show details of a specific file")
        details_parser.add_argument("file_id", help="ID of the file to show details for")
        
        # Version info
        subparsers.add_parser("version", help="Show version information")
        
        # Add verbose flag to all commands
        parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
        
        return parser
    
    def get_password(self, args, confirm=False):
        """Securely get password from user if not provided in args."""
        if args.password:
            logger.warning("Password provided via command line is insecure")
            return args.password
        
        if confirm:
            while True:
                password = getpass.getpass("Enter encryption password: ")
                if len(password) < 8:
                    print(f"{Fore.YELLOW}Warning: Password is too short. Recommended length is at least 12 characters.{Style.RESET_ALL}")
                
                confirm_password = getpass.getpass("Confirm password: ")
                if password == confirm_password:
                    break
                print(f"{Fore.RED}Passwords do not match. Please try again.{Style.RESET_ALL}")
        else:
            password = getpass.getpass("Enter decryption password: ")
        
        return password
    
    def run(self):
        """Parse arguments and execute the appropriate command."""
        parser = self.setup_parser()
        args = parser.parse_args()
        
        # Set logging level based on verbose flag
        if args.verbose:
            logger.setLevel(logging.DEBUG)
            logger.debug("Verbose mode enabled")
        
        # Execute the appropriate command
        if args.command == "store":
            self.store_file(args)
        elif args.command == "retrieve":
            self.retrieve_file(args)
        elif args.command == "list":
            self.list_files()
        elif args.command == "delete":
            self.delete_file(args)
        elif args.command == "verify":
            self.verify_blockchain()
        elif args.command == "details":
            self.file_details(args)
        elif args.command == "version":
            self.show_version()
        else:
            parser.print_help()
    
    def store_file(self, args):
        """Store and encrypt a file."""
        try:
            file_path = Path(args.file_path)
            
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                print(f"{Fore.RED}Error: File not found: {file_path}{Style.RESET_ALL}")
                return
            
            file_size = file_path.stat().st_size
            print(f"File: {Fore.CYAN}{file_path.name}{Style.RESET_ALL}")
            print(f"Size: {self.format_size(file_size)}")
            
            password = self.get_password(args, confirm=True)
            
            print(f"{Fore.YELLOW}Encrypting and storing file...{Style.RESET_ALL}")
            start_time = datetime.now()
            
            file_id = self.file_manager.store_file(str(file_path), password, args.description)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            print(f"{Fore.GREEN}File stored successfully!{Style.RESET_ALL}")
            print(f"File ID: {Fore.YELLOW}{file_id}{Style.RESET_ALL}")
            print(f"Processing time: {duration:.2f} seconds")
            print(f"Storage location: {self.storage_dir}")
            print(f"\n{Fore.CYAN}Important: Keep your File ID and password safe. There is no way to recover them.{Style.RESET_ALL}")
            
            logger.info(f"File stored: {file_path.name} -> {file_id}")
        
        except Exception as e:
            logger.error(f"Error storing file: {e}", exc_info=args.verbose)
            print(f"{Fore.RED}Error storing file: {e}{Style.RESET_ALL}")
    
    def retrieve_file(self, args):
        """Retrieve and decrypt a file."""
        try:
            file_id = args.file_id
            
            # First check if the file exists
            metadata = self.file_manager.get_metadata()
            if file_id not in metadata:
                logger.error(f"File ID not found: {file_id}")
                print(f"{Fore.RED}Error: File ID not found: {file_id}{Style.RESET_ALL}")
                return
            
            original_filename = metadata[file_id]["original_filename"]
            print(f"File ID: {Fore.CYAN}{file_id}{Style.RESET_ALL}")
            print(f"Original filename: {original_filename}")
            
            password = self.get_password(args)
            
            output_dir = args.output_dir
            if output_dir:
                output_dir = Path(output_dir)
                if not output_dir.exists():
                    print(f"Creating output directory: {output_dir}")
                    output_dir.mkdir(parents=True, exist_ok=True)
                output_dir = str(output_dir)
            
            print(f"{Fore.YELLOW}Retrieving and decrypting file...{Style.RESET_ALL}")
            start_time = datetime.now()
            
            output_path, integrity_verified = self.file_manager.retrieve_file(file_id, password, output_dir)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if output_path:
                print(f"{Fore.GREEN}File retrieved successfully!{Style.RESET_ALL}")
                print(f"Output path: {output_path}")
                print(f"Processing time: {duration:.2f} seconds")
                
                if integrity_verified:
                    print(f"Blockchain integrity verification: {Fore.GREEN}PASSED{Style.RESET_ALL}")
                else:
                    print(f"Blockchain integrity verification: {Fore.RED}FAILED{Style.RESET_ALL}")
                    print(f"{Fore.RED}WARNING: The file may have been tampered with!{Style.RESET_ALL}")
                
                logger.info(f"File retrieved: {file_id} -> {output_path} (Integrity: {integrity_verified})")
            else:
                print(f"{Fore.RED}Failed to decrypt the file. Check your password.{Style.RESET_ALL}")
                logger.error(f"Failed to decrypt file: {file_id}")
        
        except Exception as e:
            logger.error(f"Error retrieving file: {e}", exc_info=args.verbose)
            print(f"{Fore.RED}Error retrieving file: {e}{Style.RESET_ALL}")
    
    def list_files(self):
        """List all stored files with their metadata."""
        try:
            files = self.file_manager.list_files()
            
            if not files:
                print(f"{Fore.YELLOW}No files stored.{Style.RESET_ALL}")
                return
            
            print(f"{Fore.GREEN}Found {len(files)} stored files:{Style.RESET_ALL}")
            
            # Prepare data for tabulate
            table_data = []
            for file_id, metadata in files.items():
                table_data.append([
                    file_id,
                    metadata['original_filename'],
                    metadata.get('description', 'N/A'),
                    metadata['timestamp']
                ])
            
            # Sort by timestamp (newest first)
            table_data.sort(key=lambda x: x[3], reverse=True)
            
            # Display as table
            print(tabulate(
                table_data,
                headers=["File ID", "Filename", "Description", "Timestamp"],
                tablefmt="pretty"
            ))
            
            logger.info(f"Listed {len(files)} files")
        
        except Exception as e:
            logger.error(f"Error listing files: {e}", exc_info=True)
            print(f"{Fore.RED}Error listing files: {e}{Style.RESET_ALL}")
    
    def delete_file(self, args):
        """Delete a stored file."""
        try:
            file_id = args.file_id
            
            # Check if the file exists
            metadata = self.file_manager.get_metadata()
            if file_id not in metadata:
                logger.error(f"File ID not found: {file_id}")
                print(f"{Fore.RED}Error: File ID not found: {file_id}{Style.RESET_ALL}")
                return
            
            original_filename = metadata[file_id]["original_filename"]
            
            # Confirm deletion
            if not args.force:
                print(f"You are about to delete: {Fore.CYAN}{original_filename}{Style.RESET_ALL} (ID: {file_id})")
                confirm = input(f"Are you sure? This cannot be undone! (y/N): ")
                if confirm.lower() != 'y':
                    print("Deletion cancelled.")
                    return
            
            success = self.file_manager.delete_file(file_id)
            
            if success:
                print(f"{Fore.GREEN}File deleted successfully.{Style.RESET_ALL}")
                logger.info(f"File deleted: {file_id} ({original_filename})")
            else:
                print(f"{Fore.RED}Failed to delete file.{Style.RESET_ALL}")
                logger.error(f"Failed to delete file: {file_id}")
        
        except Exception as e:
            logger.error(f"Error deleting file: {e}", exc_info=True)
            print(f"{Fore.RED}Error deleting file: {e}{Style.RESET_ALL}")
    
    def verify_blockchain(self):
        """Verify the blockchain integrity."""
        try:
            print(f"{Fore.YELLOW}Verifying blockchain integrity...{Style.RESET_ALL}")
            start_time = datetime.now()
            
            results = self.file_manager.verify_all_files()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if results.get("blockchain_valid", False):
                print(f"{Fore.GREEN}Blockchain integrity verified: PASSED{Style.RESET_ALL}")
                print(f"Verification completed in {duration:.2f} seconds")
                logger.info("Blockchain verification passed")
            else:
                print(f"{Fore.RED}Blockchain integrity verified: FAILED{Style.RESET_ALL}")
                print(f"{Fore.RED}WARNING: The blockchain may have been tampered with!{Style.RESET_ALL}")
                logger.critical("Blockchain verification failed")
        
        except Exception as e:
            logger.error(f"Error verifying blockchain: {e}", exc_info=True)
            print(f"{Fore.RED}Error verifying blockchain: {e}{Style.RESET_ALL}")
    
    def file_details(self, args):
        """Show detailed information about a specific file."""
        try:
            file_id = args.file_id
            
            # Check if the file exists
            metadata = self.file_manager.get_metadata()
            if file_id not in metadata:
                logger.error(f"File ID not found: {file_id}")
                print(f"{Fore.RED}Error: File ID not found: {file_id}{Style.RESET_ALL}")
                return
            
            file_info = metadata[file_id]
            
            print(f"\n{Fore.CYAN}File Details:{Style.RESET_ALL}")
            print(f"File ID: {Fore.YELLOW}{file_id}{Style.RESET_ALL}")
            print(f"Original filename: {file_info['original_filename']}")
            print(f"Description: {file_info.get('description', 'N/A')}")
            print(f"Encrypted path: {file_info['encrypted_path']}")
            print(f"Created on: {file_info['timestamp']}")
            
            # Get file history from blockchain
            print(f"\n{Fore.CYAN}Blockchain History:{Style.RESET_ALL}")
            history = self.file_manager.get_file_history(file_id)
            
            if history:
                for i, entry in enumerate(history):
                    block_time = datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00'))
                    print(f"{i+1}. Block #{entry['block_index']} - {block_time}")
            else:
                print("No blockchain history found.")
            
            logger.info(f"Displayed details for file: {file_id}")
        
        except Exception as e:
            logger.error(f"Error showing file details: {e}", exc_info=True)
            print(f"{Fore.RED}Error showing file details: {e}{Style.RESET_ALL}")
    
    def show_version(self):
        """Show version and system information."""
        print(f"\n{Fore.CYAN}Secure File Storage with Blockchain Verification{Style.RESET_ALL}")
        print(f"Version: 1.0.0")
        print(f"Python: {sys.version.split()[0]}")
        print(f"Storage directory: {self.storage_dir}")
        print(f"Blockchain file: {self.file_manager.blockchain.blockchain_file}")
        print("\nComponents:")
        print(f"- Crypto: AES-256-CBC with PBKDF2")
        print(f"- Blockchain: Proof-of-Work with SHA-256")
        print(f"- File Manager: Metadata and file operations\n")
    
    @staticmethod
    def format_size(size_bytes):
        """Format file size from bytes to human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def main():
    """Entry point for the application."""
    try:
        # Show banner
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"  Secure File Storage with Blockchain Verification")
        print(f"{'=' * 60}{Style.RESET_ALL}\n")
        
        # Create and run the CLI
        cli = SecureStorageCLI()
        cli.run()
    
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation cancelled by user.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}Critical error: {e}{Style.RESET_ALL}")
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 