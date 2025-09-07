#!/usr/bin/env python3
"""
WMI Repair Utility for PC Hardware Checker
Attempts to fix common WMI issues automatically
"""

import os
import sys
import subprocess
import ctypes
import time

def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_command(command, description):
    """Run a command and return result"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def check_wmi_service():
    """Check and restart WMI service if needed"""
    print("\n🔍 Checking WMI Service...")
    
    # Check service status
    result = subprocess.run(['sc', 'query', 'winmgmt'], capture_output=True, text=True, shell=True)
    if "RUNNING" not in result.stdout:
        print("WMI Service is not running. Attempting to start...")
        if run_command('net start winmgmt', 'Starting WMI Service'):
            time.sleep(3)
            return True
        return False
    else:
        print("✅ WMI Service is running")
        return True

def repair_wmi_repository():
    """Repair WMI repository (requires restart)"""
    print("\n⚠️ WMI Repository Repair")
    print("This will reset the WMI repository and require a restart.")
    
    response = input("\nDo you want to proceed? (y/N): ").lower().strip()
    if response == 'y':
        print("\n🔧 Resetting WMI Repository...")
        if run_command('winmgmt /resetrepository', 'WMI Repository Reset'):
            print("\n✅ WMI Repository reset successfully")
            print("⚠️ COMPUTER RESTART REQUIRED")
            restart = input("\nRestart now? (y/N): ").lower().strip()
            if restart == 'y':
                subprocess.run(['shutdown', '/r', '/t', '10'], shell=True)
                print("Computer will restart in 10 seconds...")
            return True
        return False
    return False

def restart_wmi_service():
    """Restart WMI service"""
    print("\n🔧 Restarting WMI Service...")
    
    commands = [
        ('net stop winmgmt /y', 'Stopping WMI Service'),
        ('net start winmgmt', 'Starting WMI Service')
    ]
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
            break
        time.sleep(2)
    
    return success

def clear_wmi_cache():
    """Clear WMI repository cache"""
    print("\n🔧 Clearing WMI Cache...")
    
    cache_locations = [
        r'C:\Windows\System32\wbem\Repository',
        r'C:\Windows\System32\wbem\AutoRecover'
    ]
    
    success = True
    for location in cache_locations:
        if os.path.exists(location):
            try:
                # Stop WMI first
                subprocess.run(['net', 'stop', 'winmgmt', '/y'], capture_output=True, shell=True)
                time.sleep(2)
                
                # Clear cache files
                for root, dirs, files in os.walk(location):
                    for file in files:
                        try:
                            os.remove(os.path.join(root, file))
                        except:
                            pass
                
                print(f"✅ Cleared cache: {location}")
            except Exception as e:
                print(f"❌ Failed to clear cache: {location} - {e}")
                success = False
    
    # Restart WMI
    time.sleep(2)
    subprocess.run(['net', 'start', 'winmgmt'], capture_output=True, shell=True)
    return success

def register_wmi_dlls():
    """Re-register WMI DLLs"""
    print("\n🔧 Re-registering WMI DLLs...")
    
    dlls = [
        'wmiprvsd.dll',
        'wmiprvse.exe', 
        'wmidcprv.dll',
        'wmiutils.dll',
        'wbemcore.dll',
        'wbemess.dll',
        'wbemprox.dll'
    ]
    
    success_count = 0
    for dll in dlls:
        if run_command(f'regsvr32 /s {dll}', f'Registering {dll}'):
            success_count += 1
    
    print(f"\n📊 Successfully registered {success_count}/{len(dlls)} DLLs")
    return success_count > len(dlls) / 2

def test_wmi_functionality():
    """Test WMI functionality after repairs"""
    print("\n🔍 Testing WMI Functionality...")
    
    try:
        from hardware_detector import HardwareDetector
        hd = HardwareDetector()
        
        # Test motherboard detection
        mb_info = hd.get_motherboard_info()
        
        # Count successful detections
        success_count = 0
        total_count = 0
        
        for key, value in mb_info.items():
            total_count += 1
            if not key.endswith("Error") and "Error" not in str(value):
                success_count += 1
        
        print(f"📊 WMI Test Results: {success_count}/{total_count} items successful")
        
        if success_count > total_count / 2:
            print("✅ WMI appears to be working")
            return True
        else:
            print("❌ WMI still has issues")
            return False
            
    except Exception as e:
        print(f"❌ WMI test failed: {e}")
        return False

def main():
    """Main repair function"""
    print("WMI REPAIR UTILITY")
    print("=" * 50)
    print("This utility attempts to fix common WMI issues")
    print("=" * 50)
    
    if not is_admin():
        print("❌ This utility requires administrator privileges")
        print("Right-click and select 'Run as administrator'")
        input("\nPress Enter to exit...")
        return
    
    print("✅ Running with administrator privileges")
    
    # Test current WMI state
    print("\n📊 Testing current WMI state...")
    wmi_working = test_wmi_functionality()
    
    if wmi_working:
        print("\n✅ WMI appears to be working correctly")
        print("If you're still experiencing issues, they may be intermittent.")
        input("\nPress Enter to exit...")
        return
    
    print("\n🛠️ WMI issues detected. Starting repair process...")
    
    # Repair steps
    repair_steps = [
        ("Check WMI Service", check_wmi_service),
        ("Restart WMI Service", restart_wmi_service),
        ("Re-register WMI DLLs", register_wmi_dlls),
    ]
    
    for step_name, step_function in repair_steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        try:
            success = step_function()
            if success:
                print(f"✅ {step_name} completed successfully")
                
                # Test after each step
                print("Testing WMI functionality...")
                if test_wmi_functionality():
                    print("\n🎉 WMI REPAIR SUCCESSFUL!")
                    print("Hardware detection should now work properly.")
                    input("\nPress Enter to exit...")
                    return
            else:
                print(f"❌ {step_name} failed")
        except Exception as e:
            print(f"❌ {step_name} error: {e}")
    
    # If all else fails, offer repository reset
    print("\n⚠️ Standard repairs failed.")
    print("WMI Repository reset may be required (requires restart).")
    
    if repair_wmi_repository():
        print("\nWMI Repository reset initiated.")
    else:
        print("\n📋 MANUAL REPAIR SUGGESTIONS:")
        print("1. Restart your computer")
        print("2. Run Windows Update")
        print("3. Run 'sfc /scannow' as administrator")
        print("4. Consider system restore to before the issue started")
        print("5. Contact system administrator if in corporate environment")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nRepair interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        input("Press Enter to exit...")
