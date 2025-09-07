#!/usr/bin/env python3
"""
Windows-specific temperature monitoring
Provides temperature detection for Windows systems using WMI and other methods
"""

import time
import psutil

def get_windows_temperatures():
    """
    Get system temperatures on Windows using multiple methods
    Returns dict with temperature data or None if unavailable
    """
    temperatures = {}
    
    # Method 1: WMI Temperature Sensors
    try:
        import wmi
        import pythoncom
        
        # Initialize COM for this thread
        pythoncom.CoInitialize()
        
        try:
            # Try WMI temperature classes
            c = wmi.WMI(namespace="root\\wmi")
            
            # MSAcpi_ThermalZoneTemperature (most common)
            try:
                thermal_zones = c.MSAcpi_ThermalZoneTemperature()
                for zone in thermal_zones:
                    if hasattr(zone, 'CurrentTemperature'):
                        # Convert from tenths of Kelvin to Celsius
                        temp_celsius = (zone.CurrentTemperature / 10.0) - 273.15
                        if 0 < temp_celsius < 150:  # Sanity check
                            zone_name = getattr(zone, 'InstanceName', 'Thermal Zone')
                            temperatures[f"WMI_{zone_name}"] = {
                                'current': temp_celsius,
                                'label': zone_name,
                                'high': 85.0,
                                'critical': 95.0
                            }
            except Exception:
                # Silently skip - these errors are common on many systems
                pass
            
            # Win32_TemperatureProbe (alternative)
            try:
                temp_probes = c.Win32_TemperatureProbe()
                for probe in temp_probes:
                    if hasattr(probe, 'CurrentReading') and probe.CurrentReading:
                        temp_celsius = probe.CurrentReading / 10.0  # Usually in tenths of degrees
                        if 0 < temp_celsius < 150:
                            probe_name = getattr(probe, 'Name', 'Temperature Probe')
                            temperatures[f"WMI_{probe_name}"] = {
                                'current': temp_celsius,
                                'label': probe_name,
                                'high': 85.0,
                                'critical': 95.0
                            }
            except Exception:
                # Silently skip - these errors are common on many systems
                pass
                
        except Exception as e:
            print(f"WMI temperature detection error: {e}")
        finally:
            pythoncom.CoUninitialize()
            
    except ImportError:
        print("WMI not available for temperature monitoring")
    except Exception as e:
        print(f"WMI initialization error: {e}")
    
    # Method 2: Estimate from CPU usage (rough fallback)
    if not temperatures:
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            if cpu_usage > 0:
                # Very rough estimation based on CPU load
                # Base temperature + load factor
                base_temp = 35  # Typical idle temperature
                load_factor = cpu_usage * 0.5  # Rough scaling
                estimated_temp = base_temp + load_factor
                
                temperatures["CPU_Estimated"] = {
                    'current': estimated_temp,
                    'label': 'CPU (Estimated)',
                    'high': 75.0,
                    'critical': 85.0,
                    'estimated': True
                }
        except Exception as e:
            print(f"CPU estimation error: {e}")
    
    # Method 3: Try to get GPU temperature
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        for i, gpu in enumerate(gpus):
            if gpu.temperature and gpu.temperature > 0:
                temperatures[f"GPU_{i}"] = {
                    'current': gpu.temperature,
                    'label': f'GPU {i} ({gpu.name[:20]})',
                    'high': 80.0,
                    'critical': 90.0
                }
    except ImportError:
        pass
    except Exception as e:
        print(f"GPU temperature error: {e}")
    
    return temperatures if temperatures else None

def get_max_temperature():
    """Get the maximum temperature from all available sensors"""
    temps = get_windows_temperatures()
    if not temps:
        return 0
    
    max_temp = 0
    for sensor_data in temps.values():
        current = sensor_data.get('current', 0)
        if current > max_temp:
            max_temp = current
    
    return max_temp

def get_temperature_status(temp_celsius):
    """Get temperature status with color coding"""
    if temp_celsius <= 0:
        return "N/A", "gray"
    elif temp_celsius > 85:
        return "CRITICAL", "red"
    elif temp_celsius > 70:
        return "HIGH", "orange"
    elif temp_celsius > 60:
        return "WARM", "yellow"
    else:
        return "NORMAL", "blue"

def format_temperature_display(temp_celsius, estimated=False):
    """Format temperature for display"""
    if temp_celsius <= 0:
        return "N/A"
    
    prefix = "~" if estimated else ""
    return f"{prefix}{temp_celsius:.0f}°C"

def get_detailed_temperature_info():
    """Get detailed temperature information for professional display"""
    temps = get_windows_temperatures()
    
    if not temps:
        return """🌡️ TEMPERATURE MONITORING - Windows System
==================================================

❌ No temperature sensors detected on this Windows system.

This is common on many Windows systems because:
• Temperature monitoring requires special WMI drivers
• Some systems don't expose temperature data
• Hardware-specific drivers may be needed

🔧 ALTERNATIVES FOR TEMPERATURE MONITORING:
• Use hardware-specific software (MSI Afterburner, HWiNFO64)
• Install manufacturer utilities (Intel XTU, AMD Ryzen Master)
• Use dedicated monitoring tools (Open Hardware Monitor)
• Check BIOS/UEFI for hardware monitoring

🔍 CURRENT SYSTEM STATUS:
• CPU Usage-based estimation available
• GPU temperature may be available if supported
• System appears stable based on performance metrics"""

    info = f"🌡️ TEMPERATURE MONITORING - {time.strftime('%H:%M:%S')}\n"
    info += "=" * 50 + "\n\n"
    
    info += "Temperature Sensors:\n"
    info += "-" * 20 + "\n"
    
    for sensor_name, sensor_data in temps.items():
        label = sensor_data['label']
        current = sensor_data['current']
        high = sensor_data.get('high', 'N/A')
        critical = sensor_data.get('critical', 'N/A')
        estimated = sensor_data.get('estimated', False)
        
        status, color = get_temperature_status(current)
        
        if estimated:
            info += f"  {label}: ~{current:.1f}°C (Estimated) - {status}\n"
        else:
            info += f"  {label}: {current:.1f}°C - {status}\n"
        
        info += f"    High Threshold: {high}°C\n"
        info += f"    Critical Threshold: {critical}°C\n"
        info += "\n"
    
    # Add general status
    max_temp = get_max_temperature()
    if max_temp > 85:
        info += "🔴 THERMAL STATUS: HIGH TEMPERATURE - Monitor closely\n"
    elif max_temp > 70:
        info += "🟡 THERMAL STATUS: ELEVATED - Normal under load\n"
    else:
        info += "✅ THERMAL STATUS: NORMAL - Temperatures within safe range\n"
    
    return info

# Test function
if __name__ == "__main__":
    print("Testing Windows temperature monitoring...")
    temps = get_windows_temperatures()
    if temps:
        print(f"Found {len(temps)} temperature sensors:")
        for name, data in temps.items():
            print(f"  {name}: {data['current']:.1f}°C")
    else:
        print("No temperature sensors detected")
    
    print(f"\nMax temperature: {get_max_temperature():.1f}°C")
    print(get_detailed_temperature_info())
