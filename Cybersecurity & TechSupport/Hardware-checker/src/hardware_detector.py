"""
Hardware Detection Module
Detects and reports all PC hardware components
Compatible with different Windows versions
"""

import psutil
import platform
import subprocess
import json
import os
import sys
from datetime import datetime
import socket

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False


class HardwareDetector:
    def __init__(self):
        self.wmi_connection = None
        self.wmi_error = None
        self._initialize_wmi()
    
    def _initialize_wmi(self):
        """Initialize WMI connection with retry logic and COM threading support"""
        if not WMI_AVAILABLE:
            self.wmi_error = "WMI module not available"
            return
        
        # Initialize COM for threading support with proper apartment model
        try:
            import pythoncom
            # Use CoInitializeEx with COINIT_MULTITHREADED for better thread safety
            try:
                pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
                print("COM initialized with multithreaded apartment")
            except:
                # Fallback to standard initialization
                pythoncom.CoInitialize()
                print("COM initialized with standard apartment")
        except ImportError:
            print("pythoncom not available, proceeding without COM initialization")
        except Exception as e:
            print(f"COM initialization warning: {e}")
        
        # Try multiple connection methods with COM error handling
        connection_methods = [
            ("Standard", lambda: wmi.WMI()),
            ("Namespace", lambda: wmi.WMI(namespace="root\\cimv2")),
            ("Credentials", lambda: wmi.WMI(namespace="root\\cimv2", user="", password="")),
            ("Impersonation", lambda: wmi.WMI(namespace="root\\cimv2", 
                                            impersonation_level="impersonate")),
        ]
        
        for name, method in connection_methods:
            try:
                self.wmi_connection = method()
                # Test with a simple, reliable WMI class
                try:
                    list(self.wmi_connection.Win32_OperatingSystem())
                    print(f"WMI connection successful ({name})")
                    return
                except Exception as test_error:
                    print(f"WMI {name} connected but test failed: {test_error}")
                    # Connection works but some classes may fail
                    # Keep this connection for partial functionality
                    if self.wmi_connection is None:
                        self.wmi_connection = method()
                    continue
            except Exception as e:
                print(f"WMI {name} connection failed: {e}")
                continue
        
        if self.wmi_connection is None:
            self.wmi_error = "All WMI connection methods failed"
            print(f"WMI initialization failed: {self.wmi_error}")
        else:
            print("WMI connection established but with limited functionality")
    
    def _get_wmi_connection(self):
        """Get WMI connection with retry if needed"""
        if self.wmi_connection is None and self.wmi_error is None:
            self._initialize_wmi()
        return self.wmi_connection
    
    def _test_wmi_classes(self):
        """Test if required WMI classes are available"""
        wmi_conn = self._get_wmi_connection()
        if not wmi_conn:
            return False
        
        required_classes = ['Win32_ComputerSystem', 'Win32_BaseBoard', 'Win32_BIOS', 'Win32_DiskDrive']
        available_classes = []
        
        for class_name in required_classes:
            try:
                if hasattr(wmi_conn, class_name):
                    # Try to actually query the class
                    test_query = getattr(wmi_conn, class_name)
                    list(test_query())
                    available_classes.append(class_name)
                else:
                    print(f"WMI class {class_name} not available via hasattr")
            except Exception as e:
                print(f"WMI class {class_name} failed test: {e}")
        
        print(f"Available WMI classes: {available_classes} out of {required_classes}")
        return len(available_classes) > 0
    
    def _safe_wmi_query(self, wmi_class_name, max_retries=3):
        """Safely query WMI class with error handling and retries"""
        # Ensure COM is initialized for this thread with proper apartment model
        try:
            import pythoncom
            try:
                pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
            except:
                try:
                    pythoncom.CoInitialize()
                except:
                    pass  # Already initialized
        except ImportError:
            pass  # pythoncom not available
        
        for attempt in range(max_retries):
            wmi_conn = self._get_wmi_connection()
            if not wmi_conn:
                if attempt < max_retries - 1:
                    print(f"No WMI connection on attempt {attempt + 1}, retrying...")
                    self.wmi_connection = None
                    self._initialize_wmi()
                    continue
                return None, f"No WMI connection available after {max_retries} attempts"
            
            try:
                # For threaded environments, use fresh WMI connection first (most reliable)
                try:
                    import wmi
                    fresh_conn = wmi.WMI()
                    if hasattr(fresh_conn, wmi_class_name):
                        fresh_class = getattr(fresh_conn, wmi_class_name)
                        result = list(fresh_class())
                        return result, None
                except Exception as fresh_error:
                    # If fresh connection fails, try existing connection
                    pass
                
                # Try direct attribute access with existing connection
                if hasattr(wmi_conn, wmi_class_name):
                    try:
                        wmi_class = getattr(wmi_conn, wmi_class_name)
                        result = list(wmi_class())
                        return result, None
                    except Exception as direct_error:
                        # Thread marshalling error - try alternative methods
                        if "marshalled for a different thread" in str(direct_error):
                            pass  # Continue to alternative methods
                        else:
                            raise direct_error
                
                # Alternative access methods for thread marshalling issues
                # Method 1: WMI Query with existing connection
                try:
                    query = f"SELECT * FROM {wmi_class_name}"
                    result = list(wmi_conn.query(query))
                    return result, None
                except Exception as query_error:
                    pass  # Continue to next method
                
                # Method 2: Fresh connection with namespace
                try:
                    import wmi
                    alt_conn = wmi.WMI(namespace="root\\cimv2")
                    if hasattr(alt_conn, wmi_class_name):
                        alt_class = getattr(alt_conn, wmi_class_name)
                        result = list(alt_class())
                        return result, None
                except Exception as alt_error:
                    pass  # Continue to final method
                    
                return None, f"WMI class {wmi_class_name} not accessible in current thread context"
                    
            except AttributeError as e:
                error_msg = f"WMI class {wmi_class_name} not found: {str(e)}"
                print(f"AttributeError on attempt {attempt + 1}: {error_msg}")
                if attempt < max_retries - 1:
                    # Try to get a fresh WMI connection
                    self.wmi_connection = None
                    self._initialize_wmi()
                    continue
                return None, error_msg
                
            except Exception as e:
                error_msg = str(e)
                print(f"Error on attempt {attempt + 1} for {wmi_class_name}: {error_msg}")
                
                # Handle specific errors
                if "COM Error" in error_msg or "Exception occurred" in error_msg or "not found" in error_msg.lower():
                    if attempt < max_retries - 1:
                        print(f"Retrying with fresh connection...")
                        # Try to reinitialize WMI connection
                        try:
                            self.wmi_connection = None
                            self._initialize_wmi()
                        except Exception as init_error:
                            print(f"Failed to reinitialize WMI: {init_error}")
                        continue
                return None, f"WMI query failed: {error_msg}"
        
        return None, f"All {max_retries} attempts failed for {wmi_class_name}"
    
    def get_system_info(self):
        """Get basic system information"""
        try:
            info = {
                "Computer Name": platform.node(),
                "Operating System": platform.system(),
                "OS Release": platform.release(),
                "OS Version": platform.version(),
                "Architecture": platform.architecture()[0],
                "Processor": platform.processor(),
                "Python Version": platform.python_version(),
                "Current User": os.getlogin() if hasattr(os, 'getlogin') else "Unknown",
                "System Uptime": self._get_uptime(),
                "Current Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add Windows-specific info
            if platform.system() == "Windows":
                info.update(self._get_windows_info())
                
            return info
        except Exception as e:
            return {"Error": f"Could not retrieve system info: {str(e)}"}
    
    def get_cpu_info(self):
        """Get detailed CPU information"""
        try:
            info = {
                "Physical Cores": psutil.cpu_count(logical=False),
                "Logical Cores": psutil.cpu_count(logical=True),
                "Current Frequency": f"{psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else "Unknown",
                "Min Frequency": f"{psutil.cpu_freq().min:.2f} MHz" if psutil.cpu_freq() and psutil.cpu_freq().min else "Unknown",
                "Max Frequency": f"{psutil.cpu_freq().max:.2f} MHz" if psutil.cpu_freq() and psutil.cpu_freq().max else "Unknown",
                "CPU Usage": f"{psutil.cpu_percent(interval=1):.1f}%",
                "CPU Usage Per Core": [f"Core {i}: {usage:.1f}%" for i, usage in enumerate(psutil.cpu_percent(percpu=True, interval=1))]
            }
            
            # Add WMI CPU info if available
            if self.wmi_connection:
                try:
                    for cpu in self.wmi_connection.Win32_Processor():
                        info.update({
                            "CPU Name": cpu.Name,
                            "CPU Manufacturer": cpu.Manufacturer,
                            "CPU Family": cpu.Family,
                            "CPU Model": cpu.Model,
                            "CPU Stepping": cpu.Stepping,
                            "CPU Socket": cpu.SocketDesignation,
                            "CPU Cache L2": f"{cpu.L2CacheSize} KB" if cpu.L2CacheSize else "Unknown",
                            "CPU Cache L3": f"{cpu.L3CacheSize} KB" if cpu.L3CacheSize else "Unknown"
                        })
                        break  # Usually only one CPU
                except Exception:
                    pass
            
            return info
        except Exception as e:
            return {"Error": f"Could not retrieve CPU info: {str(e)}"}
    
    def get_memory_info(self):
        """Get detailed memory information"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            info = {
                "Total RAM": self._bytes_to_gb(memory.total),
                "Available RAM": self._bytes_to_gb(memory.available),
                "Used RAM": self._bytes_to_gb(memory.used),
                "RAM Usage": f"{memory.percent:.1f}%",
                "Total Swap": self._bytes_to_gb(swap.total),
                "Used Swap": self._bytes_to_gb(swap.used),
                "Free Swap": self._bytes_to_gb(swap.free),
                "Swap Usage": f"{swap.percent:.1f}%"
            }
            
            # Add WMI memory details if available
            if self.wmi_connection:
                try:
                    memory_modules = []
                    for memory_module in self.wmi_connection.Win32_PhysicalMemory():
                        module_info = {
                            "Capacity": self._bytes_to_gb(int(memory_module.Capacity)) if memory_module.Capacity else "Unknown",
                            "Speed": f"{memory_module.Speed} MHz" if memory_module.Speed else "Unknown",
                            "Manufacturer": memory_module.Manufacturer or "Unknown",
                            "Part Number": memory_module.PartNumber or "Unknown",
                            "Location": memory_module.DeviceLocator or "Unknown"
                        }
                        memory_modules.append(module_info)
                    
                    if memory_modules:
                        info["Memory Modules"] = memory_modules
                except Exception:
                    pass
            
            return info
        except Exception as e:
            return {"Error": f"Could not retrieve memory info: {str(e)}"}
    
    def get_disk_info(self):
        """Get detailed disk information"""
        try:
            result = {}
            
            # Get disk usage for all mounted drives
            disks = []
            for partition in psutil.disk_partitions():
                try:
                    # Try shutil first (more reliable on Windows)
                    try:
                        import shutil
                        usage = shutil.disk_usage(partition.mountpoint)
                        method = "shutil"
                    except Exception:
                        # Fallback to psutil if shutil fails
                        usage = psutil.disk_usage(partition.mountpoint)
                        method = "psutil"
                    
                    disk_info = {
                        "Device": partition.device,
                        "Mountpoint": partition.mountpoint,
                        "File System": partition.fstype,
                        "Total Size": self._bytes_to_gb(usage.total),
                        "Used": self._bytes_to_gb(usage.used),
                        "Free": self._bytes_to_gb(usage.free),
                        "Usage Percentage": f"{(usage.used / usage.total) * 100:.1f}%" if usage.total > 0 else "0%"
                    }
                    disks.append(disk_info)
                except (PermissionError, OSError) as e:
                    # Add basic info even if we can't get usage stats
                    disk_info = {
                        "Device": partition.device,
                        "Mountpoint": partition.mountpoint,
                        "File System": partition.fstype,
                        "Status": f"Access limited: {str(e)}"
                    }
                    disks.append(disk_info)
                except SystemError as e:
                    # Handle psutil SystemError specifically
                    disk_info = {
                        "Device": partition.device,
                        "Mountpoint": partition.mountpoint,
                        "File System": partition.fstype,
                        "Status": f"psutil error (trying alternative): {str(e)}"
                    }
                    
                    # Try alternative method for this specific drive
                    try:
                        import shutil
                        usage = shutil.disk_usage(partition.mountpoint)
                        disk_info.update({
                            "Total Size": self._bytes_to_gb(usage.total),
                            "Used": self._bytes_to_gb(usage.used),
                            "Free": self._bytes_to_gb(usage.free),
                            "Usage Percentage": f"{(usage.used / usage.total) * 100:.1f}%" if usage.total > 0 else "0%",
                            "Status": "Retrieved using alternative method"
                        })
                    except Exception:
                        pass
                    
                    disks.append(disk_info)
                except Exception as e:
                    # Catch any other disk-related errors
                    disk_info = {
                        "Device": partition.device,
                        "Mountpoint": partition.mountpoint,
                        "Error": f"Could not access drive: {str(e)}"
                    }
                    disks.append(disk_info)
            
            if disks:
                result["Logical Drives"] = disks
            else:
                result["Logical Drives"] = [{"Message": "No accessible drives found"}]
            
            # Get disk I/O statistics
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    io_info = {
                        "Total Read": self._bytes_to_gb(disk_io.read_bytes),
                        "Total Write": self._bytes_to_gb(disk_io.write_bytes),
                        "Read Operations": disk_io.read_count,
                        "Write Operations": disk_io.write_count
                    }
                    result["Disk I/O Statistics"] = io_info
                else:
                    result["Disk I/O Statistics"] = {"Message": "I/O statistics not available"}
            except Exception as e:
                result["Disk I/O Statistics"] = {"Error": f"Could not get I/O stats: {str(e)}"}
            
            # Try alternative method if no drives were detected
            if not disks:
                try:
                    # Use Windows-specific method to get drive letters
                    import string
                    available_drives = []
                    for letter in string.ascii_uppercase:
                        drive = f"{letter}:\\"
                        if os.path.exists(drive):
                            try:
                                # Try to get free space using os.statvfs or shutil
                                import shutil
                                total, used, free = shutil.disk_usage(drive)
                                drive_info = {
                                    "Device": drive,
                                    "Total Size": self._bytes_to_gb(total),
                                    "Used": self._bytes_to_gb(used),
                                    "Free": self._bytes_to_gb(free),
                                    "Usage Percentage": f"{(used / total) * 100:.1f}%" if total > 0 else "0%",
                                    "Method": "Alternative detection"
                                }
                                available_drives.append(drive_info)
                            except Exception:
                                # Just list the drive without details
                                available_drives.append({
                                    "Device": drive,
                                    "Status": "Drive exists but details unavailable"
                                })
                    
                    if available_drives:
                        result["Logical Drives"] = available_drives
                        result["Detection Method"] = "Alternative Windows drive detection"
                except Exception:
                    pass
            
            # Add WMI disk details using safer query method
            disks_wmi, error = self._safe_wmi_query("Win32_DiskDrive")
            if disks_wmi:
                physical_disks = []
                for disk in disks_wmi:
                    try:
                        disk_detail = {
                            "Model": getattr(disk, 'Model', None) or "Unknown",
                            "Size": self._bytes_to_gb(int(getattr(disk, 'Size', 0))) if getattr(disk, 'Size', None) else "Unknown",
                            "Interface": getattr(disk, 'InterfaceType', None) or "Unknown",
                            "Media Type": getattr(disk, 'MediaType', None) or "Unknown",
                            "Status": getattr(disk, 'Status', None) or "Unknown"
                        }
                        physical_disks.append(disk_detail)
                    except Exception as e:
                        physical_disks.append({"Error": f"Error reading disk properties: {str(e)}"})
                
                if physical_disks:
                    result["Physical Disks"] = physical_disks
                else:
                    result["Physical Disks"] = [{"Message": "No physical disks detected via WMI"}]
            else:
                error_msg = error if error else "WMI connection not available"
                result["Physical Disks"] = [{"Error": f"WMI disk detection failed: {error_msg}"}]
            
            return result
            
        except Exception as e:
            return {
                "Error": f"Could not retrieve disk info: {str(e)}",
                "Basic Info": "Try running as administrator for more detailed disk information"
            }
    
    def get_gpu_info(self):
        """Get GPU information"""
        try:
            gpu_info = []
            
            # Try GPUtil first
            if GPUTIL_AVAILABLE:
                try:
                    gpus = GPUtil.getGPUs()
                    for gpu in gpus:
                        info = {
                            "Name": gpu.name,
                            "Memory Total": f"{gpu.memoryTotal} MB",
                            "Memory Used": f"{gpu.memoryUsed} MB",
                            "Memory Free": f"{gpu.memoryFree} MB",
                            "GPU Load": f"{gpu.load * 100:.1f}%",
                            "Temperature": f"{gpu.temperature}°C"
                        }
                        gpu_info.append(info)
                except Exception:
                    pass
            
            # Add WMI GPU info if available
            if self.wmi_connection:
                try:
                    for gpu in self.wmi_connection.Win32_VideoController():
                        wmi_info = {
                            "Name": gpu.Name or "Unknown",
                            "Driver Version": gpu.DriverVersion or "Unknown",
                            "Driver Date": gpu.DriverDate or "Unknown",
                            "Video Processor": gpu.VideoProcessor or "Unknown",
                            "Video Memory": f"{int(gpu.AdapterRAM) // (1024**2)} MB" if gpu.AdapterRAM else "Unknown",
                            "Status": gpu.Status or "Unknown"
                        }
                        
                        # Check if this GPU is already in the list (from GPUtil)
                        found = False
                        for existing_gpu in gpu_info:
                            if existing_gpu.get("Name", "").lower() in wmi_info["Name"].lower():
                                existing_gpu.update(wmi_info)
                                found = True
                                break
                        
                        if not found:
                            gpu_info.append(wmi_info)
                except Exception:
                    pass
            
            return gpu_info if gpu_info else [{"Message": "No GPU information available"}]
        except Exception as e:
            return [{"Error": f"Could not retrieve GPU info: {str(e)}"}]
    
    def get_network_info(self):
        """Get network information"""
        try:
            network_info = {}
            
            # Get network interfaces
            interfaces = []
            for interface, addresses in psutil.net_if_addrs().items():
                interface_info = {
                    "Interface": interface,
                    "IPv4_Addresses": [],
                    "IPv6_Addresses": [],
                    "MAC_Address": "",
                    "Status": "Unknown",
                    "Speed": "Unknown"
                }
                
                for addr in addresses:
                    # IPv4 addresses
                    if addr.family.name == 'AF_INET':
                        interface_info["IPv4_Addresses"].append({
                            "IP": addr.address,
                            "Netmask": addr.netmask,
                            "Broadcast": addr.broadcast
                        })
                    # IPv6 addresses  
                    elif addr.family.name == 'AF_INET6':
                        interface_info["IPv6_Addresses"].append({
                            "IP": addr.address
                        })
                    # MAC address
                    elif addr.family.name == 'AF_LINK':
                        interface_info["MAC_Address"] = addr.address
                
                # Get interface status and speed
                try:
                    stats = psutil.net_if_stats()
                    if interface in stats:
                        stat = stats[interface]
                        interface_info["Status"] = "Connected" if stat.isup else "Disconnected"
                        interface_info["Speed"] = f"{stat.speed} Mbps" if stat.speed > 0 else "Unknown"
                        interface_info["MTU"] = stat.mtu
                except:
                    pass
                
                interfaces.append(interface_info)
            
            # Get network I/O statistics
            net_io = psutil.net_io_counters()
            io_stats = {}
            if net_io:
                io_stats = {
                    "Bytes Sent": self._bytes_to_gb(net_io.bytes_sent),
                    "Bytes Received": self._bytes_to_gb(net_io.bytes_recv),
                    "Packets Sent": net_io.packets_sent,
                    "Packets Received": net_io.packets_recv,
                    "Errors In": net_io.errin,
                    "Errors Out": net_io.errout,
                    "Drops In": net_io.dropin,
                    "Drops Out": net_io.dropout
                }
            
            network_info = {
                "Hostname": socket.gethostname(),
                "Interfaces": interfaces,
                "Network I/O Statistics": io_stats
            }
            
            return network_info
        except Exception as e:
            return {"Error": f"Could not retrieve network info: {str(e)}"}
    
    def get_motherboard_info(self):
        """Get motherboard information with multiple detection methods"""
        result = {}
        
        # Try WMI with safer query method
        # Get motherboard info
        boards, error = self._safe_wmi_query("Win32_BaseBoard")
        if boards:
            board = boards[0]
            result.update({
                "Manufacturer": getattr(board, 'Manufacturer', None) or "Unknown",
                "Product": getattr(board, 'Product', None) or "Unknown", 
                "Version": getattr(board, 'Version', None) or "Unknown",
                "Serial Number": getattr(board, 'SerialNumber', None) or "Unknown"
            })
        elif error:
            result["Motherboard Error"] = f"Win32_BaseBoard access failed: {error}"
        
        # Get BIOS info
        bios_list, error = self._safe_wmi_query("Win32_BIOS")
        if bios_list:
            bios = bios_list[0]
            result.update({
                "BIOS Manufacturer": getattr(bios, 'Manufacturer', None) or "Unknown",
                "BIOS Version": getattr(bios, 'SMBIOSBIOSVersion', None) or "Unknown",
                "BIOS Date": str(getattr(bios, 'ReleaseDate', None)) if getattr(bios, 'ReleaseDate', None) else "Unknown"
            })
        elif error:
            result["BIOS Error"] = f"Win32_BIOS access failed: {error}"
        
        # Get system info  
        systems, error = self._safe_wmi_query("Win32_ComputerSystem")
        if systems:
            system = systems[0]
            result.update({
                "System Manufacturer": getattr(system, 'Manufacturer', None) or "Unknown",
                "System Model": getattr(system, 'Model', None) or "Unknown",
                "Total Physical Memory": self._bytes_to_gb(int(getattr(system, 'TotalPhysicalMemory', 0))) if getattr(system, 'TotalPhysicalMemory', None) else "Unknown"
            })
        elif error:
            result["System Error"] = f"Win32_ComputerSystem access failed: {error}"
        
        # Add alternative detection methods
        self._add_alternative_motherboard_info(result)
        
        # If we still have no useful info, provide helpful message
        if len([k for k in result.keys() if not k.endswith("Error")]) == 0:
            result.update({
                "Status": "Limited motherboard information available",
                "Suggestion": "Try running as administrator or check Windows services",
                "Alternative Methods": "Use msinfo32, Device Manager, or BIOS setup",
                "WMI Status": self.wmi_error if self.wmi_error else "WMI connection failed"
            })
        
        return result
    
    def _add_alternative_motherboard_info(self, result):
        """Add motherboard info using alternative methods"""
        try:
            # Try registry-based detection
            import winreg
            
            # System information from registry
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS") as key:
                    try:
                        bios_vendor = winreg.QueryValueEx(key, "BIOSVendor")[0]
                        if "BIOS Manufacturer" not in result:
                            result["BIOS Manufacturer (Registry)"] = bios_vendor
                    except FileNotFoundError:
                        pass
                    
                    try:
                        bios_version = winreg.QueryValueEx(key, "BIOSVersion")[0]
                        if "BIOS Version" not in result:
                            result["BIOS Version (Registry)"] = bios_version
                    except FileNotFoundError:
                        pass
                        
                    try:
                        system_manufacturer = winreg.QueryValueEx(key, "SystemManufacturer")[0]
                        if "System Manufacturer" not in result:
                            result["System Manufacturer (Registry)"] = system_manufacturer
                    except FileNotFoundError:
                        pass
                        
                    try:
                        system_product = winreg.QueryValueEx(key, "SystemProductName")[0]
                        if "System Model" not in result:
                            result["System Model (Registry)"] = system_product
                    except FileNotFoundError:
                        pass
                        
            except Exception as e:
                result["Registry Detection"] = f"Failed: {str(e)}"
        
        except ImportError:
            pass
        
        # Add basic platform info
        try:
            if "System" not in result:
                result["Operating System"] = platform.system()
            if "Architecture" not in result:
                result["Architecture"] = platform.architecture()[0]
            if "Machine Type" not in result:
                result["Machine Type"] = platform.machine()
            if "Platform Details" not in result:
                result["Platform Details"] = platform.platform()
        except Exception:
            pass
        
        # Try DMI decode alternative (if available)
        try:
            import subprocess
            # This would require dmidecode tool, which isn't standard on Windows
            # Left as placeholder for future enhancement
        except Exception:
            pass
    
    def get_all_hardware_info(self):
        """Get all hardware information"""
        return {
            "System Information": self.get_system_info(),
            "CPU Information": self.get_cpu_info(),
            "Memory Information": self.get_memory_info(),
            "Disk Information": self.get_disk_info(),
            "GPU Information": self.get_gpu_info(),
            "Network Information": self.get_network_info(),
            "Motherboard Information": self.get_motherboard_info()
        }
    
    def _get_uptime(self):
        """Get system uptime"""
        try:
            uptime_seconds = psutil.boot_time()
            uptime = datetime.now() - datetime.fromtimestamp(uptime_seconds)
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{days} days, {hours} hours, {minutes} minutes"
        except Exception:
            return "Unknown"
    
    def _get_windows_info(self):
        """Get Windows-specific information using thread-safe WMI queries"""
        try:
            info = {}
            
            # Use thread-safe WMI query
            os_data, error = self._safe_wmi_query("Win32_OperatingSystem")
            if os_data and not error:
                try:
                    for os_info in os_data:
                        # Convert WMI dates to readable format
                        install_date = self._convert_wmi_date(getattr(os_info, 'InstallDate', None))
                        last_boot = self._convert_wmi_date(getattr(os_info, 'LastBootUpTime', None))
                        
                        info.update({
                            "Windows Edition": getattr(os_info, 'Caption', 'Unknown') or "Unknown",
                            "Windows Build": getattr(os_info, 'BuildNumber', 'Unknown') or "Unknown", 
                            "Windows Version": getattr(os_info, 'Version', 'Unknown') or "Unknown",
                            "Install Date": install_date,
                            "Last Boot": last_boot
                        })
                        break
                except Exception as e:
                    info["Windows Info Note"] = "Advanced Windows details require elevated privileges"
            else:
                info["Windows Info Note"] = "WMI access not available - using basic detection"
            
            return info
        except Exception as e:
            return {"Windows Info Note": "Could not retrieve Windows details"}
    
    def _convert_wmi_date(self, wmi_date):
        """Convert WMI date format to readable format"""
        if not wmi_date:
            return "Unknown"
        
        try:
            # WMI date format: YYYYMMDDHHMMSS.ffffff+UUU
            # Example: 20250321204727.000000+000
            date_str = str(wmi_date)
            
            # Extract the main date part (before the dot and timezone)
            if '.' in date_str:
                date_part = date_str.split('.')[0]
            else:
                date_part = date_str[:14]  # Take first 14 characters
            
            # Parse the date: YYYYMMDDHHMMSS
            if len(date_part) >= 14:
                year = date_part[0:4]
                month = date_part[4:6]
                day = date_part[6:8]
                hour = date_part[8:10]
                minute = date_part[10:12]
                second = date_part[12:14]
                
                # Format as readable date
                return f"{year}-{month}-{day} {hour}:{minute}:{second}"
            else:
                return str(wmi_date)[:19]  # Fallback to first 19 chars
                
        except Exception as e:
            return f"Invalid date format: {str(wmi_date)}"
    
    def _bytes_to_gb(self, bytes_value):
        """Convert bytes to GB with appropriate unit"""
        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024**2:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024**3:
            return f"{bytes_value / (1024**2):.1f} MB"
        else:
            return f"{bytes_value / (1024**3):.1f} GB"
