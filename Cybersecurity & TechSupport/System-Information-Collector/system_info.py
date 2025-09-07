import psutil
import platform
import subprocess
import os
import getpass
from datetime import datetime, timedelta
import GPUtil

# Cross-platform function to get installed software
def get_installed_software():
    installed_software = []
    if platform.system() == 'Windows':
        import winreg
        try:
            reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as reg_key:
                for i in range(0, winreg.QueryInfoKey(reg_key)[0]):
                    try:
                        sub_key_name = winreg.EnumKey(reg_key, i)
                        with winreg.OpenKey(reg_key, sub_key_name) as sub_key:
                            software_name = winreg.QueryValueEx(sub_key, "DisplayName")[0]
                            installed_software.append(software_name)
                    except FileNotFoundError:
                        continue
        except FileNotFoundError:
            pass
    elif platform.system() == 'Linux':
        # Try dpkg (Debian-based systems)
        try:
            dpkg_output = subprocess.run(['dpkg-query', '-l'], capture_output=True, text=True).stdout
            if dpkg_output:
                installed_software = [line.split()[1] for line in dpkg_output.splitlines() if line.startswith('ii')]
        except FileNotFoundError:
            # Try rpm (Red Hat-based systems)
            try:
                rpm_output = subprocess.run(['rpm', '-qa'], capture_output=True, text=True).stdout
                if rpm_output:
                    installed_software = rpm_output.splitlines()
            except FileNotFoundError:
                # Fallback to listing files in /usr/bin and /usr/local/bin
                common_dirs = ["/usr/bin", "/usr/local/bin"]
                for common_dir in common_dirs:
                    for root, dirs, files in os.walk(common_dir):
                        for file in files:
                            installed_software.append(file)
    return installed_software

# Cross-platform function to get installed browsers
def get_installed_browsers():
    browsers = []
    if platform.system() == 'Windows':
        import winreg
        browser_reg_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
            r"SOFTWARE\Clients\StartMenuInternet"
        ]
        for reg_path in browser_reg_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as reg_key:
                    for i in range(0, winreg.QueryInfoKey(reg_key)[0]):
                        try:
                            sub_key_name = winreg.EnumKey(reg_key, i)
                            with winreg.OpenKey(reg_key, sub_key_name) as sub_key:
                                try:
                                    browser_path = winreg.QueryValueEx(sub_key, "")[0]
                                    browser_name = sub_key_name
                                    # Get browser version from the executable
                                    version_info = subprocess.run([browser_path, "--version"], capture_output=True, text=True).stdout
                                    version = version_info.strip()
                                    # Construct user agent based on browser name and version
                                    if "chrome" in browser_name.lower():
                                        user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
                                    elif "firefox" in browser_name.lower():
                                        user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}) Gecko/20100101 Firefox/{version}"
                                    elif "edge" in browser_name.lower():
                                        user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 Edg/{version}"
                                    elif "opera" in browser_name.lower():
                                        user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 OPR/{version}"
                                    elif "iexplore" in browser_name.lower():
                                        user_agent = f"Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:{version}) like Gecko"
                                    else:
                                        user_agent = "Unknown"
                                    browsers.append({
                                        'name': browser_name,
                                        'path': browser_path,
                                        'version': version,
                                        'user_agent': user_agent
                                    })
                                except FileNotFoundError:
                                    continue
                        except FileNotFoundError:
                            continue
            except FileNotFoundError:
                continue
    elif platform.system() == 'Linux':
        # Search for browsers in common directories
        common_dirs = [
            "/usr/bin",
            "/usr/local/bin",
            "/opt",
            "/snap/bin"
        ]
        browser_executables = [
            "google-chrome",
            "chrome",
            "firefox",
            "opera",
            "brave-browser",
            "chromium-browser",
            "microsoft-edge",
            "vivaldi",
            "waterfox"
        ]
        for common_dir in common_dirs:
            for root, dirs, files in os.walk(common_dir):
                for file in files:
                    if file.lower() in browser_executables:
                        browser_path = os.path.join(root, file)
                        # Get browser version from the executable
                        version_info = subprocess.run([browser_path, "--version"], capture_output=True, text=True).stdout
                        version = version_info.strip()
                        # Construct user agent based on browser name and version
                        if "chrome" in file.lower():
                            user_agent = f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
                        elif "firefox" in file.lower():
                            user_agent = f"Mozilla/5.0 (X11; Linux x86_64; rv:{version}) Gecko/20100101 Firefox/{version}"
                        elif "opera" in file.lower():
                            user_agent = f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 OPR/{version}"
                        elif "brave" in file.lower():
                            user_agent = f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
                        elif "chromium" in file.lower():
                            user_agent = f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
                        elif "edge" in file.lower():
                            user_agent = f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 Edg/{version}"
                        elif "vivaldi" in file.lower():
                            user_agent = f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 Vivaldi/{version}"
                        elif "waterfox" in file.lower():
                            user_agent = f"Mozilla/5.0 (X11; Linux x86_64; rv:{version}) Gecko/20100101 Waterfox/{version}"
                        else:
                            user_agent = "Unknown"
                        browsers.append({
                            'name': file,
                            'path': browser_path,
                            'version': version,
                            'user_agent': user_agent
                        })
    return browsers

