# Cybersecurity Portfolio

This repository contains a collection of cybersecurity projects and tools focused on network security, cryptography, and authentication mechanisms.

## Projects

### [OTP-Generator](./OTP-Generator/)
- **Description**: Secure One-Time Password generator using Fibonacci sequence mapping and proportional mean calculations.
- **Features**:
  - Fibonacci sequence mapping for enhanced security
  - Proportional mean calculation for unpredictability
  - Multiple OTP generation modes with varying complexity
  - GUI interface built with Tkinter
- **Files**:
  - `project.py` - Main application with OTP generation logic
  - `test_project.py` - Test suite for the OTP generator
  - `requirements.txt` - Dependencies for the project

### [Network-Monitoring-Tool](./Network-Monitoring-Tool/)
- **Description**: Python-based tool for monitoring network traffic and detecting security threats.
- **Features**:
  - Real-time packet capture using Scapy
  - Detection of SYN flood attacks and port scanning
  - Threat intelligence integration
  - Automatic IP blocking via Windows Firewall or Linux iptables
  - Cross-platform support
- **Files**:
  - `network_Monitoring_Tool.py` - Main tool implementation
  - `requirements.txt` - Dependencies including Scapy

### [Fibonacci-numbers](./Fibonacci-numbers/)
- **Description**: Implementation of OTP and cipher algorithms using Fibonacci sequences.
- **Features**:
  - Fibonacci-based cipher for text encryption
  - OTP generation using Fibonacci numbers
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
- **Files**:
  - `Server connection monitoring.ipynb` - Jupyter notebook with implementation

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
- **Libraries**: Scapy, Tkinter, Flask, base64, cryptography
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