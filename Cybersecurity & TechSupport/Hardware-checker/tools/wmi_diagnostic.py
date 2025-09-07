#!/usr/bin/env python3
"""
WMI Diagnostic Tool for PC Hardware Checker
Helps identify and resolve WMI connection issues
"""

import sys
import os
import subprocess
import platform

def check_wmi_service():
    """Check if WMI service is running"""
    print("🔍 Checking WMI Service Status...")
    try:
        # Check WMI service status
        result = subprocess.run(['sc', 'query', 'winmgmt'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            if "RUNNING" in result.stdout:
                print("✅ WMI Service (winmgmt) is running")
                return True
            else:
                print("❌ WMI Service (winmgmt) is not running")
                print("   Output:", result.stdout)
                return False
        else:
            print("❌ Could not check WMI service status")
            return False
    except Exception as e:
        print(f"❌ Error checking WMI service: {e}")
        return False

def test_wmi_connection():
    """Test WMI connection methods"""
    print("\n🔍 Testing WMI Connection Methods...")
    
    try:
        import wmi
    except ImportError:
        print("❌ WMI module not installed")
        print("   Run: pip install WMI")
        return False
    
    connection_methods = [
        ("Standard WMI()", lambda: wmi.WMI()),
        ("WMI with namespace", lambda: wmi.WMI(namespace="root\\cimv2")),
        ("WMI with empty credentials", lambda: wmi.WMI(namespace="root\\cimv2", user="", password="")),
    ]
    
    working_methods = []
    
    for name, method in connection_methods:
        try:
            print(f"   Testing {name}...")
            conn = method()
            # Test the connection
            list(conn.Win32_ComputerSystem())
            print(f"   ✅ {name} - SUCCESS")
            working_methods.append(name)
        except Exception as e:
            print(f"   ❌ {name} - FAILED: {e}")
    
    return working_methods

def test_wmi_classes():
    """Test specific WMI classes"""
    print("\n🔍 Testing WMI Classes...")
    
    try:
        import wmi
        conn = wmi.WMI()
    except Exception as e:
        print(f"❌ Cannot create WMI connection: {e}")
        return
    
    wmi_classes = [
        ("Win32_ComputerSystem", "System Information"),
        ("Win32_BaseBoard", "Motherboard Information"),
        ("Win32_BIOS", "BIOS Information"),
        ("Win32_Processor", "CPU Information"),
        ("Win32_PhysicalMemory", "Memory Information"),
        ("Win32_DiskDrive", "Disk Information"),
        ("Win32_VideoController", "Graphics Information"),
        ("Win32_OperatingSystem", "OS Information"),
    ]
    
    for class_name, description in wmi_classes:
        try:
            print(f"   Testing {class_name} ({description})...")
            items = list(getattr(conn, class_name)())
            print(f"   ✅ {class_name} - Found {len(items)} items")
        except Exception as e:
            print(f"   ❌ {class_name} - FAILED: {e}")

def check_permissions():
    """Check if running with appropriate permissions"""
    print("\n🔍 Checking Permissions...")
    
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if is_admin:
            print("✅ Running with administrator privileges")
        else:
            print("⚠️ Not running with administrator privileges")
            print("   Some WMI features may be limited")
        return is_admin
    except Exception as e:
        print(f"❌ Could not check admin status: {e}")
        return False

def suggest_fixes():
    """Suggest potential fixes for WMI issues"""
    print("\n🛠️ POTENTIAL FIXES FOR WMI ISSUES:")
    print("="*50)
    
    print("\n1. RESTART WMI SERVICE:")
    print("   Open Command Prompt as Administrator and run:")
    print("   net stop winmgmt")
    print("   net start winmgmt")
    
    print("\n2. REBUILD WMI REPOSITORY:")
    print("   Open Command Prompt as Administrator and run:")
    print("   winmgmt /resetrepository")
    print("   (This will restart your computer)")
    
    print("\n3. CHECK WINDOWS SERVICES:")
    print("   - Press Win+R, type 'services.msc'")
    print("   - Find 'Windows Management Instrumentation'")
    print("   - Make sure it's set to 'Automatic' and 'Running'")
    
    print("\n4. RUN AS ADMINISTRATOR:")
    print("   - Right-click the application")
    print("   - Select 'Run as administrator'")
    
    print("\n5. CHECK FIREWALL/ANTIVIRUS:")
    print("   - Temporarily disable firewall/antivirus")
    print("   - Test if WMI works")
    print("   - Add exceptions if needed")
    
    print("\n6. SYSTEM FILE CHECK:")
    print("   Open Command Prompt as Administrator and run:")
    print("   sfc /scannow")
    
    print("\n7. WINDOWS UPDATE:")
    print("   - Install all pending Windows updates")
    print("   - Restart computer")

def test_registry_access():
    """Test registry access for alternative detection"""
    print("\n🔍 Testing Registry Access...")
    
    try:
        import winreg
        
        registry_keys = [
            (r"HARDWARE\DESCRIPTION\System\BIOS", "BIOS Information"),
            (r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "Windows Version"),
            (r"HARDWARE\DESCRIPTION\System\CentralProcessor\0", "CPU Information"),
        ]
        
        for key_path, description in registry_keys:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                    print(f"   ✅ {description} - Registry access OK")
            except Exception as e:
                print(f"   ❌ {description} - Registry access failed: {e}")
                
    except ImportError:
        print("❌ winreg module not available")

def main():
    """Main diagnostic function"""
    print("WMI DIAGNOSTIC TOOL")
    print("="*50)
    print("This tool helps diagnose WMI connection issues")
    print(f"Platform: {platform.platform()}")
    print(f"Python: {sys.version}")
    print("="*50)
    
    # Run all diagnostic tests
    wmi_service_ok = check_wmi_service()
    is_admin = check_permissions()
    working_methods = test_wmi_connection()
    test_wmi_classes()
    test_registry_access()
    
    # Summary
    print("\n📊 DIAGNOSTIC SUMMARY:")
    print("="*30)
    print(f"WMI Service Running: {'✅' if wmi_service_ok else '❌'}")
    print(f"Administrator Rights: {'✅' if is_admin else '⚠️'}")
    print(f"Working WMI Methods: {len(working_methods)}")
    
    if not working_methods:
        print("\n❌ NO WMI METHODS WORKING")
        print("WMI functionality is completely unavailable")
        suggest_fixes()
    elif len(working_methods) < 3:
        print("\n⚠️ LIMITED WMI FUNCTIONALITY")
        print("Some WMI methods are working but not all")
        suggest_fixes()
    else:
        print("\n✅ WMI APPEARS TO BE WORKING")
        print("If you're still having issues, try running as administrator")
    
    print("\n" + "="*50)
    print("Diagnostic complete!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnostic interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error during diagnosis: {e}")
    
    input("\nPress Enter to exit...")
