#!/usr/bin/env python3
"""
WMI Class Fix Utility
Specifically fixes missing WMI classes like Win32_BaseBoard, Win32_BIOS, etc.
"""

import subprocess
import os
import sys
import ctypes
import time

def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_command(command, description, timeout=60):
    """Run a command and return success status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ {description} - TIMEOUT ({timeout}s)")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def test_wmi_classes():
    """Test if WMI classes are available"""
    print("\n🔍 Testing WMI Classes...")
    
    try:
        import wmi
        conn = wmi.WMI()
        
        classes_to_test = [
            'Win32_ComputerSystem',
            'Win32_BaseBoard', 
            'Win32_BIOS',
            'Win32_DiskDrive',
            'Win32_Processor',
            'Win32_PhysicalMemory',
            'Win32_VideoController',
            'Win32_OperatingSystem'
        ]
        
        working_classes = []
        failed_classes = []
        
        for class_name in classes_to_test:
            try:
                if hasattr(conn, class_name):
                    wmi_class = getattr(conn, class_name)
                    result = list(wmi_class())
                    working_classes.append(class_name)
                    print(f"   ✅ {class_name} - {len(result)} items")
                else:
                    failed_classes.append(class_name)
                    print(f"   ❌ {class_name} - Not found")
            except Exception as e:
                failed_classes.append(class_name)
                print(f"   ❌ {class_name} - Error: {e}")
        
        print(f"\n📊 Results: {len(working_classes)}/{len(classes_to_test)} classes working")
        
        if failed_classes:
            print(f"❌ Failed classes: {', '.join(failed_classes)}")
            return False
        else:
            print("✅ All WMI classes are working!")
            return True
            
    except ImportError:
        print("❌ WMI module not available")
        return False
    except Exception as e:
        print(f"❌ WMI test failed: {e}")
        return False

def stop_wmi_service():
    """Stop WMI service and dependent services"""
    print("\n🛑 Stopping WMI Services...")
    
    services_to_stop = [
        'winmgmt',
        'wmiApSrv',
        'iphlpsvc'
    ]
    
    for service in services_to_stop:
        run_command(f'net stop {service} /y', f'Stopping {service} service')
        time.sleep(1)

def start_wmi_service():
    """Start WMI service"""
    print("\n🚀 Starting WMI Services...")
    
    services_to_start = [
        'winmgmt',
        'wmiApSrv'
    ]
    
    for service in services_to_start:
        run_command(f'net start {service}', f'Starting {service} service')
        time.sleep(2)

def rebuild_wmi_repository():
    """Rebuild WMI repository"""
    print("\n🔨 Rebuilding WMI Repository...")
    
    # Stop WMI first
    stop_wmi_service()
    time.sleep(3)
    
    # Rebuild repository
    success = run_command('winmgmt /resetrepository', 'Rebuilding WMI Repository', timeout=120)
    
    if success:
        print("✅ WMI Repository rebuilt successfully")
        time.sleep(5)
        
        # Start WMI service
        start_wmi_service()
        return True
    else:
        print("❌ Failed to rebuild WMI Repository")
        return False

def register_wmi_providers():
    """Re-register WMI providers"""
    print("\n📝 Re-registering WMI Providers...")
    
    # Re-register core WMI providers
    providers = [
        r'%windir%\system32\wbem\cimwin32.dll',
        r'%windir%\system32\wbem\wbemcore.dll',
        r'%windir%\system32\wbem\wmiutils.dll',
        r'%windir%\system32\wbem\wbemprox.dll'
    ]
    
    success_count = 0
    for provider in providers:
        if run_command(f'regsvr32 /s {provider}', f'Registering {os.path.basename(provider)}'):
            success_count += 1
    
    print(f"📊 Registered {success_count}/{len(providers)} providers")
    return success_count > 0

def recompile_wmi_mof():
    """Recompile WMI MOF files"""
    print("\n🔄 Recompiling WMI MOF Files...")
    
    # Key MOF files that define hardware classes
    mof_files = [
        r'%windir%\system32\wbem\cimwin32.mof',
        r'%windir%\system32\wbem\cimwin32.mfl'
    ]
    
    success_count = 0
    for mof_file in mof_files:
        if run_command(f'mofcomp {mof_file}', f'Compiling {os.path.basename(mof_file)}'):
            success_count += 1
    
    print(f"📊 Compiled {success_count}/{len(mof_files)} MOF files")
    return success_count > 0

def main():
    """Main repair function"""
    print("WMI CLASS REPAIR UTILITY")
    print("=" * 50)
    print("Fixes missing WMI classes like Win32_BaseBoard, Win32_BIOS, etc.")
    print("=" * 50)
    
    if not is_admin():
        print("❌ This utility requires administrator privileges")
        print("Right-click and select 'Run as administrator'")
        input("\nPress Enter to exit...")
        return
    
    print("✅ Running with administrator privileges")
    
    # Test current state
    print("\n📊 Testing current WMI state...")
    if test_wmi_classes():
        print("\n✅ All WMI classes are already working!")
        print("If you're still seeing errors, they may be application-specific.")
        input("\nPress Enter to exit...")
        return
    
    print("\n🛠️ WMI classes are missing. Starting repair process...")
    
    # Repair sequence
    repair_steps = [
        ("Re-register WMI Providers", register_wmi_providers),
        ("Recompile MOF Files", recompile_wmi_mof),
        ("Restart WMI Service", lambda: (stop_wmi_service(), time.sleep(3), start_wmi_service())[2])
    ]
    
    for step_name, step_function in repair_steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        try:
            success = step_function()
            if success:
                print(f"✅ {step_name} completed")
                
                # Test after each step
                time.sleep(3)
                print("Testing WMI classes...")
                if test_wmi_classes():
                    print("\n🎉 WMI CLASSES FIXED!")
                    print("All hardware detection should now work properly.")
                    input("\nPress Enter to exit...")
                    return
            else:
                print(f"❌ {step_name} failed")
        except Exception as e:
            print(f"❌ {step_name} error: {e}")
    
    # Last resort - full repository rebuild
    print("\n⚠️ Standard repairs failed. Trying repository rebuild...")
    print("This will require a system restart.")
    
    response = input("\nProceed with WMI repository rebuild? (y/N): ").lower().strip()
    if response == 'y':
        if rebuild_wmi_repository():
            print("\n✅ WMI Repository rebuilt successfully")
            print("🔄 SYSTEM RESTART REQUIRED")
            
            restart = input("\nRestart computer now? (y/N): ").lower().strip()
            if restart == 'y':
                print("Restarting in 10 seconds...")
                subprocess.run(['shutdown', '/r', '/t', '10'], shell=True)
                return
        else:
            print("❌ Repository rebuild failed")
    
    print("\n📋 MANUAL STEPS TO TRY:")
    print("1. Restart your computer")
    print("2. Run Windows Update")
    print("3. Run 'sfc /scannow' as administrator")
    print("4. Check Windows Event Viewer for WMI errors")
    print("5. Consider system restore if issue started recently")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nRepair interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        input("Press Enter to exit...")