# Cross-platform function to get firewall rules
def get_firewall_rules():
    if platform.system() == 'Windows':
        try:
            firewall_output = subprocess.run(['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all'], capture_output=True, text=True).stdout
            return firewall_output
        except FileNotFoundError:
            return 'Netsh command not found or not available'
    elif platform.system() == 'Linux':
        try:
            firewall_output = subprocess.run(['ufw', 'status'], capture_output=True, text=True).stdout
            return firewall_output
        except FileNotFoundError:
            return 'UFW not installed'
    return 'Firewall information not available'

# Cross-platform function to get user information
def get_user_info():
    return {
        'current_user': getpass.getuser(),
        'users': [user.name for user in psutil.users()]
    }

# Cross-platform function to get hardware information
def get_hardware_info():
    cpu_info = {}
    if hasattr(psutil, 'cpu_freq'):
        cpu_freq = psutil.cpu_freq()
        cpu_info['cpu_freq'] = cpu_freq.current if cpu_freq else 'Unknown'
    else:
        cpu_info['cpu_freq'] = 'Unknown'

    cpu_info['cpu_count'] = psutil.cpu_count(logical=True)
    cpu_info['cpu_physical_count'] = psutil.cpu_count(logical=False)
    cpu_info['cpu_model'] = platform.processor()

    memory_info = psutil.virtual_memory()
    disk_info = [psutil.disk_usage(partition.mountpoint) for partition in psutil.disk_partitions()]

    battery_info = {}
    if hasattr(psutil, 'sensors_battery'):
        battery = psutil.sensors_battery()
        if battery:
            battery_info['percent'] = battery.percent
            battery_info['power_plugged'] = battery.power_plugged
        else:
            battery_info['percent'] = 'No battery'
            battery_info['power_plugged'] = 'No battery'
    else:
        battery_info['percent'] = 'Battery info not available'
        battery_info['power_plugged'] = 'Battery info not available'

    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())

    gpu_info = []
    gpus = GPUtil.getGPUs()
    for gpu in gpus:
        gpu_info.append({
            'id': gpu.id,
            'name': gpu.name,
            'load': gpu.load,
            'memory_total': gpu.memoryTotal,
            'memory_used': gpu.memoryUsed,
            'memory_free': gpu.memoryFree,
            'temperature': gpu.temperature
        })

    return {
        'cpu_info': cpu_info,
        'memory_info': memory_info,
        'disk_info': disk_info,
        'battery_info': battery_info,
        'uptime': uptime,
        'gpu_info': gpu_info
    }

# Cross-platform function to get network information
def get_network_info():
    network_info = {}
    for interface, addrs in psutil.net_if_addrs().items():
        network_info[interface] = []
        for addr in addrs:
            network_info[interface].append({
                'family': addr.family.name,
                'address': addr.address,
                'netmask': addr.netmask,
                'broadcast': addr.broadcast
            })
    return network_info

# Cross-platform function to get network hardware information
def get_network_hardware_info():
    network_hardware_info = {}
    for interface, stats in psutil.net_if_stats().items():
        network_hardware_info[interface] = {
            'is_up': stats.isup,
            'duplex': stats.duplex,
            'speed': stats.speed,
            'mtu': stats.mtu
        }
    return network_hardware_info

# Cross-platform function to get system information
def get_system_info():
    # Gather hardware information
    cpu_info = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    network_io = psutil.net_io_counters()

    # Gather system information
    os_info = platform.system()
    os_version = platform.version()
    machine_type = platform.machine()

    # Gather AV and firewall information
    av_info = {}
    firewall_info = {}
    
    # Get installed software
    installed_software = get_installed_software()

    if os_info == 'Windows':
        # Windows specific commands
        av_info['windows_av'] = [software for software in installed_software if "norton" in software.lower() or "windows defender" in software.lower()]
        
        firewall_info['windows_firewall_rules'] = get_firewall_rules()
    elif os_info == 'Linux':
        # Linux specific commands
        try:
            av_info['linux_av'] = subprocess.run(['clamscan', '--version'], capture_output=True, text=True).stdout
        except FileNotFoundError:
            av_info['linux_av'] = 'ClamAV not installed'
        
        try:
            firewall_info['linux_firewall'] = subprocess.run(['ufw', 'status'], capture_output=True, text=True).stdout
        except FileNotFoundError:
            firewall_info['linux_firewall'] = 'UFW not installed'

    # Return all gathered information
    return {
        'cpu_info': cpu_info,
        'memory_info': memory_info,
        'disk_info': disk_info,
        'network_io': network_io,
        'network_info': get_network_info(),
        'network_hardware_info': get_network_hardware_info(),
        'os_info': os_info,
        'os_version': os_version,
        'machine_type': machine_type,
        'av_info': av_info,
        'firewall_info': firewall_info,
        'installed_software': installed_software,
        'installed_browsers': get_installed_browsers(),
        'user_info': get_user_info(),
        'hardware_info': get_hardware_info()
    }

