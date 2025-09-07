# PC Hardware Checker - Launcher Guide

## 🚀 How to Start the Application

The PC Hardware Checker includes multiple launcher options to ensure it works on your system:

### 📊 **RECOMMENDED: run_admin_simple.bat**
```
✅ Best choice for most users
✅ Enhanced hardware detection
✅ Automatic directory detection
✅ Clear error messages with solutions
✅ Works with or without admin rights
```
**Usage**: Simply double-click this file. If you want maximum hardware detection, right-click and select "Run as administrator".

### 🔧 **STANDARD: run.bat**
```
✅ Standard hardware detection
✅ No administrator privileges required
✅ Good for basic system checking
✅ Fastest startup
```
**Usage**: Double-click to run in standard mode.

### 🛡️ **ADVANCED: run_as_admin.bat**
```
✅ Automatically requests administrator rights
✅ Maximum hardware detection capabilities
✅ Full WMI access for detailed information
✅ Best for complete system analysis
```
**Usage**: Double-click and click "Yes" when Windows asks for permission.

## 🔧 **Installation Options**

### 📦 **launchers\install.bat**
```
✅ Automatic installation of all requirements
✅ Checks Python installation
✅ Installs required packages
✅ Tests the installation
```
**Usage**: Run this first if you haven't installed Python or the required packages.

## 🐛 **Troubleshooting the Directory Issue**

The error you encountered was caused by the batch file running from the wrong directory. This has been fixed in the updated versions:

### **What was wrong:**
- The administrator batch file was starting from `C:\Windows\System32\` instead of the application folder
- It couldn't find `main.py` because it was looking in the wrong place

### **What's fixed:**
- Added `cd /d "%~dp0"` to ensure the script runs from its own directory
- Added directory verification and error checking
- Improved PowerShell command for admin restart
- Added alternative launchers that don't require PowerShell

## 🎯 **Quick Start Instructions**

1. **First Time Setup:**
   ```
   1. Double-click "launchers\install.bat"
   2. Wait for installation to complete
   ```

2. **Running the Application:**
   ```
   BEST: Double-click "run_admin_simple.bat"
   OR:   Double-click "run.bat"
   ```

3. **If You Need Maximum Detection:**
   ```
   Right-click "run_admin_simple.bat" → "Run as administrator"
   ```

## 📋 **What Each Launcher Does**

| Launcher | Admin Rights | Hardware Detection | Complexity |
|----------|-------------|-------------------|------------|
| `run.bat` | Optional | Standard | Simple |
| `run_admin_simple.bat` | Optional | Enhanced | Simple |
| `run_as_admin.bat` | Automatic | Maximum | Advanced |

## ✅ **Recommended Workflow**

1. Start with `run_admin_simple.bat`
2. If you see limited information, right-click it and "Run as administrator"
3. If you have issues, try `run.bat` for basic functionality
4. Check the built-in help system for specific component troubleshooting

All launchers now include proper directory handling and should work correctly from any location!
