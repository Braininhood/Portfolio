# Cybersecurity Portfolio

This repository contains a collection of cybersecurity projects and tools focused on network security, cryptography, authentication mechanisms, vulnerability scanning, system monitoring, and data privacy compliance.

## Projects

### [GDPR-Compliance-Checker](./GDPR_Compliance_Checker/)
- **Description**: GUI-based desktop application that scans websites for GDPR compliance issues and provides detailed remediation recommendations.
- **Features**:
  - Cookie consent verification (banners, granular options)
  - Privacy policy analysis
  - Data collection forms assessment
  - Third-party services detection
  - Data subject rights verification
  - Legal basis analysis
  - International data transfer detection
  - Security measures assessment (HTTPS, disclosures)
  - Comprehensive reporting with remediation guidelines
- **Technologies**: Python, PyQt5, Beautiful Soup 4, Requests
- **Files**:
  - `app.py` - Main application with GUI and scanning logic
  - `GDPR_Compliance_Checker.vbs` - Launcher that hides command window
  - `requirements.txt` - Dependencies for the project

### [Website-Vulnerability-Scanner](./Website-Vulnerability-Scanner/)
- **Description**: GUI-based scanner that checks websites for common security vulnerabilities.
- **Features**:
  - Security headers check (OWASP recommendations)
  - Open ports scanning (TCP & UDP)
  - CMS detection (WordPress, Joomla, Drupal, Magento)
  - SQL Injection vulnerability check
  - XSS vulnerability check
  - API endpoint discovery
  - Sensitive file/directory exposure check
  - GUI interface using Tkinter
- **Technologies**: Python, Tkinter, requests, bs4
- **Files**:
  - `Website_Vulnerability_Scanner.py` - Main scanner implementation

### [System-Monitor](./System-Monitor/)
- **Description**: Comprehensive real-time system monitoring tool for security and performance analysis.
- **Features**:
  - System health monitoring (CPU, memory, disk, swap usage)
  - Process management with filtering options
  - Network usage monitoring
  - Memory leak detection
  - Customizable update intervals
- **Technologies**: Python, psutil
- **Files**:
  - `system.py` - Main monitoring implementation

### [OTP-Generator](./OTP-Generator/)
- **Description**: Secure One-Time Password generator using Fibonacci sequence mapping and proportional mean calculations.
- **Features**:
  - Fibonacci sequence mapping for enhanced security
  - Proportional mean calculation for unpredictability
  - Multiple OTP generation modes with varying complexity
  - GUI interface built with Tkinter
- **Technologies**: Python, Tkinter
- **Files**:
  - `project.py` - Main application with OTP generation logic
  - `test_project.py` - Test suite for the OTP generator
  - `requirements.txt` - Dependencies for the project

### [Network-Monitoring-Tool](./Network-Monitoring-Tool/)
- **Description**: Advanced network monitoring tool built with Python and Scapy that detects potential security threats like port scans and SYN floods.
- **Features**:
  - Real-time network traffic monitoring
  - **Port scan detection** - Identifies when an IP address attempts to access multiple ports in a short time
  - **SYN flood detection** - Detects potential denial-of-service attacks with excessive SYN packets
  - **Malicious IP detection** using threat intelligence database
  - **Full IPv4 and IPv6 support**
  - **Custom malicious IP management**
  - **Comprehensive Help & Usage Guide** built into the application
  - Graphical user interface with CustomTkinter
  - Support for multiple network interfaces
  - Network traffic statistics
  - Configurable detection thresholds
  - Subnet filtering for focused monitoring
- **Technologies**: Python, Scapy, CustomTkinter
- **Files**:
  - `network_Monitoring_Tool.py` - Command-line interface implementation
  - `GUI_Network_Monitor.py` - Graphical interface implementation
  - `requirements.txt` - Dependencies including Scapy
  - `Start_Network_Monitor.bat` - Windows launcher script
- **Platform Support**:
  - Windows: Requires Npcap for optimal functionality
  - Linux: Requires root privileges and libpcap
- **Usage**:
  - Windows: Run `Start_Network_Monitor.bat`
  - Linux: Run `sudo python GUI_Network_Monitor.py`

### [Fibonacci-numbers](./Fibonacci-numbers/)
- **Description**: Implementation of OTP and cipher algorithms using Fibonacci sequences.
- **Features**:
  - Fibonacci-based cipher for text encryption
  - OTP generation using Fibonacci numbers
