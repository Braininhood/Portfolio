# GDPR Compliance Checker

A comprehensive desktop application that scans websites for GDPR compliance issues, detects potential data privacy violations, and provides detailed remediation recommendations.

![GDPR Compliance Checker](https://img.shields.io/badge/GDPR-Compliance%20Checker-blue)

## Overview

The GDPR Compliance Checker is a powerful tool designed to help website owners and privacy professionals assess their compliance with the General Data Protection Regulation (GDPR). The application scans websites and analyzes key compliance areas, providing detailed reports and actionable recommendations to address any identified issues.

## Features

### Comprehensive Compliance Scanning
- **Cookie Consent Verification**: Checks for proper cookie banners, granular consent options, and cookie policies
- **Privacy Policy Analysis**: Verifies the presence and accessibility of privacy policies
- **Data Collection Forms Assessment**: Identifies consent mechanisms on data collection forms
- **Third-Party Services Detection**: Identifies third-party scripts and services that may process personal data
- **Data Subject Rights Verification**: Ensures websites inform users about their rights and how to exercise them
- **Legal Basis Analysis**: Checks if websites disclose the legal basis for data processing
- **International Data Transfer Detection**: Identifies information about cross-border data transfers
- **Security Measures Assessment**: Verifies HTTPS implementation and security information disclosure

### User-Friendly Interface
- Clean and intuitive GUI with multiple tabs for different types of information
- Real-time scanning progress updates
- Comprehensive summary and detailed views of findings

### Detailed Reporting
- Export findings to CSV or TXT formats
- Complete compliance assessment with reference to specific GDPR articles
- Actionable recommendations for addressing identified issues
- Comprehensive remediation guidelines tailored to each compliance area

## Requirements

- **Python 3.7+**
- **PyQt5**: For the GUI
- **Beautiful Soup 4**: For HTML parsing
- **Requests**: For HTTP requests
- **tldextract**: For domain extraction

## Installation

1. Clone this repository or download the source code.
2. Navigate to the project directory.
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

You can run the application in several ways:

1. Double-click the VBS launcher (recommended):
```
GDPR_Compliance_Checker.vbs
```
This launches the application without showing any command prompt window.

2. Run the batch file:
```
run_app.bat
```

3. Execute the Python script directly:
```bash
python app.py
```

### Scanning a Website

1. Enter the URL of the website you want to scan in the input field.
2. Click the "Scan" button to start the analysis.
3. Wait for the scan to complete (progress is shown in the progress bar).
4. Review the results in the Summary, Details, and Raw Data tabs.

### Understanding the Results

- **Summary Tab**: Provides an overview of compliance status with key findings and recommendations
- **Details Tab**: Shows a detailed breakdown of each compliance area with specific status and recommendations
- **Raw Data Tab**: Displays the raw scan data for technical analysis

### Generating Reports

1. After scanning a website, click the "Save Report" button.
2. Choose between CSV format (for data analysis) or TXT format (for comprehensive documentation).
3. Select a location to save the report.

## How It Works

The GDPR Compliance Checker uses sophisticated scanning technology to:

1. Send requests to websites that mimic browser behavior to bypass common blocking techniques
2. Parse the HTML content to identify elements related to GDPR compliance
3. Check for key indicators of compliance in various areas
4. Generate detailed findings based on the scan results
5. Provide recommendations based on GDPR requirements and best practices

## Key Compliance Areas

The application checks compliance in eight critical areas:

1. **Cookie Consent (GDPR Art. 6, ePrivacy Directive)**: Ensures websites obtain valid consent before using non-essential cookies
2. **Privacy Policy (GDPR Art. 12-14)**: Verifies the presence of a clear and accessible privacy policy
3. **Data Collection Forms (GDPR Art. 6-7)**: Ensures forms collect explicit consent when gathering personal data
4. **Third-Party Services (GDPR Art. 28)**: Identifies third-party data processors that require oversight
5. **Data Subject Rights (GDPR Art. 15-22)**: Checks if users are informed about their rights
6. **Legal Basis for Processing (GDPR Art. 6)**: Ensures transparency about the legal basis for data processing
7. **International Data Transfers (GDPR Art. 44-50)**: Verifies disclosure of cross-border data sharing
8. **Security Measures (GDPR Art. 32)**: Checks for implementation and disclosure of security protections

## Limitations

- The tool performs static analysis of website content only
- It cannot detect server-side processing activities
- Results should be considered as guidance and not as definitive legal assessment
- For comprehensive GDPR compliance assessment, consult with a legal professional

## Contributing

Contributions to improve the GDPR Compliance Checker are welcome. Please feel free to submit a pull request or open an issue to discuss potential improvements.

## License

This project is for educational and informational purposes only.

## Disclaimer

This tool is designed to help identify potential GDPR compliance issues but is not a substitute for professional legal advice. Use at your own risk and always consult with a qualified legal professional for definitive compliance guidance. 