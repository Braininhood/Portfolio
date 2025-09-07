# Zero-Knowledge Password Manager

A secure password manager with zero-knowledge architecture, where all encryption and decryption happens client-side. The server or application never has access to your unencrypted credentials.

## Project Overview

This repository contains two implementations of a zero-knowledge password manager:

1. **WebApp** - A web-based solution with Django backend and React frontend
2. **Python Desktop App** - A native cross-platform desktop application built with Python and PyQt5

Both implementations share the same security principles and zero-knowledge architecture.

## Features

- Zero-knowledge architecture - your data is encrypted/decrypted locally
- Master password is never sent to the server or stored anywhere
- Strong encryption using AES-256
- Password strength analysis
- Secure password generator with customizable options
- Search and organize your passwords
- Import/export functionality
- Auto-lock for additional security

## Tech Stack

### Web Application
- **Backend**: Django, Django REST Framework
- **Frontend**: React, React Router, Styled Components
- **Encryption**: CryptoJS for client-side encryption
- **Authentication**: Token-based authentication

### Desktop Application
- **UI Framework**: PyQt5
- **Encryption**: Python cryptography library, AES-GCM
- **Storage**: Local encrypted vault files
- **Authentication**: Local user accounts

## How Zero-Knowledge Security Works

1. When you create an account, you set a master password
2. The master password is used to derive an encryption key using PBKDF2 with 100,000 iterations
3. A salt is generated and stored alongside the encrypted data
4. Your passwords and other sensitive data are encrypted using the derived key
5. Only the encrypted data and salt are stored - never the master password or plaintext data
6. Decryption happens entirely client-side using your master password
7. If you forget your master password, your data cannot be recovered

## Setup Instructions

### Web Application

#### Backend Setup

1. Navigate to the WebApp/backend directory:
   ```
   cd WebApp/backend
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Start the Django development server:
   ```
   python manage.py runserver
   ```

#### Frontend Setup

1. Navigate to the WebApp/frontend directory:
   ```
   cd WebApp/frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the React development server:
   ```
   npm start
   ```

4. Open your browser and go to http://localhost:3000

### Python Desktop Application

1. Navigate to the DesktopApp directory:
   ```
   cd DesktopApp
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install PyQt5 cryptography pycryptodome pyperclip
   ```

4. Run the application:
   ```
   python password_manager.py
   ```

## Security Considerations

- The master password is the only way to decrypt your data. If lost, your data cannot be recovered.
- All cryptographic operations happen locally on your device.
- The Python app stores encrypted vaults in `~/.secure_vault/` directory.
- The web app uses secure browser storage with additional server-side encrypted backups.
- For production web deployments, enable HTTPS to protect data in transit.
- Regular security audits are recommended.

## Development

If you want to contribute or extend the application:

1. **WebApp**: The backend API is in Django, and the frontend is a React SPA.
2. **Python App**: Built with PyQt5 for UI and uses the Python cryptography library for encryption.

Both applications implement similar security principles with a focus on zero-knowledge architecture.

## License

MIT

