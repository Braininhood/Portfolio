# System Information Collector

A cross-platform Python script that collects and reports detailed system information for Windows and Linux systems.

## Features

- **System Information**: OS details, version, machine type
- **Hardware Information**: CPU, memory, disk, GPU details
- **Network Information**: Network interfaces, IP addresses, hardware details
- **Software Information**: Installed software (Windows and Linux)
- **Browser Information**: Installed browsers with version and user-agent details
- **Security Information**: Antivirus and firewall status

## Requirements

- Python 3.6+
- Required packages are listed in `requirements.txt`

## Installation

1. Clone or download this repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the script:
```
python system_info.py
```

The script will collect system information and save it to `system_info_log.txt` in the same directory.

## Supported Platforms

- Windows: Full support for all features
- Linux: Support for Debian-based (using dpkg) and RPM-based (using rpm) distributions
  
## Output Format

The script generates a text file with sections for:
- System Information
- Hardware Information
- GPU Information
- User Information
- Antivirus Information
- Firewall Information
- Network Information
- Network Hardware Information
- Installed Software
- Installed Browsers 