def print_system_info(system_info, file):
    file.write("=== System Information ===\n")
    file.write(f"OS: {system_info['os_info']}\n")
    file.write(f"OS Version: {system_info['os_version']}\n")
    file.write(f"Machine Type: {system_info['machine_type']}\n")
    file.write("\n=== Hardware Information ===\n")
    file.write(f"CPU Usage: {system_info['cpu_info']}%\n")
    file.write(f"CPU Model: {system_info['hardware_info']['cpu_info']['cpu_model']}\n")
    file.write(f"CPU Count: {system_info['hardware_info']['cpu_info']['cpu_count']}\n")
    file.write(f"CPU Physical Cores: {system_info['hardware_info']['cpu_info']['cpu_physical_count']}\n")
    file.write(f"CPU Frequency: {system_info['hardware_info']['cpu_info']['cpu_freq']} MHz\n")
    file.write(f"Memory Usage: {system_info['memory_info'].percent}%\n")
    file.write(f"Total Memory: {system_info['memory_info'].total / (1024 ** 3):.2f} GB\n")
    file.write(f"Available Memory: {system_info['memory_info'].available / (1024 ** 3):.2f} GB\n")
    file.write(f"Disk Usage: {system_info['disk_info'].percent}%\n")
    file.write(f"Total Disk Space: {system_info['disk_info'].total / (1024 ** 3):.2f} GB\n")
    file.write(f"Free Disk Space: {system_info['disk_info'].free / (1024 ** 3):.2f} GB\n")
    file.write(f"Battery Percentage: {system_info['hardware_info']['battery_info']['percent']}\n")
    file.write(f"Power Plugged: {system_info['hardware_info']['battery_info']['power_plugged']}\n")
    file.write(f"System Uptime: {system_info['hardware_info']['uptime']}\n")
    file.write("\n=== GPU Information ===\n")
    for gpu in system_info['hardware_info']['gpu_info']:
        file.write(f"GPU ID: {gpu['id']}\n")
        file.write(f"GPU Name: {gpu['name']}\n")
        file.write(f"GPU Load: {gpu['load'] * 100}%\n")
        file.write(f"GPU Memory Total: {gpu['memory_total']} MB\n")
        file.write(f"GPU Memory Used: {gpu['memory_used']} MB\n")
        file.write(f"GPU Memory Free: {gpu['memory_free']} MB\n")
        file.write(f"GPU Temperature: {gpu['temperature']} C\n")
    file.write("\n=== User Information ===\n")
    file.write(f"Current User: {system_info['user_info']['current_user']}\n")
    file.write(f"Users: {', '.join(system_info['user_info']['users'])}\n")
    file.write("\n=== Antivirus Information ===\n")
    for key, value in system_info['av_info'].items():
        file.write(f"{key}: {', '.join(value) if isinstance(value, list) else value}\n")
    file.write("\n=== Firewall Information ===\n")
    if system_info['os_info'] == 'Windows':
        file.write(system_info['firewall_info']['windows_firewall_rules'])
    elif system_info['os_info'] == 'Linux':
        file.write(system_info['firewall_info']['linux_firewall'])
    file.write("\n=== Network Information ===\n")
    file.write(f"Network I/O: {system_info['network_io']}\n")
    for interface, addrs in system_info['network_info'].items():
        file.write(f"\nInterface: {interface}\n")
        for addr in addrs:
            file.write(f"  Family: {addr['family']}\n")
            file.write(f"  Address: {addr['address']}\n")
            file.write(f"  Netmask: {addr['netmask']}\n")
            file.write(f"  Broadcast: {addr['broadcast']}\n")
    file.write("\n=== Network Hardware Information ===\n")
    for interface, stats in system_info['network_hardware_info'].items():
        file.write(f"\nInterface: {interface}\n")
        for key, value in stats.items():
            file.write(f"  {key}: {value}\n")
    file.write("\n=== Installed Software ===\n")
    file.write("\n".join(system_info['installed_software']))
    file.write("\n=== Installed Browsers ===\n")
    for browser in system_info['installed_browsers']:
        file.write(f"Browser Name: {browser['name']}\n")
        file.write(f"Browser Path: {browser['path']}\n")
        file.write(f"Browser Version: {browser['version']}\n")
        file.write(f"User Agent: {browser['user_agent']}\n")

if __name__ == '__main__':
    system_info = get_system_info()
    with open('system_info_log.txt', 'w') as file:
        print_system_info(system_info, file) 