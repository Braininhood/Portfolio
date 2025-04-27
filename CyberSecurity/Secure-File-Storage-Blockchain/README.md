# Secure File Storage with Blockchain Verification

A secure file storage system that uses strong encryption and blockchain technology to ensure file integrity and security. The application provides three different interfaces for maximum flexibility:

1. **Web Interface**: Browser-based UI for easy access
2. **Command-Line Interface**: Traditional CLI for automation and scripts
3. **Desktop GUI**: Modern desktop application with an intuitive interface

## Features

- **Strong Encryption**: AES-256-CBC encryption with PBKDF2 key derivation
- **Blockchain Verification**: Every file operation is recorded in a blockchain to ensure integrity
- **Modern Interfaces**: Multiple interfaces for different use cases
- **Metadata Management**: Keeps track of all files with metadata
- **Integrity Verification**: Detect tampering attempts through blockchain validation

## System Architecture

The system consists of several core components:

1. **Crypto Module**: Handles file encryption and decryption
2. **File Manager**: Manages file operations and metadata
3. **Blockchain**: Records file operations and ensures integrity

### Crypto Module

The `Crypto` class provides methods for:
- Deriving encryption keys from passwords using PBKDF2
- Encrypting files using AES-256-CBC
- Decrypting files
- Calculating file hashes for integrity verification

### File Manager

The `FileManager` class handles:
- Storing and encrypting files
- Retrieving and decrypting files
- Managing file metadata
- Deleting files
- Listing stored files

### Blockchain

The `Blockchain` class implements:
- A proof-of-work blockchain
- Functions for creating new blocks
- Methods for verifying the chain's integrity
- File history tracking

## Requirements

- Python 3.6+
- Required Python packages (see below for installation)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/secure-file-storage-blockchain.git
   cd secure-file-storage-blockchain
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

The system provides three different interfaces for interacting with the secure file storage:

### 1. Desktop GUI Application

The most user-friendly interface with intuitive controls and modern design.

#### Starting the GUI

```
python gui_app.py
```

#### Features

- **Store Files**: Click "Store File" button or use the toolbar to encrypt and store files
- **Retrieve Files**: Select a file and click "Retrieve File" to decrypt and download
- **File Management**: View file details, delete files, and manage your storage
- **Blockchain Verification**: Verify the integrity of the blockchain with a single click
- **Theme Selection**: Choose between light and dark themes
- **Password Strength Meter**: Visual feedback on password strength when storing files

#### Usage Guide

1. **Storing Files**:
   - Click "Store File" button
   - Select a file from your computer
   - Enter a description (optional)
   - Create and confirm a strong password
   - The file will be encrypted and stored securely

2. **Retrieving Files**:
   - Select a file from the list
   - Click "Retrieve File"
   - Enter the password you used to encrypt the file
   - Choose a location to save the decrypted file

3. **Viewing File Details**:
   - Select a file and click "View Details"
   - See file information and blockchain history

4. **Verifying Blockchain**:
   - Go to the Blockchain tab
   - Click "Verify Blockchain Integrity"
   - View results of the verification

### 2. Command-Line Interface (CLI)

The CLI provides a traditional command-line interface for scripting and automation.

#### Basic Commands

```
python example.py --help
```

Will show all available commands and options.

#### Storing a File

```
python example.py store path/to/file.txt --description "Important document"
```

You will be prompted securely for a password. This will:
- Encrypt the file using the provided password
- Store the encrypted file in the secure storage directory
- Record the operation in the blockchain
- Return a file ID for future reference

#### Retrieving a File

```
python example.py retrieve file_id
```

You will be prompted for the decryption password. This will:
- Retrieve the encrypted file
- Decrypt it using the provided password
- Verify its integrity using the blockchain
- Save it to the specified output directory (or current directory if not specified)

#### Listing Files

```
python example.py list
```

This will display all stored files with their metadata in a tabular format.

#### File Details

```
python example.py details file_id
```

This will show detailed information about a specific file, including its blockchain history.

#### Deleting a File

```
python example.py delete file_id
```

This will prompt for confirmation and then remove the encrypted file and its metadata.

#### Verifying Blockchain Integrity

```
python example.py verify
```

This will verify the integrity of the entire blockchain.

### 3. Interactive CLI

A more user-friendly command-line interface with modern styling and interactive prompts.

#### Starting the Interactive CLI

```
python cli.py
```

This presents an interactive menu with the following options:
- Store a file
- Retrieve a file
- List all files
- Delete a file
- Verify blockchain integrity
- File details
- About
- Exit

Navigate using arrow keys and follow the interactive prompts.

### 4. Web Interface

The web interface provides browser-based access to your secure storage.

#### Starting the Web Server

```
python run_web.py
```

This will start a web server on `http://localhost:5000` (default).

#### Features

- **User Authentication**: Secure login system
- **File Upload**: Encrypt and store files through your browser
- **File Download**: Retrieve and decrypt files
- **File Sharing**: Share files with other users (optional)
- **Blockchain Verification**: Verify file integrity

#### Usage Guide

1. **Login/Register**:
   - Create an account or log in with existing credentials

2. **Upload Files**:
   - Click "Upload" button
   - Select file and enter password
   - File will be encrypted and stored

3. **Download Files**:
   - Click on a file in your dashboard
   - Enter the password
   - File will be decrypted and downloaded

4. **Share Files** (if implemented):
   - Select a file and click "Share"
   - Enter the username of the recipient
   - They will see the file in their shared files section

## Security Considerations

- **Password Strength**: Use strong, unique passwords for each file
- **Password Storage**: This system does not store passwords; they must be provided each time
- **Data at Rest**: All files are encrypted at rest
- **Tamper Protection**: The blockchain ensures that any tampering with files can be detected

## Troubleshooting

### Common Issues

1. **Import Errors**:
   - Ensure all dependencies are installed with `pip install -r requirements.txt`
   - Make sure you're running the commands from the project root directory

2. **File Not Found Errors**:
   - Check that the file paths you're providing are correct
   - Ensure you have the necessary permissions to read/write to those locations

3. **Blockchain Verification Failures**:
   - This could indicate that files have been tampered with
   - Check file integrity and blockchain consistency

4. **GUI Display Issues**:
   - Ensure PyQt5 is installed correctly
   - Try switching between dark and light themes

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Acknowledgments

- Thanks to all the open-source libraries that made this project possible 