# PC Hardware Checker - Project Structure

## 📁 **Organized File Structure**

```
PC_Hardware_Checker/
├── 📄 run.bat                     # Main launcher (standard mode)
├── 📄 run_admin_simple.bat        # Enhanced launcher (recommended)
├── 📁 launchers/                  # Installation and startup scripts
├── 📄 install_stress_testing.bat  # Stress testing installation
├── 📄 debug_wmi.bat               # WMI diagnostic tool
├── 📄 repair_wmi.bat              # WMI repair utility
├── 📄 test_stress_testing.py      # Stress testing verification
├── 📄 requirements.txt            # Python dependencies
├── 📄 requirements_testing.txt    # Stress testing dependencies
├── 📄 PROJECT_STRUCTURE.md        # This file
│
├── 📂 src/                        # Python source code
│   ├── 📄 __init__.py             # Package initialization
│   ├── 📄 main.py                 # Main application entry point
│   ├── 📄 hardware_detector.py    # Core hardware detection logic
│   ├── 📄 gui_components.py       # GUI interface components
│   ├── 📄 hardware_stress_tester.py  # Hardware stress testing engine
│   └── 📄 stress_test_gui.py      # Stress testing GUI interface
│
├── 📂 docs/                       # Documentation files
│   ├── 📄 README.md               # Main documentation
│   ├── 📄 QUICK_START.txt         # Quick start guide
│   ├── 📄 THREADING_FIX_COMPLETE.md    # Threading fix documentation
│   ├── 📄 WMI_FIX_SUMMARY.md      # WMI issues and fixes
│   ├── 📄 COM_ERROR_FIX.md        # COM error resolution
│   ├── 📄 LAUNCHER_GUIDE.md       # Launcher usage guide
│   └── 📄 CHANGELOG.md            # Version history
│
├── 📂 tools/                      # Diagnostic and repair tools
│   ├── 📄 wmi_diagnostic.py       # WMI system diagnostic
│   ├── 📄 wmi_repair.py           # WMI service repair
│   └── 📄 fix_wmi_classes.py      # WMI class registration fix
│
└── 📂 launchers/                  # Original launcher files (archived)
    ├── 📄 run_as_admin.bat        # Advanced admin launcher
    ├── 📄 fix_wmi_classes.bat     # WMI class repair launcher
    └── (other original batch files)
```

## 🚀 **How to Use**

### **Quick Start:**
1. **Install**: Double-click `launchers\install.bat`
2. **Run**: Double-click `run_admin_simple.bat`

### **For Different Needs:**
- **Standard Mode**: `run.bat`
- **Enhanced Mode**: `run_admin_simple.bat` (recommended)
- **WMI Issues**: `debug_wmi.bat` → `repair_wmi.bat`
- **Manual Run**: `python src\main.py`

## 📋 **File Descriptions**

### **Root Level Launchers:**
- **`run_admin_simple.bat`** - Best option for most users, enhanced detection
- **`run.bat`** - Standard mode, basic hardware detection
- **`launchers\install.bat`** - Automatic Python package installation
- **`debug_wmi.bat`** - Diagnose WMI and threading issues
- **`repair_wmi.bat`** - Fix WMI service problems (requires admin)

### **Source Code (`src/`):**
- **`main.py`** - Application entry point and main GUI setup
- **`hardware_detector.py`** - Core hardware detection with WMI and fallbacks
- **`gui_components.py`** - Modern tkinter interface with user-friendly design
- **`__init__.py`** - Python package configuration

### **Documentation (`docs/`):**
- **`README.md`** - Complete project documentation
- **`QUICK_START.txt`** - Simple getting started guide
- **`*_FIX_*.md`** - Technical fix documentation for various issues
- **`CHANGELOG.md`** - Version history and changes

### **Tools (`tools/`):**
- **`wmi_diagnostic.py`** - Comprehensive WMI system testing
- **`wmi_repair.py`** - Automated WMI service repair and registry fixes
- **`fix_wmi_classes.py`** - Specific WMI class registration repair

### **Archived (`launchers/`):**
- Original batch files for reference
- Advanced launcher options
- Specialized repair utilities

## 🎯 **Benefits of This Structure**

### **User Benefits:**
- ✅ **Clean Root Directory** - Only essential files visible
- ✅ **Easy Access** - Main launchers in root for simple double-clicking
- ✅ **Clear Purpose** - Each file/folder has obvious function
- ✅ **Professional Layout** - Organized like commercial software

### **Developer Benefits:**
- ✅ **Modular Code** - Source separated from tools and docs
- ✅ **Maintainable** - Related files grouped together
- ✅ **Scalable** - Easy to add new tools or documentation
- ✅ **Version Control Friendly** - Clear separation of concerns

### **Troubleshooting Benefits:**
- ✅ **Diagnostic Tools** - Centralized in tools/ directory
- ✅ **Documentation** - All help files in docs/ directory
- ✅ **Step-by-step** - Clear progression from install → run → debug → repair

## 🔧 **Development Notes**

### **Adding New Features:**
- **Hardware Detection**: Add to `src/hardware_detector.py`
- **GUI Components**: Add to `src/gui_components.py`
- **Diagnostic Tools**: Add to `tools/` directory
- **Documentation**: Add to `docs/` directory

### **Creating New Launchers:**
- Place in root directory for user access
- Reference files using relative paths (e.g., `src\main.py`)
- Include proper error checking and user guidance

This structure makes the PC Hardware Checker professional, maintainable, and user-friendly! 🚀
