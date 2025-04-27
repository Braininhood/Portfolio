#!/usr/bin/env python3
"""
Secure File Storage CLI - Modern, user-friendly command-line interface
"""

import os
import sys
import time
import getpass
import argparse
from pathlib import Path
from datetime import datetime
import threading
import random

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
    from rich import box
    import questionary
    from questionary import Style
except ImportError:
    print("Required packages not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich", "questionary"])
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
    from rich import box
    import questionary
    from questionary import Style

# Import core modules
try:
    from crypto import Crypto
    from file_manager import FileManager
    from blockchain import Blockchain
except ImportError as e:
    print(f"Error importing core modules: {e}")
    print("Make sure the application is installed correctly and you're running from the correct directory.")
    sys.exit(1)

# Initialize console
console = Console()

# Custom styles
CUSTOM_STYLE = Style([
    ('qmark', 'fg:#673ab7 bold'),       # token in front of the question
    ('question', 'bold fg:#673ab7'),    # question text
    ('answer', 'fg:#f44336 bold'),      # submitted answer text
    ('pointer', 'fg:#673ab7 bold'),     # pointer used in select and checkbox prompts
    ('highlighted', 'fg:#673ab7 bold'), # pointed-at choice in select and checkbox prompts
    ('selected', 'fg:#cc5454'),         # style for a selected item of a checkbox
    ('separator', 'fg:#6b778d'),        # separator in lists
    ('instruction', 'fg:#5b5fc7'),      # user instructions for select, rawselect, checkbox
    ('text', 'fg:#ffffff'),             # plain text
    ('disabled', 'fg:#858585 italic')   # disabled choices for select and checkbox prompts
])

