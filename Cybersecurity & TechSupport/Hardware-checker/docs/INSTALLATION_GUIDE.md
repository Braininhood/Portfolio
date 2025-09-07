# PC Hardware Checker - Installation Guide

## 🚀 **Quick Installation (Recommended)**

### **Option 1: Essential Installation (Most Reliable)**
```bash
# Double-click this file for basic functionality
install_essential.bat
```
- ✅ Works with all Python versions
- ✅ Core hardware detection
- ✅ Basic system monitoring
- ✅ Windows compatibility guaranteed

### **Option 2: Simple Stress Testing**
```bash
# After essential installation, add stress testing
install_stress_simple.bat
```
- ✅ Essential stress testing features
- ✅ Avoids problematic packages
- ✅ Maximum compatibility
- ✅ Works with Python 3.13+

### **Option 3: Full Installation (Advanced)**
```bash
# For advanced users with compatible systems
install_stress_testing.bat
```
- ⚠️ May have compatibility issues with newer Python
- ✅ Complete feature set if successful
- ⚠️ Requires troubleshooting if packages fail

## 📋 **Installation Requirements**

### **System Requirements:**
- **Windows**: 7, 8, 10, or 11 (32-bit or 64-bit)
- **Python**: 3.7 or newer (3.10-3.12 recommended)
- **Memory**: 2GB RAM minimum
- **Storage**: 500MB free space
- **Internet**: Required for package installation

### **Python Installation:**
1. Download from [python.org](https://python.org)
2. ✅ **IMPORTANT**: Check "Add Python to PATH" during installation
3. Restart computer after installation
4. Test: Open Command Prompt and type `python --version`

## 🔧 **Manual Installation**

### **Core Requirements (Essential):**
```bash
pip install psutil wmi pywin32 GPUtil --user
```

### **Stress Testing (Optional):**
```bash
pip install numpy py-cpuinfo --user
```

### **Advanced Features (Optional):**
```bash
pip install scipy memory-profiler pympler --user
```

## 🚨 **Common Installation Issues**

### **Issue 1: Pillow Build Error (Python 3.13)**
**Symptom**: `KeyError: '__version__'` during Pillow installation
**Solution**: 
- Use `install_essential.bat` (doesn't include Pillow)
- Or manually: `pip install pillow --upgrade --user`

### **Issue 2: "Python not found"**
**Symptom**: `'python' is not recognized as internal or external command`
**Solutions**:
1. Reinstall Python with "Add to PATH" checked
2. Use `py` instead of `python`: `py --version`
3. Add Python to PATH manually

### **Issue 3: Permission Errors**
**Symptom**: `Permission denied` or `Access denied`
**Solutions**:
1. Add `--user` flag: `pip install package --user`
2. Run Command Prompt as Administrator
3. Use virtual environment

### **Issue 4: Package Build Failures**
**Symptom**: `Failed building wheel` or `Microsoft Visual C++ required`
**Solutions**:
1. Use pre-compiled packages: `pip install package --only-binary=all`
2. Install Visual Studio Build Tools
3. Use alternative packages or skip optional features

### **Issue 5: WMI Errors**
**Symptom**: `winmgmts:` or COM errors
**Solutions**:
1. Run as Administrator
2. Use `debug_wmi.bat` to diagnose
3. Use `repair_wmi.bat` to fix WMI service

## ✅ **Verification Steps**

### **Test Basic Installation:**
```bash
python src/main.py
```
- Should open GUI without errors
- Hardware detection should work
- No stress testing tab = OK (install stress testing separately)

### **Test Stress Testing:**
```bash
python -c "import sys; sys.path.append('src'); from hardware_stress_tester import HardwareStressTester; print('Stress testing ready')"
```
- Should print "Stress testing ready"
- If error: stress testing libraries not installed

### **Test Complete System:**
1. Run `run_admin_simple.bat`
2. Click each navigation button
3. Check "🔥 Stress Tests" tab (if available)
4. Try exporting a report

## 🎯 **Installation Recommendations**

### **For Regular Users:**
1. Start with `install_essential.bat`
2. Test the application
3. Add `install_stress_simple.bat` if needed

### **For Technical Users:**
1. Try `install_stress_testing.bat` first
2. If issues, fall back to `install_essential.bat`
3. Manually install specific packages as needed

### **For Developers:**
1. Use virtual environment: `python -m venv venv`
2. Activate: `venv\Scripts\activate`
3. Install: `pip install -r requirements.txt`
4. Test: `python src/main.py`

## 📞 **Getting Help**

### **If Installation Fails:**
1. Check error messages carefully
2. Try the simpler installation option
3. Verify Python installation
4. Check internet connection
5. Run as Administrator

### **What Works Without Stress Testing:**
- ✅ Complete hardware detection
- ✅ System monitoring
- ✅ GPU information
- ✅ Network details
- ✅ Export functionality
- ✅ All basic features

### **What Requires Stress Testing Libraries:**
- 🔥 CPU stress testing
- 🔥 Memory stress testing
- 🔥 Disk performance testing
- 🔥 Real-time monitoring during tests
- 🔥 Performance benchmarking

The PC Hardware Checker is designed to work reliably even without all optional packages installed! 🚀
