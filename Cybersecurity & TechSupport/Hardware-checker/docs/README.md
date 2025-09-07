# PC Hardware Checker Professional

An enterprise-grade hardware diagnostic application that provides comprehensive analysis of your computer's components. This professional tool combines detailed hardware information with advanced stress testing capabilities, comparable to AIDA64 and other professional benchmarking suites.

## 🚀 Main Features

### 📊 HARDWARE INFORMATION & MONITORING
- 🖥️ **Complete System Overview** - Computer specifications, Windows details, and system information
- 🧠 **Processor (CPU) Analysis** - Detailed CPU information, real-time monitoring, and thermal analysis
- 💾 **Memory (RAM) Information** - RAM capacity, usage statistics, module details, and performance metrics
- 💿 **Storage Drive Analysis** - Drive specifications, performance metrics, partition analysis, and health status
- 🎮 **Graphics (GPU) Information** - Graphics card details, utilization monitoring, and video memory usage
- 🌐 **Network Configuration** - Network interfaces, performance statistics, IPv4/IPv6 configuration, and MAC addresses
- 🔧 **Motherboard & BIOS** - Motherboard specifications, BIOS information, and hardware compatibility analysis

### 🔥 PROFESSIONAL STRESS TESTING SUITE
- 🔄 **Comprehensive System Test** - Complete multi-component stress testing with system-wide analysis
- ⚡ **CPU Benchmark & Stability** - Multi-threaded computational stress testing with performance scoring
- 💾 **Memory Performance & Stability** - RAM speed testing, error checking, and stability analysis
- 💿 **Storage Performance Test** - Disk I/O speed testing, latency analysis, and reliability testing
- 🎮 **GPU Performance Test** - Graphics processing stress testing with thermal analysis
- 🌐 **Network Performance Test** - Bandwidth testing, latency analysis, and connectivity evaluation
- 🔧 **Hardware Compatibility Test** - Component compatibility verification and system stability testing
- 🌡️ **Thermal Stress Test** - Advanced temperature monitoring and thermal efficiency analysis

### 📈 REAL-TIME MONITORING & VISUALIZATION
- 📊 **Professional Charts & Graphs** - Live CPU, Memory, Disk I/O, and Network performance visualization
- 🌡️ **Temperature Monitoring** - Multi-sensor temperature tracking with thermal analysis and safety alerts
- ⚡ **Performance Metrics** - Real-time statistics with professional formatting and color-coded alerts
- 📈 **Historical Data** - Performance tracking with trend analysis and bottleneck identification

### 💾 PROFESSIONAL REPORTING & EXPORT
- 📄 **TXT Format Reports** - Human-readable detailed analysis reports with complete methodology
- 📊 **JSON Format Data** - Structured technical data for advanced analysis and integration
- 🏆 **AIDA64-Style Analysis** - Professional performance scoring, stability ratings, and expert recommendations
- 📋 **Comprehensive Documentation** - Complete test results, hardware specifications, and optimization advice

## User-Friendly Design

- **Simple Interface** - Clean, modern GUI with clear navigation
- **Non-Technical Explanations** - All technical terms explained in simple language
- **Visual Indicators** - Emojis and clear labeling for easy understanding
- **Help System** - Built-in help guide for all features
- **Export Functionality** - Save reports for future reference or technical support

## Compatibility

Works with all Windows versions:
- Windows 7
- Windows 8/8.1
- Windows 10
- Windows 11

Compatible with both 32-bit and 64-bit systems.

## Hardware Stress Testing

The PC Hardware Checker includes advanced stress testing capabilities to evaluate your system's performance and stability:

### Test Types:
- **🔥 Comprehensive Test** - Tests all components simultaneously
- **🧠 CPU Stress Test** - Multi-threaded processor stress testing
- **💾 Memory Stress Test** - RAM allocation and stability testing
- **💿 Disk Performance Test** - Storage read/write performance testing
- **🎮 GPU Stress Test** - Graphics card load testing