- **Technologies**: Python, Jupyter Notebook
- **Files**:
  - `Fibonacci_cipher.ipynb` - Jupyter notebook with Fibonacci cipher implementation
  - `Fibonacci_numbers_and_OTP.ipynb` - Jupyter notebook with OTP implementation

### [CIPHER-APPLICATION](./CIPHER-APPLICATION/)
- **Description**: Web-based application for encrypting and decrypting messages using various cipher techniques.
- **Features**:
  - User authentication with secure password requirements
  - Multiple cipher methods: Fibonacci, Caesar, Vigenère, Atbash
  - Responsive web design
  - Session management
- **Technologies**: Python, Flask, SQLite, HTML/CSS/JavaScript
- **Files**:
  - `app.py` - Main Flask application
  - `cipher_functions.py` - Implementation of cipher algorithms
  - `users.py` - User management and authentication
  - `users.db` - SQLite database for user information
  - `templates/` - HTML templates for the web interface
  - `static/` - CSS and JavaScript files

### [Checker-connection-DNS-mapping](./Checker-connection-DNS-mapping/)
- **Description**: Tool for monitoring server connections and performing DNS mapping.
- **Features**:
  - Domain name resolution and reverse DNS lookup
  - IP address and domain name validation
  - Server connection monitoring
  - DNS record mapping (A, AAAA, MX, NS, CNAME, TXT)
- **Technologies**: Python, Jupyter Notebook
- **Files**:
  - `Server connection monitoring.ipynb` - Jupyter notebook with implementation

### [Secure-File-Storage-Blockchain](./Secure-File-Storage-Blockchain/)
- **Description**: Secure file storage system using encryption and blockchain technology to ensure file integrity and security.
- **Features**:
  - Strong AES-256-CBC encryption with PBKDF2 key derivation
  - Blockchain verification for file operations
  - Multiple interfaces (Web, CLI, and Desktop GUI)
  - Metadata management and file history tracking
  - Tamper detection through blockchain validation
- **Technologies**: Python, AES encryption, blockchain, Flask (web interface), PyQt5 (desktop GUI)
- **Files**:
  - `crypto.py` - Encryption/decryption module
  - `file_manager.py` - File operations management
  - `blockchain.py` - Blockchain implementation
  - `gui_app.py` - Desktop application
  - `cli.py` - Command-line interface
  - `run_web.py` - Web interface server

### [PasswordManager](./PasswordManager/)
- **Description**: Zero-knowledge password manager where encryption/decryption happens client-side for maximum security.
- **Features**:
  - Zero-knowledge architecture (server never has access to unencrypted data)
  - AES-256 encryption with client-side processing
  - Password strength analysis
  - Secure password generator
  - Search and organization features
  - Import/export functionality
  - Auto-lock for additional security
- **Technologies**: Python, PyQt5, Django, React, cryptography libraries
- **Files**:
  - `DesktopApp/password_manager.py` - Main Python desktop application
  - `WebApp/backend/` - Django REST API backend
  - `WebApp/frontend/` - React-based frontend

## Standalone Notebooks

### [CaesarCipherChallenge.ipynb](./CaesarCipherChallenge.ipynb)
- **Description**: Implementation and analysis of the Caesar cipher encryption method.
- **Features**:
  - Basic Caesar cipher encryption and decryption
  - Brute force decryption demonstrations
  - Handling of special characters and spaces

### [Base64EncodingChallenge.ipynb](./Base64EncodingChallenge.ipynb)
- **Description**: Exercises and demonstrations of Base64 encoding and related conversions.
- **Features**:
  - Converting decimal to hexadecimal
  - Converting strings to hexadecimal values
  - Converting hexadecimal to binary
  - Base64 encoding of images

## Technologies Used

- **Programming Languages**: Python
- **Libraries**: Scapy, Tkinter, CustomTkinter, PyQt5, Flask, psutil, requests, bs4, termcolor, cryptography, Beautiful Soup
- **Web Technologies**: HTML, CSS, JavaScript
- **Database**: SQLite
- **Development Environment**: Jupyter Notebooks, VS Code

## Getting Started

1. Clone the repository
2. Navigate to the desired project folder
3. Install dependencies from the project's requirements.txt file:
   ```
   pip install -r requirements.txt
   ```
4. Run the main application file or open the Jupyter notebook

## Security Note

Some of these tools and programs are designed for educational purposes and security testing. Always ensure you have proper authorization before using these tools on any network or system you do not own.

## License

Each project may have its own license. Please check the individual project folders for license information. 