class SecureStorageCLI:
    """Modern CLI interface for Secure File Storage system."""
    
    def __init__(self):
        """Initialize the CLI with FileManager."""
        try:
            self.file_manager = FileManager()
            self.storage_dir = self.file_manager.storage_dir
            
            # Ensure storage directory exists
            os.makedirs(self.storage_dir, exist_ok=True)
            
        except Exception as e:
            console.print(f"[bold red]Failed to initialize: {e}[/bold red]")
            sys.exit(1)
    
    def display_welcome(self):
        """Display welcome banner and information."""
        console.clear()
        welcome_panel = Panel(
            "[bold cyan]Secure File Storage with Blockchain Verification[/bold cyan]\n\n"
            "Store and manage your files with cutting-edge encryption and blockchain verification. "
            "Your files are secured with AES-256-CBC encryption and verified for integrity "
            "using blockchain technology.",
            title="Welcome",
            subtitle="v1.0.0",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(welcome_panel)
    
    def display_menu(self):
        """Display the interactive main menu."""
        while True:
            choice = questionary.select(
                "Select an operation:",
                choices=[
                    "Store a file",
                    "Retrieve a file",
                    "List all files",
                    "Delete a file",
                    "Verify blockchain integrity",
                    "File details",
                    "About",
                    "Exit"
                ],
                style=CUSTOM_STYLE
            ).ask()
            
            if choice == "Store a file":
                self.store_file()
            elif choice == "Retrieve a file":
                self.retrieve_file()
            elif choice == "List all files":
                self.list_files()
            elif choice == "Delete a file":
                self.delete_file()
            elif choice == "Verify blockchain integrity":
                self.verify_blockchain()
            elif choice == "File details":
                self.file_details()
            elif choice == "About":
                self.show_about()
            elif choice == "Exit":
                self.exit_app()
                break
    
    def store_file(self):
        """Interactive file storage with rich UI."""
        console.print("\n[bold blue]== Store and Encrypt a File ==[/bold blue]")
        
        # Get file path with validation
        file_path = questionary.path(
            "Enter the path to the file you want to store:",
            style=CUSTOM_STYLE,
            validate=lambda p: os.path.isfile(p) or "File not found"
        ).ask()
        
        if not file_path:
            return
        
        file_path = Path(file_path)
        file_size = file_path.stat().st_size
        
        console.print(f"File: [cyan]{file_path.name}[/cyan]")
        console.print(f"Size: [yellow]{self.format_size(file_size)}[/yellow]")
        
        # Description (optional)
        description = questionary.text(
            "Enter a description for this file (optional):",
            style=CUSTOM_STYLE
        ).ask()
        
        # Get password with confirmation
        while True:
            password = questionary.password(
                "Enter encryption password:",
                style=CUSTOM_STYLE,
                validate=lambda p: len(p) >= 8 or "Password must be at least 8 characters"
            ).ask()
            
            if not password:
                return
                
            if len(password) < 12:
                console.print("[yellow]Warning: For maximum security, passwords should be at least 12 characters.[/yellow]")
            
            confirm_password = questionary.password(
                "Confirm password:",
                style=CUSTOM_STYLE
            ).ask()
            
            if password == confirm_password:
                break
            else:
                console.print("[bold red]Passwords do not match. Please try again.[/bold red]")
        
        # Confirm operation
        if not Confirm.ask("Ready to encrypt and store the file?", default=True):
            console.print("[yellow]Operation cancelled.[/yellow]")
            return
        
        # Progress animation
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Encrypting and storing file...", total=100)
            
            # Simulate progress steps
            progress.update(task, advance=10)
            time.sleep(0.5)  # Generating encryption keys
            
            # Start encryption in a thread to allow progress updates
            result = {"file_id": None, "error": None}
            
            def encrypt_file():
                try:
                    result["file_id"] = self.file_manager.store_file(str(file_path), password, description)
                except Exception as e:
                    result["error"] = str(e)
            
            encryption_thread = threading.Thread(target=encrypt_file)
            encryption_thread.start()
            
            # Update progress while encryption is running
            while encryption_thread.is_alive():
                # Simulate progress (in a real app, you'd report actual progress)
                current = progress.tasks[task.id].completed
                if current < 90:
                    progress.update(task, advance=random.uniform(1, 5))
                time.sleep(0.3)
                
            encryption_thread.join()
            progress.update(task, completed=100)
        
        if result["error"]:
            console.print(f"[bold red]Error storing file: {result['error']}[/bold red]")
            return
            
        file_id = result["file_id"]
        
        # Success panel
        success_panel = Panel(
            f"[bold green]File stored successfully![/bold green]\n\n"
            f"File ID: [yellow]{file_id}[/yellow]\n"
            f"Storage location: {self.storage_dir}\n\n"
            f"[cyan]Important: Keep your File ID and password safe. There is no way to recover them.[/cyan]",
            title="Success",
            border_style="green",
            padding=(1, 2)
        )
        console.print(success_panel)
        Prompt.ask("Press Enter to continue")
    
    def retrieve_file(self):
        """Interactive file retrieval with rich UI."""
        console.print("\n[bold blue]== Retrieve and Decrypt a File ==[/bold blue]")
        
        # Get files for selection
        files = self.file_manager.list_files()
        if not files:
            console.print("[yellow]No files are currently stored.[/yellow]")
            Prompt.ask("Press Enter to continue")
            return
        
        # Format file choices
        file_choices = []
        for file_id, metadata in files.items():
            file_choices.append({
                'name': f"{metadata['original_filename']} ({file_id})",
                'value': file_id
            })
            
        # Add a cancel option
        file_choices.append({'name': '< Cancel >', 'value': None})
        
        # Select a file
        file_id = questionary.select(
            "Select a file to retrieve:",
            choices=file_choices,
            style=CUSTOM_STYLE
        ).ask()
        
        if not file_id:
            return
        
        # Get metadata for the selected file
        metadata = files[file_id]
        console.print(f"File ID: [cyan]{file_id}[/cyan]")
        console.print(f"Original filename: [cyan]{metadata['original_filename']}[/cyan]")
        
        # Get password
        password = questionary.password(
            "Enter decryption password:",
            style=CUSTOM_STYLE
        ).ask()
        
        if not password:
            return
        
        # Output directory
        default_dir = os.path.join(os.getcwd(), "decrypted")
        output_dir = questionary.path(
            "Enter the directory to save the decrypted file (or press Enter for default):",
            default=default_dir,
            style=CUSTOM_STYLE,
            only_directories=True
        ).ask()
        
        if not output_dir:
            output_dir = default_dir
        
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Confirm operation
        if not Confirm.ask("Ready to decrypt and retrieve the file?", default=True):
            console.print("[yellow]Operation cancelled.[/yellow]")
            return
        
        # Progress animation for decryption
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Retrieving and decrypting file...", total=100)
            
            # Simulate progress steps
            progress.update(task, advance=10)
            time.sleep(0.5)  # Preparing for decryption
            
            # Start decryption in a thread to allow progress updates
            result = {"output_path": None, "integrity_verified": False, "error": None}
            
            def decrypt_file():
                try:
                    result["output_path"], result["integrity_verified"] = self.file_manager.retrieve_file(
                        file_id, password, output_dir
                    )
                except Exception as e:
                    result["error"] = str(e)
            
            decryption_thread = threading.Thread(target=decrypt_file)
            decryption_thread.start()
            
            # Update progress while decryption is running
            while decryption_thread.is_alive():
                # Simulate progress
                current = progress.tasks[task.id].completed
                if current < 90:
                    progress.update(task, advance=random.uniform(1, 5))
                time.sleep(0.3)
                
            decryption_thread.join()
            progress.update(task, completed=100)
        
        if result["error"]:
            console.print(f"[bold red]Error retrieving file: {result['error']}[/bold red]")
            return
            
        output_path = result["output_path"]
        integrity_verified = result["integrity_verified"]
        
        if not output_path:
            console.print("[bold red]Failed to decrypt the file. Check your password.[/bold red]")
            Prompt.ask("Press Enter to continue")
            return
        
        # Success panel
        status_color = "green" if integrity_verified else "red"
        status_text = "PASSED" if integrity_verified else "FAILED"
        warning = "" if integrity_verified else "\n[bold red]WARNING: The file may have been tampered with![/bold red]"
        
        success_panel = Panel(
            f"[bold green]File retrieved successfully![/bold green]\n\n"
            f"Output path: [cyan]{output_path}[/cyan]\n"
            f"Blockchain integrity verification: [{status_color}]{status_text}[/{status_color}]{warning}",
            title="Success",
            border_style="green",
            padding=(1, 2)
        )
        console.print(success_panel)
        Prompt.ask("Press Enter to continue")
    
    def list_files(self):
        """List all stored files in a formatted table."""
        console.print("\n[bold blue]== Stored Files ==[/bold blue]")
        
        files = self.file_manager.list_files()
        
        if not files:
            console.print("[yellow]No files stored.[/yellow]")
            Prompt.ask("Press Enter to continue")
            return
        
        table = Table(title=f"Stored Files ({len(files)} total)", box=box.ROUNDED)
        table.add_column("File ID", style="cyan", no_wrap=True)
        table.add_column("Filename", style="green")
        table.add_column("Description", style="blue")
        table.add_column("Timestamp", style="magenta")
        table.add_column("Size", style="yellow", justify="right")
        
        # Sort by timestamp (newest first)
        sorted_files = sorted(files.items(), key=lambda x: x[1]['timestamp'], reverse=True)
        
        for file_id, metadata in sorted_files:
            # Get size if available
            size = metadata.get('size', 'N/A')
            if isinstance(size, int):
                size = self.format_size(size)
                
            # Truncate description if too long
            description = metadata.get('description', 'N/A')
            if len(description) > 30:
                description = description[:27] + '...'
                
            table.add_row(
                file_id,
                metadata['original_filename'],
                description,
                metadata['timestamp'],
                size
            )
        
        console.print(table)
        Prompt.ask("Press Enter to continue")
    
    def delete_file(self):
        """Delete a stored file with confirmation."""
        console.print("\n[bold blue]== Delete a File ==[/bold blue]")
        
        # Get files for selection
        files = self.file_manager.list_files()
        if not files:
            console.print("[yellow]No files are currently stored.[/yellow]")
            Prompt.ask("Press Enter to continue")
            return
        
        # Format file choices
        file_choices = []
        for file_id, metadata in files.items():
            file_choices.append({
                'name': f"{metadata['original_filename']} ({file_id})",
                'value': file_id
            })
            
        # Add a cancel option
        file_choices.append({'name': '< Cancel >', 'value': None})
        
        # Select a file
        file_id = questionary.select(
            "Select a file to delete:",
            choices=file_choices,
            style=CUSTOM_STYLE
        ).ask()
        
        if not file_id:
            return
        
        # Get metadata for the selected file
        metadata = files[file_id]
        original_filename = metadata["original_filename"]
        
        console.print(f"You are about to delete: [cyan]{original_filename}[/cyan] (ID: {file_id})")
        console.print("[bold red]Warning: This action cannot be undone![/bold red]")
        
        # Confirm deletion
        if not Confirm.ask("Are you sure you want to delete this file?", default=False):
            console.print("[yellow]Deletion cancelled.[/yellow]")
            return
        
        # Delete the file
        with Progress(SpinnerColumn(), TextColumn("[bold red]Deleting file...[/bold red]")) as progress:
            progress.add_task("Deleting", total=None)
            success = self.file_manager.delete_file(file_id)
        
        if success:
            console.print("[bold green]File deleted successfully.[/bold green]")
        else:
            console.print("[bold red]Failed to delete file.[/bold red]")
            
        Prompt.ask("Press Enter to continue")
    
    def verify_blockchain(self):
        """Verify the blockchain integrity."""
        console.print("\n[bold blue]== Blockchain Integrity Verification ==[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Verifying blockchain integrity...[/bold blue]"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Verifying", total=None)
            
            # Start verification in a thread
            result = {"verified": False, "error": None}
            
            def verify():
                try:
                    result["verified"] = self.file_manager.verify_all_files().get("blockchain_valid", False)
                except Exception as e:
                    result["error"] = str(e)
            
            verify_thread = threading.Thread(target=verify)
            verify_thread.start()
            verify_thread.join()
        
        if result["error"]:
            console.print(f"[bold red]Error verifying blockchain: {result['error']}[/bold red]")
            Prompt.ask("Press Enter to continue")
            return
        
        # Display verification result
        if result["verified"]:
            status_panel = Panel(
                "[bold green]✓ Blockchain integrity verified: PASSED[/bold green]\n\n"
                "All blocks in the blockchain have been verified and the chain is intact.",
                title="Verification Result",
                border_style="green",
                padding=(1, 2)
            )
        else:
            status_panel = Panel(
                "[bold red]✗ Blockchain integrity verified: FAILED[/bold red]\n\n"
                "The blockchain may have been tampered with! Some blocks have invalid hashes "
                "or the chain has been modified.",
                title="Verification Result",
                border_style="red",
                padding=(1, 2)
            )
        
        console.print(status_panel)
        Prompt.ask("Press Enter to continue")
    
    def file_details(self):
        """Show detailed information about a specific file."""
        console.print("\n[bold blue]== File Details ==[/bold blue]")
        
        # Get files for selection
        files = self.file_manager.list_files()
        if not files:
            console.print("[yellow]No files are currently stored.[/yellow]")
            Prompt.ask("Press Enter to continue")
            return
        
        # Format file choices
        file_choices = []
        for file_id, metadata in files.items():
            file_choices.append({
                'name': f"{metadata['original_filename']} ({file_id})",
                'value': file_id
            })
            
        # Add a cancel option
        file_choices.append({'name': '< Cancel >', 'value': None})
        
        # Select a file
        file_id = questionary.select(
            "Select a file to view details:",
            choices=file_choices,
            style=CUSTOM_STYLE
        ).ask()
        
        if not file_id:
            return
        
        # Get metadata for the selected file
        file_info = files[file_id]
        
        # Get file history from blockchain
        with Progress(SpinnerColumn(), TextColumn("[bold blue]Loading blockchain history...[/bold blue]")) as progress:
            progress.add_task("Loading", total=None)
            history = self.file_manager.get_file_history(file_id)
            
        # Build a details panel
        details = [
            f"[bold]File ID:[/bold] [yellow]{file_id}[/yellow]",
            f"[bold]Original filename:[/bold] {file_info['original_filename']}",
            f"[bold]Description:[/bold] {file_info.get('description', 'N/A')}",
            f"[bold]Encrypted path:[/bold] {file_info['encrypted_path']}",
            f"[bold]Created on:[/bold] {file_info['timestamp']}"
        ]
        
        details_panel = Panel(
            "\n".join(details),
            title="File Details",
            border_style="blue",
            padding=(1, 2)
        )
        console.print(details_panel)
        
        # Show blockchain history if available
        if history:
            console.print("\n[bold cyan]Blockchain History:[/bold cyan]")
            
            history_table = Table(box=box.ROUNDED)
            history_table.add_column("#", style="dim")
            history_table.add_column("Block #", style="cyan")
            history_table.add_column("Timestamp", style="magenta")
            history_table.add_column("Hash (first 10 chars)", style="green")
            
            for i, entry in enumerate(history):
                block_time = datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00'))
                formatted_time = block_time.strftime('%Y-%m-%d %H:%M:%S')
                
                # Truncate hash for display
                hash_display = entry.get("hash", "N/A")
                if hash_display != "N/A" and len(hash_display) > 10:
                    hash_display = hash_display[:10] + "..."
                
                history_table.add_row(
                    str(i+1),
                    str(entry["block_index"]),
                    formatted_time,
                    hash_display
                )
            
            console.print(history_table)
        else:
            console.print("[yellow]No blockchain history found for this file.[/yellow]")
        
        Prompt.ask("Press Enter to continue")
    
    def show_about(self):
        """Show information about the application."""
        about_md = """
        # Secure File Storage with Blockchain Verification

        **Version:** 1.0.0  
        
        ## Features
        
        * **Strong Encryption**: AES-256-CBC encryption with PBKDF2 key derivation
        * **Blockchain Verification**: Every file operation is recorded in a blockchain
        * **Metadata Management**: Keeps track of all files with metadata
        * **Modern UI**: Intuitive and responsive user interface
        
        ## Components
        
        * **Crypto Module**: AES-256-CBC with PBKDF2
        * **Blockchain**: Proof-of-Work with SHA-256
        * **File Manager**: Metadata and file operations
        
        ## Security
        
        Your files are encrypted using industry-standard AES-256-CBC encryption.
        The blockchain ensures tamper detection and file integrity verification.
        """
        
        console.print(Markdown(about_md))
        Prompt.ask("Press Enter to continue")
    
    def exit_app(self):
        """Exit the application with a goodbye message."""
        goodbye_panel = Panel(
            "[bold cyan]Thank you for using Secure File Storage![/bold cyan]\n\n"
            "Your files remain securely encrypted at rest. Remember to keep your file IDs "
            "and passwords in a safe place.",
            title="Goodbye",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(goodbye_panel)
        time.sleep(1)
    
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
        # Create and run the CLI
        cli = SecureStorageCLI()
        cli.display_welcome()
        cli.display_menu()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Critical error: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 