### Safety Features:
- Real-time temperature monitoring
- Automatic safety checks
- User-controlled test stopping
- Progressive test intensity options

### To Enable Stress Testing:
1. Run `install_stress_testing.bat` to install additional libraries
2. Restart the application
3. Access via the "🔥 Stress Tests" tab

**Note**: Stress testing puts significant load on your hardware. Always monitor temperatures and stop tests if your system becomes unstable.

## Installation

1. **Install Python** (if not already installed):
   - Download Python 3.7+ from [python.org](https://python.org)
   - Make sure to check "Add Python to PATH" during installation

2. **Install Required Packages**:
   ```
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```
   python main.py
   ```

## Quick Start

1. Launch the application by running `python main.py`
2. The welcome screen will explain all available features
3. Click any category in the left menu to view detailed information
4. Use "Refresh Data" to update all information
5. Use "Save Report" to export information to a file
6. Click "Help" for detailed usage instructions

## What Information is Provided?

### System Overview
- Computer name and Windows edition
- System architecture (32-bit/64-bit)
- System uptime and current user
- Installation and boot information

### Processor (CPU)
- CPU model, manufacturer, and specifications
- Number of physical and logical cores
- Current and maximum frequencies
- Real-time CPU usage per core
- Cache information and socket type

### Memory (RAM)
- Total, used, and available memory
- Memory usage percentage
- Individual memory module details
- Memory speed and manufacturer information
- Virtual memory (swap) usage

### Storage Drives
- All connected drives (hard drives, SSDs, USB drives)
- Drive capacity, used space, and free space
- File system types (NTFS, FAT32, etc.)
- Physical disk information and interface types
- Disk I/O statistics

### Graphics (GPU)
- Graphics card model and manufacturer
- Video memory capacity and usage
- Current GPU load and temperature
- Driver version and status
- Support for multiple graphics cards

### Network Information
- All network interfaces (Ethernet, WiFi, etc.)
- IP addresses and network configuration
- Network usage statistics
- Hostname and network connectivity

### Motherboard
- Motherboard manufacturer and model
- BIOS version and date
- Serial numbers and version information

## Export Features

The application can export complete hardware reports in two formats:

- **Text File (.txt)** - Human-readable format with explanations
- **JSON File (.json)** - Structured data format for technical analysis

Reports include:
- Timestamp of when the report was generated
- All detected hardware information
- Organized sections for easy reading

## Troubleshooting

### Common Issues

**"Unknown" Information Displayed:**
- Some information may show as "Unknown" if the system cannot detect specific hardware details
- This is normal for some older systems or certain hardware configurations
- Try running as administrator for more detailed information

**Application Won't Start:**
- Ensure Python 3.7+ is installed
- Install all required packages: `pip install -r requirements.txt`
- Check if all required DLL files are available (especially on older Windows versions)

**Missing Hardware Information:**
- Some features require Windows Management Instrumentation (WMI)
- Ensure WMI service is running
- Some information may require administrator privileges

### Getting More Information

- Use the "Refresh Data" button to reload all information
- Check the help system built into the application
- Export a report and share it with technical support if needed

## Technical Details

### Dependencies
- **psutil** - Cross-platform system and process utilities
- **wmi** - Windows Management Instrumentation for detailed hardware info
- **GPUtil** - GPU monitoring and information
- **tkinter** - GUI framework (included with Python)

### Architecture
- Modular design with separate hardware detection and GUI components
- Threaded operations to prevent GUI freezing during data collection
- Error handling for different Windows versions and hardware configurations
- Graceful fallbacks when advanced features are not available

### Security
- No network connections required
- No data collection or transmission
- All information stays on your local computer
- Safe to use on corporate or secure systems

## License

This project is open source and available under the MIT License.

## Support

For technical support or questions:
1. Check the built-in help system
2. Review this README file
3. Export a hardware report to share with technical support
4. Ensure you're running the latest version

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests to improve the application.
