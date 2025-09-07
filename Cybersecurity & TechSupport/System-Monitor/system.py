import os
import psutil
import platform
import time
import socket
from termcolor import colored  # For colored text

class SystemMonitor:
    def __init__(self):
        self.os_info = platform.uname()
        self.root_dir = self.get_root_directory()
        self.prev_network_io = psutil.net_io_counters()  # Initialize network I/O counters
        self.last_network_process_update = time.time()  # Track last network process update time
        self.network_processes = []  # Cache network processes
        self.previous_processes = set()  # Track previous processes for highlighting new ones
        self.update_interval = 1  # Default update interval in seconds
        self.show_hidden = False  # Toggle for showing hidden processes
        self.show_vulnerable = False  # Toggle for showing vulnerable processes
        self.show_network = False  # Toggle for showing network processes

    def get_root_directory(self):
        """Get a valid root directory based on the operating system."""
        if os.name == 'nt':  # Windows
            drives = [f"{d}:\\" for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f"{d}:\\")]
            for drive in drives:
                try:
                    # Validate the drive by checking if it's accessible
                    if os.path.isdir(drive):
                        return drive
                except Exception as e:
                    print(f"Drive {drive} is invalid or inaccessible: {e}")
            return 'C:\\'  # Fallback to C:\
        else:  # UNIX-like systems
            try:
                if os.path.isdir('/'):
                    return '/'
            except Exception as e:
                print(f"Root directory '/' is invalid or inaccessible: {e}")
                return os.getcwd()

    def get_system_health(self):
        """Monitor system health in real-time."""
        cpu_usage = psutil.cpu_percent(interval=self.update_interval)
        memory_info = psutil.virtual_memory()
        disk_usage = None
        swap_memory = psutil.swap_memory()

        # Get disk usage (skip if the root directory is invalid)
        try:
            disk_usage = psutil.disk_usage(self.root_dir)
        except Exception as e:
            print(f"Failed to get disk usage for {self.root_dir}: {e}")

        return {
            "CPU Usage (%)": cpu_usage,
            "Memory Usage (%)": memory_info.percent,
            "Available Memory (MB)": round(memory_info.available / (1024 * 1024), 2),
            "Disk Usage (%)": disk_usage.percent if disk_usage else "N/A",
            "Swap Usage (%)": swap_memory.percent,
            "Total Swap (MB)": round(swap_memory.total / (1024 * 1024), 2),
            "Used Swap (MB)": round(swap_memory.used / (1024 * 1024), 2),
        }

    def get_processes(self):
        """List all processes and mark hidden/vulnerable ones."""
        processes = []
        current_processes = set()
        for proc in psutil.process_iter(attrs=['pid', 'name', 'username', 'exe', 'status']):
            try:
                process_info = proc.info
                process_info['hidden'] = process_info['exe'] is None or not os.path.exists(process_info['exe'])
                process_info['vulnerable'] = self.is_process_vulnerable(proc)
                processes.append(process_info)
                current_processes.add(proc.info['pid'])  # Track current processes
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

        # Determine new processes
        new_processes = current_processes - self.previous_processes
        self.previous_processes = current_processes

        return processes, new_processes

    def get_network_processes(self):
        """List network-related processes."""
        if time.time() - self.last_network_process_update < 30:  # Update every 30 seconds
            return self.network_processes

        network_processes = []
        for proc in psutil.process_iter(attrs=['pid', 'name', 'username', 'exe', 'status']):
            try:
                if proc.connections():  # Check if the process has network connections
                    process_info = proc.info
                    process_info['hidden'] = process_info['exe'] is None or not os.path.exists(process_info['exe'])
                    process_info['vulnerable'] = self.is_process_vulnerable(proc)
                    network_processes.append(process_info)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

        self.network_processes = network_processes
        self.last_network_process_update = time.time()
        return network_processes

    def is_process_vulnerable(self, proc):
        """Check if a process is vulnerable (e.g., running with elevated privileges)."""
        try:
            # Example: Mark processes running as root or with known vulnerabilities
            if proc.info['username'] == 'root' or proc.info['name'] in ['vulnerable_process']:
                return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        return False

    def get_network_usage(self):
        """Get network usage (sent/received bytes and speed)."""
        current_network_io = psutil.net_io_counters()
        sent_bytes = current_network_io.bytes_sent - self.prev_network_io.bytes_sent
        recv_bytes = current_network_io.bytes_recv - self.prev_network_io.bytes_recv
        self.prev_network_io = current_network_io  # Update previous network I/O counters

        # Calculate network speed in MB/s
        sent_speed = sent_bytes / (1024 * 1024)  # Convert to MB
        recv_speed = recv_bytes / (1024 * 1024)  # Convert to MB

        return {
            "Sent Bytes": sent_bytes,
            "Received Bytes": recv_bytes,
            "Sent Speed (MB/s)": sent_speed,
            "Received Speed (MB/s)": recv_speed,
        }

    def get_ip_addresses(self):
        """Get the system's IP addresses (IPv4 and IPv6)."""
        ip_addresses = []
        try:
            # Get all network interfaces
            interfaces = psutil.net_if_addrs()
            for interface_name, interface_addresses in interfaces.items():
                for address in interface_addresses:
                    if address.family == socket.AF_INET:  # IPv4
                        ip_addresses.append(f"IPv4 ({interface_name}): {address.address}")
                    elif address.family == socket.AF_INET6:  # IPv6
                        ip_addresses.append(f"IPv6 ({interface_name}): {address.address}")
        except Exception as e:
            print(f"Failed to retrieve IP addresses: {e}")

        return ip_addresses

    def get_warnings(self, health_data):
        """Check for critical system health warnings."""
        warnings = []
        if health_data["CPU Usage (%)"] > 85:
            warnings.append("High CPU usage detected (>85%). Consider closing resource-heavy applications.")
        if health_data["Memory Usage (%)"] > 90:
            warnings.append("High memory usage detected (>90%). Consider freeing up memory.")
        if health_data["Disk Usage (%)"] != "N/A" and health_data["Disk Usage (%)"] > 90:
            warnings.append("High disk usage detected (>90%). Consider cleaning up disk space.")
        if health_data["Swap Usage (%)"] > 80:
            warnings.append("High swap usage detected (>80%). This may slow down your system.")
        return warnings

    def get_memory_leaks(self):
        """Detect potential memory leaks."""
        leaks = []
        for proc in psutil.process_iter(attrs=['pid', 'name', 'memory_info']):
            try:
                mem_info = proc.info['memory_info']
                if mem_info.rss > (500 * 1024 * 1024):  # Processes using >500MB might be suspicious
                    leaks.append(f"PID {proc.info['pid']} ({proc.info['name']}) is using a large amount of memory: {round(mem_info.rss / (1024 * 1024), 2)} MB.")
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        return leaks

    def display_static_system_info(self):
        """Display static system information."""
        print("\n=== Static System Information ===")
        print(f"System: {self.os_info.system}")
        print(f"Node Name: {self.os_info.node}")
        print(f"Release: {self.os_info.release}")
        print(f"Version: {self.os_info.version}")
        print(f"Machine: {self.os_info.machine}")
        print(f"Processor: {self.os_info.processor}")
        print(f"Root Directory: {self.root_dir}")

    def display_menu(self):
        """Display the main menu for selecting what to show."""
        print("\n=== Main Menu ===")
        print("1. Show System Health")
        print("2. Show Processes")
        print("3. Show Network Usage")
        print("4. Show Warnings")
        print("5. Show Memory Leaks")
        print("6. Exit")

    def display_process_menu(self):
        """Display the process menu for selecting process filters."""
        print("\n=== Process Display Menu ===")
        print("1. Show All Processes")
        print("2. Only Hidden Processes")
        print("3. Only Vulnerable Processes")
        print("4. Only Network Processes")
        print("5. Mix (Custom Combination)")
        print("6. Return to Main Menu")

    def display_system_health(self):
        """Display system health in real-time."""
        try:
            while True:
                health = self.get_system_health()
                print("\n=== System Health ===")
                for key, value in health.items():
                    print(f"{key}: {value}")
                print("\nPress 'Ctrl+C' to return to the menu.")
                time.sleep(self.update_interval)  # Update every specified interval
                os.system('cls' if os.name == 'nt' else 'clear')
                self.display_static_system_info()
        except KeyboardInterrupt:
            return  # Return to the menu on Ctrl+C

    def display_warnings(self):
        """Display warnings in real-time."""
        try:
            while True:
                health = self.get_system_health()
                warnings = self.get_warnings(health)
                print("\n=== Warnings ===")
                if warnings:
                    for warning in warnings:
                        print(colored(warning, "red"))  # Mark warnings in red
                else:
                    print("No warnings detected.")
                print("\nPress 'Ctrl+C' to return to the menu.")
                time.sleep(self.update_interval)  # Update every specified interval
                os.system('cls' if os.name == 'nt' else 'clear')
                self.display_static_system_info()
        except KeyboardInterrupt:
            return  # Return to the menu on Ctrl+C

    def display_processes(self):
        """Display processes based on selected filters."""
        try:
            while True:
                if self.show_network:
                    processes = self.get_network_processes()
                else:
                    processes, new_processes = self.get_processes()

                print("\n=== Processes ===")
                for proc in processes:
                    hidden_flag = colored("(Hidden)", "red") if proc['hidden'] else ""
                    vulnerable_flag = colored("(Vulnerable)", "yellow") if proc['vulnerable'] else ""
                    process_line = f"PID: {proc['pid']}, Name: {proc['name']}, User: {proc['username']}, Status: {proc['status']} {hidden_flag} {vulnerable_flag}"

                    # Apply filters
                    if (self.show_hidden and proc['hidden']) or \
                       (self.show_vulnerable and proc['vulnerable']) or \
                       (self.show_network and proc in self.network_processes) or \
                       (not self.show_hidden and not self.show_vulnerable and not self.show_network):
                        if 'new_processes' in locals() and proc['pid'] in new_processes:
                            print(colored(process_line, "green"))  # Highlight new processes in green
                        else:
                            print(process_line)

                print("\nPress 'Ctrl+C' to return to the menu.")
                time.sleep(self.update_interval)  # Update every specified interval
                os.system('cls' if os.name == 'nt' else 'clear')
                self.display_static_system_info()
        except KeyboardInterrupt:
            return  # Return to the menu on Ctrl+C

    def display_network_usage(self):
        """Display network usage and IP addresses in real-time."""
        try:
            while True:
                network_usage = self.get_network_usage()
                ip_addresses = self.get_ip_addresses()

                print("\n=== Network Usage ===")
                for key, value in network_usage.items():
                    print(f"{key}: {value}")

                print("\n=== IP Addresses ===")
                if ip_addresses:
                    for ip in ip_addresses:
                        print(ip)
                else:
                    print("No IP addresses found.")

                print("\nPress 'Ctrl+C' to return to the menu.")
                time.sleep(self.update_interval)  # Update every specified interval
                os.system('cls' if os.name == 'nt' else 'clear')
                self.display_static_system_info()
        except KeyboardInterrupt:
            return  # Return to the menu on Ctrl+C

    def display_memory_leaks(self):
        """Display memory leaks in real-time."""
        try:
            while True:
                leaks = self.get_memory_leaks()
                print("\n=== Memory Leak Detection ===")
                if leaks:
                    for leak in leaks:
                        print(leak)
                else:
                    print("No potential memory leaks detected.")
                print("\nPress 'Ctrl+C' to return to the menu.")
                time.sleep(self.update_interval)  # Update every specified interval
                os.system('cls' if os.name == 'nt' else 'clear')
                self.display_static_system_info()
        except KeyboardInterrupt:
            return  # Return to the menu on Ctrl+C

    def set_update_interval(self):
        """Set the update interval for real-time monitoring."""
        try:
            interval = int(input("Enter update interval in seconds (default is 1): ") or 1)
            if interval <= 0:
                print("Interval must be greater than 0. Using default interval of 1 second.")
                self.update_interval = 1
            else:
                self.update_interval = interval
                print(f"Update interval set to {self.update_interval} seconds.")
        except ValueError:
            print("Invalid input. Using default interval of 1 second.")
            self.update_interval = 1

    def run(self):
        """Run the system monitor with a menu."""
        # Display static system information
        self.display_static_system_info()

        # Ask for update interval
        self.set_update_interval()

        # Main menu loop
        while True:
            self.display_menu()
            choice = input("Select an option: ")

            if choice == "1":
                self.display_system_health()
            elif choice == "2":
                self.handle_process_menu()
            elif choice == "3":
                self.display_network_usage()
            elif choice == "4":
                self.display_warnings()
            elif choice == "5":
                self.display_memory_leaks()
            elif choice == "6":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")

            input("\nPress Enter to continue...")
            os.system('cls' if os.name == 'nt' else 'clear')

    def handle_process_menu(self):
        """Handle the process display menu."""
        while True:
            self.display_process_menu()
            choice = input("Select an option: ")

            if choice == "1":
                self.show_hidden = False
                self.show_vulnerable = False
                self.show_network = False
                self.display_processes()
            elif choice == "2":
                self.show_hidden = True
                self.show_vulnerable = False
                self.show_network = False
                self.display_processes()
            elif choice == "3":
                self.show_hidden = False
                self.show_vulnerable = True
                self.show_network = False
                self.display_processes()
            elif choice == "4":
                self.show_hidden = False
                self.show_vulnerable = False
                self.show_network = True
                self.display_processes()
            elif choice == "5":
                self.show_hidden = input("Show hidden processes? (y/n): ").lower() == 'y'
                self.show_vulnerable = input("Show vulnerable processes? (y/n): ").lower() == 'y'
                self.show_network = input("Show network processes? (y/n): ").lower() == 'y'
                self.display_processes()
            elif choice == "6":
                break  # Return to the main menu
            else:
                print("Invalid choice. Please try again.")

            input("\nPress Enter to continue...")
            os.system('cls' if os.name == 'nt' else 'clear')


def main():
    monitor = SystemMonitor()
    monitor.run()


if __name__ == "__main__":
    main()