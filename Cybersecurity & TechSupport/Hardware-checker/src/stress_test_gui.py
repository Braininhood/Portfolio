#!/usr/bin/env python3
"""
Stress Test GUI Component
User interface for hardware stress testing functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import os
from datetime import datetime
import json

# Import with multiple fallback strategies for PyInstaller compatibility
try:
    from hardware_stress_tester import HardwareStressTester
except ImportError:
    try:
        from .hardware_stress_tester import HardwareStressTester
    except ImportError:
        try:
            import src.hardware_stress_tester as hardware_stress_tester
            HardwareStressTester = hardware_stress_tester.HardwareStressTester
        except ImportError as e:
            print(f"Could not import HardwareStressTester: {e}")
            raise


class StressTestGUI:
    def __init__(self, parent_notebook):
        self.parent_notebook = parent_notebook
        self.stress_tester = HardwareStressTester()
        self.current_test_thread = None
        self.is_running = False
        
        # Create stress test tab
        self.create_stress_test_tab()
        
    def create_stress_test_tab(self):
        """Create the stress testing tab with improved two-column layout"""
        # Create main frame
        self.stress_frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.stress_frame, text="🔥 Stress Tests")
        
        # Configure responsive two-column grid layout
        self.stress_frame.columnconfigure(0, weight=0, minsize=350)  # Left column - responsive width for controls
        self.stress_frame.columnconfigure(1, weight=2)              # Right column - expandable for results
        self.stress_frame.rowconfigure(0, weight=1)                 # Single row that expands
        
        # Create left panel (controls and progress)
        self.left_panel = ttk.Frame(self.stress_frame)
        self.left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 5), pady=10)
        self.left_panel.columnconfigure(0, weight=1)
        
        # Create right panel (results)
        self.right_panel = ttk.Frame(self.stress_frame)
        self.right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 10), pady=10)
        self.right_panel.columnconfigure(0, weight=1)
        self.right_panel.rowconfigure(0, weight=1)
        
        # Create content for left panel
        self.create_left_panel_content()
        
        # Create content for right panel
        self.create_right_panel_content()
    
    def create_left_panel_content(self):
        """Create content for left panel - controls and progress"""
        # Title
        title_label = ttk.Label(self.left_panel, text="🔥 Hardware Stress Testing", 
                               font=('Segoe UI', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 15), sticky=tk.W)
        
        # Test controls
        self.create_test_controls_left()
        
        # Progress monitoring
        self.create_progress_frame_left()
    
    def create_right_panel_content(self):
        """Create content for right panel - test results"""
        # Results frame
        results_frame = ttk.LabelFrame(self.right_panel, text="📊 Test Results & Professional Analysis", padding="10")
        results_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(0, weight=1)
        
        # Results text area - responsive size
        self.results_text = tk.Text(results_frame, wrap=tk.WORD, height=25, width=60,
                                   font=('Consolas', 9), bg='white', fg='black',
                                   relief=tk.SUNKEN, borderwidth=2)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        results_scrollbar = ttk.Scrollbar(results_frame, orient='vertical', 
                                         command=self.results_text.yview)
        results_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        # Add professional welcome message
        self.show_results_welcome()
        
    def create_test_controls(self):
        """Create test control buttons and options"""
        control_frame = ttk.LabelFrame(self.stress_frame, text="Test Controls", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        # Test type selection
        ttk.Label(control_frame, text="Select Test Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.test_type = tk.StringVar(value="comprehensive")
        test_types = [
            ("🔥 Comprehensive System Test", "comprehensive"),
            ("🧠 CPU Benchmark & Stability", "cpu"),
            ("💾 Memory Performance & Stability", "memory"),
            ("💿 Storage Performance Test", "disk"),
            ("🎮 GPU Performance Test", "gpu"),
            ("🌐 Network Performance Test", "network"),
            ("🔧 Hardware Compatibility Test", "compatibility"),
            ("🌡️ Thermal Stress Test", "thermal")
        ]
        
        for i, (text, value) in enumerate(test_types):
            ttk.Radiobutton(control_frame, text=text, variable=self.test_type, 
                           value=value).grid(row=i+1, column=0, sticky=tk.W, padx=20)
        
        # Duration selection
        ttk.Label(control_frame, text="Test Duration:").grid(row=0, column=1, sticky=tk.W, padx=(50, 0), pady=5)
        
        duration_frame = ttk.Frame(control_frame)
        duration_frame.grid(row=1, column=1, sticky=tk.W, padx=(50, 0))
        
        self.duration_var = tk.StringVar(value="60")
        duration_spinbox = ttk.Spinbox(duration_frame, from_=10, to=3600, width=10, 
                                      textvariable=self.duration_var)
        duration_spinbox.grid(row=0, column=0)
        ttk.Label(duration_frame, text="seconds").grid(row=0, column=1, padx=(5, 0))
        
        # Intensity selection for CPU test
        ttk.Label(control_frame, text="CPU Intensity:").grid(row=2, column=1, sticky=tk.W, padx=(50, 0), pady=5)
        
        self.intensity_var = tk.StringVar(value="high")
        intensity_combo = ttk.Combobox(control_frame, textvariable=self.intensity_var, 
                                      values=["low", "medium", "high", "extreme"], 
                                      state="readonly", width=10)
        intensity_combo.grid(row=3, column=1, sticky=tk.W, padx=(50, 0))
        
        # Memory size for memory test
        ttk.Label(control_frame, text="Memory Size (MB):").grid(row=4, column=1, sticky=tk.W, padx=(50, 0), pady=5)
        
        self.memory_size_var = tk.StringVar(value="1024")
        memory_spinbox = ttk.Spinbox(control_frame, from_=128, to=8192, width=10, 
                                    textvariable=self.memory_size_var)
        memory_spinbox.grid(row=5, column=1, sticky=tk.W, padx=(50, 0))
        
        # Control buttons - better layout
        button_frame = ttk.LabelFrame(control_frame, text="Test Controls", padding="10")
        button_frame.grid(row=10, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))
        
        # Main action buttons
        main_buttons = ttk.Frame(button_frame)
        main_buttons.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.start_button = ttk.Button(main_buttons, text="🚀 Start Test", 
                                      command=self.start_test, style="Accent.TButton", width=15)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.stop_button = ttk.Button(main_buttons, text="🛑 Stop Test", 
                                     command=self.stop_test, state="disabled", width=15)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Utility buttons
        utility_buttons = ttk.Frame(button_frame)
        utility_buttons.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(utility_buttons, text="📊 View Baseline", 
                  command=self.show_baseline, width=15).grid(row=0, column=0, padx=5)
        
        ttk.Button(utility_buttons, text="💾 Save as TXT", 
                  command=self.save_results_txt, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Button(utility_buttons, text="📄 Save as JSON", 
                  command=self.save_results, width=15).grid(row=1, column=1, padx=5, pady=(5,0))
        
        ttk.Button(utility_buttons, text="🔄 Reset Monitor", 
                  command=self.reset_monitoring, width=15).grid(row=0, column=2, padx=5)
        
    def create_progress_frame(self):
        """Create progress monitoring frame"""
        progress_frame = ttk.LabelFrame(self.stress_frame, text="Test Progress", padding="10")
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Status labels
        self.status_label = ttk.Label(progress_frame, text="Ready to start testing", 
                                     font=('Segoe UI', 10, 'bold'))
        self.status_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.time_label = ttk.Label(progress_frame, text="Time: 0:00")
        self.time_label.grid(row=1, column=1, sticky=tk.E, pady=2)
        
        # Real-time monitoring with professional layout
        monitor_frame = ttk.LabelFrame(progress_frame, text="Real-Time System Monitoring", padding="10")
        monitor_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        monitor_frame.columnconfigure(0, weight=1)
        
        # Create monitoring grid
        monitor_grid = ttk.Frame(monitor_frame)
        monitor_grid.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # CPU Monitoring
        ttk.Label(monitor_grid, text="🧠 CPU:", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.cpu_monitor = ttk.Label(monitor_grid, text="0%", font=('Segoe UI', 12, 'bold'), foreground='blue')
        self.cpu_monitor.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Memory Monitoring  
        ttk.Label(monitor_grid, text="💾 RAM:", font=('Segoe UI', 10, 'bold')).grid(row=0, column=2, sticky=tk.W, padx=5)
        self.memory_monitor = ttk.Label(monitor_grid, text="0%", font=('Segoe UI', 12, 'bold'), foreground='green')
        self.memory_monitor.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # Temperature Monitoring
        ttk.Label(monitor_grid, text="🌡️ Temp:", font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.temp_monitor = ttk.Label(monitor_grid, text="--°C", font=('Segoe UI', 12, 'bold'), foreground='red')
        self.temp_monitor.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # GPU Monitoring
        ttk.Label(monitor_grid, text="🎮 GPU:", font=('Segoe UI', 10, 'bold')).grid(row=1, column=2, sticky=tk.W, padx=5)
        self.gpu_monitor = ttk.Label(monitor_grid, text="0%", font=('Segoe UI', 12, 'bold'), foreground='purple')
        self.gpu_monitor.grid(row=1, column=3, sticky=tk.W, padx=5)
        
        # Additional monitoring
        ttk.Label(monitor_grid, text="💿 Disk:", font=('Segoe UI', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, padx=5)
        self.disk_monitor = ttk.Label(monitor_grid, text="0 MB/s", font=('Segoe UI', 12, 'bold'), foreground='orange')
        self.disk_monitor.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(monitor_grid, text="🌐 Network:", font=('Segoe UI', 10, 'bold')).grid(row=2, column=2, sticky=tk.W, padx=5)
        self.network_monitor = ttk.Label(monitor_grid, text="0 KB/s", font=('Segoe UI', 12, 'bold'), foreground='teal')
        self.network_monitor.grid(row=2, column=3, sticky=tk.W, padx=5)
        
    def create_results_frame(self):
        """Create results display frame"""
        results_frame = ttk.LabelFrame(self.stress_frame, text="Test Results", padding="10")
        results_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Results text area
        self.results_text = tk.Text(results_frame, wrap=tk.WORD, height=15, 
                                   font=('Consolas', 9))
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        results_scrollbar = ttk.Scrollbar(results_frame, orient='vertical', 
                                         command=self.results_text.yview)
        results_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        # Initial welcome message - improved
        welcome_text = """🏁 PROFESSIONAL HARDWARE STRESS TESTING - READY
=================================================================

Welcome to enterprise-grade hardware testing! This professional tool 
tests your computer's performance under heavy load with detailed analysis.

📊 AVAILABLE TEST TYPES:
• 🔄 COMPREHENSIVE SYSTEM TEST - Complete system analysis  
• ⚡ CPU BENCHMARK & STABILITY - Processor performance testing
• 💾 MEMORY PERFORMANCE & STABILITY - RAM testing with analysis
• 💿 STORAGE PERFORMANCE TEST - Disk speed and reliability
• 🎮 GPU PERFORMANCE TEST - Graphics card stress testing
• 🌐 NETWORK PERFORMANCE TEST - Network speed and latency
• 🔧 HARDWARE COMPATIBILITY TEST - System compatibility analysis
• 🌡️ THERMAL STRESS TEST - Temperature monitoring and analysis

🛡️ SAFETY FEATURES:
• Real-time temperature monitoring with alerts
• Automatic safety thresholds and warnings
• Professional-grade result analysis
• Detailed performance recommendations

⚡ PROFESSIONAL FEATURES:
• AIDA64-style detailed reporting
• Real-time monitoring with color-coded alerts
• Comprehensive hardware compatibility testing
• Professional result formatting and analysis

🚀 GETTING STARTED:
1. Select test type and configure parameters above
2. Click 'Start Test' to begin professional analysis
3. Monitor real-time results in the monitoring section
4. View detailed analysis in this results area

Ready for professional testing - Select your test type!"""
        
        self.results_text.insert('1.0', welcome_text)
        self.results_text.configure(state='disabled')
        
    def start_test(self):
        """Start the selected stress test"""
        if self.is_running:
            messagebox.showwarning("Test Running", "A test is already running. Please stop it first.")
            return
        
        test_type = self.test_type.get()
        duration = int(self.duration_var.get())
        intensity = self.intensity_var.get()
        memory_size = int(self.memory_size_var.get())
        
        # Confirm with user
        if duration > 300:  # 5 minutes
            result = messagebox.askyesno("Long Test Warning", 
                                       f"You're about to run a {duration} second test. "
                                       "This may put significant stress on your hardware. Continue?")
            if not result:
                return
        
        # Update UI
        self.is_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.progress_var.set(0)
        self.status_label.configure(text=f"Starting {test_type} test...")
        
        # Clear results
        self.results_text.configure(state='normal')
        self.results_text.delete('1.0', tk.END)
        self.results_text.insert('1.0', f"Starting {test_type.upper()} stress test...\n")
        self.results_text.insert(tk.END, f"Duration: {duration} seconds\n")
        if test_type == 'cpu':
            self.results_text.insert(tk.END, f"Intensity: {intensity}\n")
        elif test_type == 'memory':
            self.results_text.insert(tk.END, f"Memory Size: {memory_size} MB\n")
        self.results_text.insert(tk.END, "\n" + "="*50 + "\n\n")
        self.results_text.configure(state='disabled')
        
        # Start test in separate thread
        self.current_test_thread = threading.Thread(
            target=self.run_test_thread, 
            args=(test_type, duration, intensity, memory_size)
        )
        self.current_test_thread.start()
        
        # Start progress monitoring
        self.start_time = time.time()
        self.test_duration = duration
        self.monitor_progress()
        
    def run_test_thread(self, test_type, duration, intensity, memory_size):
        """Run the stress test in a separate thread"""
        try:
            self.stress_tester.is_testing = True
            
            if test_type == "comprehensive":
                results = self.stress_tester.comprehensive_stress_test(duration)
            elif test_type == "cpu":
                results = self.stress_tester.cpu_stress_test(duration, intensity)
            elif test_type == "memory":
                results = self.stress_tester.memory_stress_test(duration, memory_size)
            elif test_type == "disk":
                results = self.stress_tester.disk_stress_test(duration)
            elif test_type == "gpu":
                results = self.stress_tester.gpu_stress_test(duration)
            elif test_type == "network":
                results = self.stress_tester.network_performance_test(duration)
            elif test_type == "compatibility":
                results = self.stress_tester.hardware_compatibility_test(duration)
            elif test_type == "thermal":
                results = self.stress_tester.thermal_stress_test(duration)
            else:
                results = {"error": "Unknown test type"}
            
            # Store results
            self.last_results = results
            
            # Update UI in main thread - fix threading issue
            try:
                self.stress_frame.after(0, self.test_completed, results)
            except RuntimeError:
                # Handle case where GUI is destroyed
                print("GUI destroyed, cannot update test results")
            
        except Exception as e:
            error_results = {"error": str(e), "test_type": test_type}
            self.stress_frame.after(0, self.test_completed, error_results)
    
    def monitor_progress(self):
        """Monitor test progress and update UI"""
        if not self.is_running:
            return
        
        elapsed = time.time() - self.start_time
        progress = min((elapsed / self.test_duration) * 100, 100)
        self.progress_var.set(progress)
        
        # Update time display
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        self.time_label.configure(text=f"Time: {minutes}:{seconds:02d}")
        
        # Update real-time monitoring with comprehensive data
        try:
            import psutil
            
            # CPU Monitoring - comprehensive professional display
            try:
                cpu_usage = psutil.cpu_percent(interval=None)  # Non-blocking call
                cpu_freq = psutil.cpu_freq()
                cpu_count = psutil.cpu_count()
                
                # Update CPU usage
                self.cpu_monitor.configure(text=f"{cpu_usage:.1f}%")
                if cpu_usage > 80:
                    self.cpu_monitor.configure(foreground='red')
                elif cpu_usage > 60:
                    self.cpu_monitor.configure(foreground='orange')
                else:
                    self.cpu_monitor.configure(foreground='blue')
                
                # Update CPU frequency
                if cpu_freq:
                    self.cpu_freq_monitor.configure(text=f"{cpu_freq.current/1000:.2f} GHz")
                
                # Update CPU cores info
                if hasattr(self, 'cpu_cores_monitor'):
                    self.cpu_cores_monitor.configure(text=f"{cpu_count} cores")
                    
            except Exception as e:
                print(f"CPU monitoring error: {e}")
                self.cpu_monitor.configure(text="N/A", foreground='gray')
            
            # Memory Monitoring - enhanced with detailed info
            try:
                memory = psutil.virtual_memory()
                self.memory_monitor.configure(text=f"{memory.percent:.1f}%")
                if memory.percent > 90:
                    self.memory_monitor.configure(foreground='red')
                elif memory.percent > 75:
                    self.memory_monitor.configure(foreground='orange')
                else:
                    self.memory_monitor.configure(foreground='green')
                
                # Update detailed memory info
                if hasattr(self, 'memory_detail_monitor'):
                    used_gb = memory.used / (1024**3)
                    total_gb = memory.total / (1024**3)
                    self.memory_detail_monitor.configure(text=f"{used_gb:.1f} GB / {total_gb:.1f} GB")
                
                if hasattr(self, 'memory_avail_monitor'):
                    avail_gb = memory.available / (1024**3)
                    self.memory_avail_monitor.configure(text=f"{avail_gb:.1f} GB")
                    
            except Exception as e:
                print(f"Memory monitoring error: {e}")
                self.memory_monitor.configure(text="N/A", foreground='gray')
            
            # Temperature Monitoring - Windows compatible
            try:
                # Use Windows-specific temperature monitoring
                try:
                    from windows_temperature import get_max_temperature, format_temperature_display, get_temperature_status
                except ImportError:
                    try:
                        from .windows_temperature import get_max_temperature, format_temperature_display, get_temperature_status
                    except ImportError:
                        import src.windows_temperature as windows_temperature
                        get_max_temperature = windows_temperature.get_max_temperature
                        format_temperature_display = windows_temperature.format_temperature_display
                        get_temperature_status = windows_temperature.get_temperature_status
                
                max_temp = get_max_temperature()
                
                if max_temp > 0:
                    temp_display = format_temperature_display(max_temp, estimated=max_temp < 40)
                    status, color = get_temperature_status(max_temp)
                    
                    self.temp_monitor.configure(text=temp_display, foreground=color)
                    
                    # Update temperature status monitor if available
                    if hasattr(self, 'temp_status_monitor'):
                        self.temp_status_monitor.configure(text=status, foreground=color)
                else:
                    self.temp_monitor.configure(text="N/A", foreground='gray')
                    if hasattr(self, 'temp_status_monitor'):
                        self.temp_status_monitor.configure(text="No Data", foreground='gray')
                        
            except ImportError:
                # Fallback: try estimation from CPU usage
                try:
                    cpu_usage = psutil.cpu_percent(interval=None)
                    if cpu_usage > 0:
                        # Rough estimation: base temp + usage factor
                        estimated_temp = 35 + (cpu_usage * 0.5)
                        self.temp_monitor.configure(text=f"~{estimated_temp:.0f}°C")
                        if hasattr(self, 'temp_status_monitor'):
                            self.temp_status_monitor.configure(text="Estimated", foreground='gray')
                        if estimated_temp > 75:
                            self.temp_monitor.configure(foreground='orange')
                        else:
                            self.temp_monitor.configure(foreground='gray')
                    else:
                        self.temp_monitor.configure(text="N/A", foreground='gray')
                        if hasattr(self, 'temp_status_monitor'):
                            self.temp_status_monitor.configure(text="No Data", foreground='gray')
                except:
                    self.temp_monitor.configure(text="N/A", foreground='gray')
                    if hasattr(self, 'temp_status_monitor'):
                        self.temp_status_monitor.configure(text="Error", foreground='red')
                    
            except Exception as e:
                print(f"Temperature monitoring error: {e}")
                self.temp_monitor.configure(text="N/A", foreground='gray')
            
            # GPU Monitoring - enhanced with memory info
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    self.gpu_monitor.configure(text=f"{gpu.load*100:.0f}%")
                    if gpu.load > 0.8:
                        self.gpu_monitor.configure(foreground='red')
                    elif gpu.load > 0.6:
                        self.gpu_monitor.configure(foreground='orange')
                    else:
                        self.gpu_monitor.configure(foreground='purple')
                    
                    # Update GPU memory if available
                    if hasattr(self, 'gpu_memory_monitor'):
                        memory_used = gpu.memoryUsed
                        memory_total = gpu.memoryTotal
                        memory_percent = (memory_used / memory_total) * 100 if memory_total > 0 else 0
                        self.gpu_memory_monitor.configure(text=f"{memory_used:.0f}/{memory_total:.0f} MB ({memory_percent:.0f}%)")
                else:
                    self.gpu_monitor.configure(text="N/A")
                    if hasattr(self, 'gpu_memory_monitor'):
                        self.gpu_memory_monitor.configure(text="N/A")
            except:
                self.gpu_monitor.configure(text="N/A")
                if hasattr(self, 'gpu_memory_monitor'):
                    self.gpu_memory_monitor.configure(text="N/A")
            
            # Disk I/O Monitoring - enhanced with separate read/write and IOPS
            try:
                if hasattr(self, 'last_disk_io'):
                    current_io = psutil.disk_io_counters()
                    if current_io and self.last_disk_io:
                        time_diff = 1.0  # Update interval
                        read_speed = (current_io.read_bytes - self.last_disk_io.read_bytes) / time_diff / (1024 * 1024)  # MB/s
                        write_speed = (current_io.write_bytes - self.last_disk_io.write_bytes) / time_diff / (1024 * 1024)  # MB/s
                        read_ops = (current_io.read_count - self.last_disk_io.read_count) / time_diff
                        write_ops = (current_io.write_count - self.last_disk_io.write_count) / time_diff
                        
                        # Update professional disk monitors
                        if hasattr(self, 'disk_read_monitor'):
                            self.disk_read_monitor.configure(text=f"{read_speed:.1f} MB/s")
                        if hasattr(self, 'disk_write_monitor'):
                            self.disk_write_monitor.configure(text=f"{write_speed:.1f} MB/s")
                        if hasattr(self, 'disk_iops_monitor'):
                            self.disk_iops_monitor.configure(text=f"{read_ops + write_ops:.0f}")
                        
                        self.last_disk_io = current_io
                    else:
                        self.last_disk_io = psutil.disk_io_counters()
                        if hasattr(self, 'disk_read_monitor'):
                            self.disk_read_monitor.configure(text="0 MB/s")
                        if hasattr(self, 'disk_write_monitor'):
                            self.disk_write_monitor.configure(text="0 MB/s")
                        if hasattr(self, 'disk_iops_monitor'):
                            self.disk_iops_monitor.configure(text="0")
                else:
                    self.last_disk_io = psutil.disk_io_counters()
                    if hasattr(self, 'disk_read_monitor'):
                        self.disk_read_monitor.configure(text="0 MB/s")
                    if hasattr(self, 'disk_write_monitor'):
                        self.disk_write_monitor.configure(text="0 MB/s")
                    if hasattr(self, 'disk_iops_monitor'):
                        self.disk_iops_monitor.configure(text="0")
            except Exception as e:
                print(f"Disk monitoring error: {e}")
                if hasattr(self, 'disk_read_monitor'):
                    self.disk_read_monitor.configure(text="N/A")
                if hasattr(self, 'disk_write_monitor'):
                    self.disk_write_monitor.configure(text="N/A")
                if hasattr(self, 'disk_iops_monitor'):
                    self.disk_iops_monitor.configure(text="N/A")
            
            # Network I/O Monitoring - enhanced with separate upload/download and packets
            try:
                if hasattr(self, 'last_net_io'):
                    current_io = psutil.net_io_counters()
                    if current_io and self.last_net_io:
                        time_diff = 1.0  # Update interval
                        sent_speed = (current_io.bytes_sent - self.last_net_io.bytes_sent) / time_diff / 1024  # KB/s
                        recv_speed = (current_io.bytes_recv - self.last_net_io.bytes_recv) / time_diff / 1024  # KB/s
                        packets_sent = (current_io.packets_sent - self.last_net_io.packets_sent) / time_diff
                        packets_recv = (current_io.packets_recv - self.last_net_io.packets_recv) / time_diff
                        
                        # Update professional network monitors
                        if hasattr(self, 'network_up_monitor'):
                            self.network_up_monitor.configure(text=f"{sent_speed:.1f} KB/s")
                        if hasattr(self, 'network_down_monitor'):
                            self.network_down_monitor.configure(text=f"{recv_speed:.1f} KB/s")
                        if hasattr(self, 'network_packets_monitor'):
                            self.network_packets_monitor.configure(text=f"{packets_sent + packets_recv:.0f}/s")
                        
                        self.last_net_io = current_io
                    else:
                        self.last_net_io = psutil.net_io_counters()
                        if hasattr(self, 'network_up_monitor'):
                            self.network_up_monitor.configure(text="0 KB/s")
                        if hasattr(self, 'network_down_monitor'):
                            self.network_down_monitor.configure(text="0 KB/s")
                        if hasattr(self, 'network_packets_monitor'):
                            self.network_packets_monitor.configure(text="0/s")
                else:
                    self.last_net_io = psutil.net_io_counters()
                    if hasattr(self, 'network_up_monitor'):
                        self.network_up_monitor.configure(text="0 KB/s")
                    if hasattr(self, 'network_down_monitor'):
                        self.network_down_monitor.configure(text="0 KB/s")
                    if hasattr(self, 'network_packets_monitor'):
                        self.network_packets_monitor.configure(text="0/s")
            except Exception as e:
                print(f"Network monitoring error: {e}")
                if hasattr(self, 'network_up_monitor'):
                    self.network_up_monitor.configure(text="N/A")
                if hasattr(self, 'network_down_monitor'):
                    self.network_down_monitor.configure(text="N/A")
                if hasattr(self, 'network_packets_monitor'):
                    self.network_packets_monitor.configure(text="N/A")
                
        except Exception as e:
            print(f"Monitoring error: {e}")
        
        # Schedule next update - increased interval to prevent freezing
        if self.is_running:
            self.stress_frame.after(1000, self.monitor_progress)  # Update every 1 second instead of 0.5
    
    def test_completed(self, results):
        """Handle test completion - improved professional display with save information"""
        self.is_running = False
        self.stress_tester.is_testing = False
        
        # Update UI
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.progress_var.set(100)
        self.status_label.configure(text="✅ Test completed")
        
        # Clear and display results professionally
        self.results_text.configure(state='normal')
        self.results_text.delete('1.0', tk.END)  # Clear previous results
        
        if "error" in results:
            # Professional error display
            error_display = f"🔴 TEST EXECUTION ERROR\n"
            error_display += "=" * 60 + "\n\n"
            error_display += f"Test Type: {results.get('test_type', 'Unknown')}\n"
            error_display += f"Error Details: {results['error']}\n\n"
            error_display += "🔧 TROUBLESHOOTING RECOMMENDATIONS:\n"
            error_display += "• Ensure sufficient system resources\n"
            error_display += "• Check hardware compatibility\n"
            error_display += "• Verify administrative privileges\n"
            error_display += "• Try reducing test duration/intensity\n"
            error_display += "• Close resource-intensive applications\n"
            self.results_text.insert('1.0', error_display)
        else:
            # Professional success display
            try:
                formatted_results = self.stress_tester.format_results(results)
                self.results_text.insert('1.0', formatted_results)
                
                # Add completion timestamp
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                completion_note = f"\n\n✅ TEST COMPLETED SUCCESSFULLY at {timestamp}\n"
                completion_note += "📊 Professional analysis completed - Results ready for review\n"
                
                # Add information about what data is available for saving
                completion_note += "\n" + "=" * 70 + "\n"
                completion_note += "💾 COMPREHENSIVE DATA AVAILABLE FOR EXPORT\n"
                completion_note += "=" * 70 + "\n"
                completion_note += "📋 Complete test methodology and execution details\n"
                completion_note += "📊 Detailed performance metrics and analysis\n"
                completion_note += "🖥️ System baseline and hardware specifications\n"
                completion_note += "🌡️ Temperature monitoring and thermal analysis\n"
                completion_note += "⚠️ Issues identified and professional recommendations\n"
                completion_note += "📈 Real-time monitoring data and statistics\n"
                completion_note += "🔍 Safety analysis and stability assessment\n"
                completion_note += "💡 Expert optimization advice\n"
                completion_note += "\n💾 Use 'Save as TXT' for comprehensive human-readable report\n"
                completion_note += "📄 Use 'Save as JSON' for structured technical data\n"
                completion_note += "=" * 70 + "\n"
                
                self.results_text.insert(tk.END, completion_note)
                
                # Auto-display saved information summary if any results exist
                self._display_current_test_summary(results)
                
            except Exception as e:
                # Fallback formatting
                fallback_display = f"✅ TEST COMPLETED\n"
                fallback_display += "=" * 50 + "\n\n"
                fallback_display += f"Test Results:\n{str(results)}\n\n"
                fallback_display += f"Note: Advanced formatting error: {e}\n"
                self.results_text.insert('1.0', fallback_display)
        
        # Ensure results are visible
        self.results_text.mark_set("insert", "1.0")
        self.results_text.see("insert")
        self.results_text.configure(state='disabled')
        
        # Enhanced completion notifications with save information
        test_type = results.get('test_type', 'Test')
        if "error" not in results:
            # Show detailed completion info with export options
            completion_msg = (f"🎉 {test_type} Analysis Complete!\n\n"
                            f"✅ Professional analysis finished successfully\n"
                            f"📊 Comprehensive data ready for review\n"
                            f"💾 All test steps and details captured\n\n"
                            f"📋 Available Export Options:\n"
                            f"• TXT: Complete human-readable report\n"
                            f"• JSON: Structured data for analysis\n\n"
                            f"🔍 Review results below and save for future reference!")
            
            messagebox.showinfo("🎉 Professional Analysis Complete!", completion_msg)
        else:
            messagebox.showerror("❌ Test Execution Error", 
                               f"Test encountered an error.\n"
                               f"Check results area for troubleshooting steps.")
    
    def _display_current_test_summary(self, results):
        """Display summary of current test information that will be saved"""
        # Add a summary section at the end of results showing what information is captured
        summary_text = f"\n\n📋 CAPTURED TEST INFORMATION SUMMARY\n"
        summary_text += "=" * 50 + "\n"
        
        # Count different types of data available
        data_categories = []
        
        if 'baseline' in results:
            data_categories.append("✅ System baseline measurements")
        
        if 'individual_tests' in results:
            individual = results['individual_tests']
            if 'cpu' in individual:
                data_categories.append("✅ CPU performance and thermal data")
            if 'memory' in individual:
                data_categories.append("✅ Memory usage and stability metrics")
            if 'disk' in individual:
                data_categories.append("✅ Storage performance statistics")
            if 'gpu' in individual:
                data_categories.append("✅ GPU utilization and temperatures")
            if 'network' in individual:
                data_categories.append("✅ Network connectivity and bandwidth")
        
        if 'test_details' in results:
            data_categories.append("✅ Test methodology and configuration")
        
        if 'performance_score' in results:
            data_categories.append("✅ Performance scoring and ratings")
        
        if 'recommendations' in results:
            data_categories.append("✅ Professional recommendations")
        
        if 'what_good' in results or 'what_bad' in results:
            data_categories.append("✅ Issue analysis and positive findings")
        
        # Display the summary
        for category in data_categories:
            summary_text += f"{category}\n"
        
        if not data_categories:
            summary_text += "📊 Basic test execution data\n"
        
        summary_text += f"\n📊 Total data elements: {len(results) if isinstance(results, dict) else 1}\n"
        summary_text += f"🕒 Test duration: {results.get('duration', 'Unknown')} seconds\n"
        summary_text += f"🎯 Test type: {results.get('test_type', 'Unknown')}\n"
        summary_text += f"✅ Status: {results.get('status', 'Unknown').upper()}\n"
        
        # Add this summary to the results display
        self.results_text.configure(state='normal')
        self.results_text.insert(tk.END, summary_text)
        self.results_text.configure(state='disabled')
    
    def stop_test(self):
        """Stop the running test"""
        if not self.is_running:
            return
        
        result = messagebox.askyesno("Stop Test", "Are you sure you want to stop the running test?")
        if result:
            self.stress_tester.stop_all_tests()
            self.is_running = False
            
            # Update UI
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.status_label.configure(text="Test stopped by user")
            
            self.results_text.configure(state='normal')
            self.results_text.insert(tk.END, "\n\n⚠️ Test stopped by user")
            self.results_text.configure(state='disabled')
    
    def show_baseline(self):
        """Show system baseline information"""
        try:
            baseline = self.stress_tester.get_system_baseline()
            
            # Create popup window
            baseline_window = tk.Toplevel(self.stress_frame)
            baseline_window.title("System Baseline")
            baseline_window.geometry("600x400")
            baseline_window.configure(bg="#f0f0f0")
            
            # Text widget for baseline info
            baseline_text = tk.Text(baseline_window, wrap=tk.WORD, font=('Consolas', 10))
            baseline_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Format baseline info
            baseline_info = "SYSTEM BASELINE INFORMATION\n"
            baseline_info += "="*50 + "\n\n"
            baseline_info += f"Timestamp: {baseline['timestamp']}\n\n"
            baseline_info += f"CPU Information:\n"
            baseline_info += f"  Physical Cores: {baseline['cpu_count']}\n"
            baseline_info += f"  Logical Cores: {baseline['cpu_count_logical']}\n"
            baseline_info += f"  Current Frequency: {baseline['cpu_freq']:.0f} MHz\n"
            baseline_info += f"  Idle Usage: {baseline['cpu_usage_idle']:.1f}%\n\n"
            baseline_info += f"Memory Information:\n"
            baseline_info += f"  Total RAM: {baseline['memory_total'] / (1024**3):.2f} GB\n"
            baseline_info += f"  Idle Usage: {baseline['memory_usage_idle']:.1f}%\n\n"
            
            if baseline.get('gpu_info'):
                baseline_info += f"GPU Information:\n"
                for i, gpu in enumerate(baseline['gpu_info']):
                    baseline_info += f"  GPU {i+1}: {gpu['name']}\n"
                    baseline_info += f"    Memory: {gpu['memory_used']}/{gpu['memory_total']} MB\n"
                    baseline_info += f"    Load: {gpu['load']:.1f}%\n"
                    baseline_info += f"    Temperature: {gpu['temperature']:.0f}°C\n"
                baseline_info += "\n"
            
            baseline_info += f"Disk Information:\n"
            for device, info in baseline['disk_usage'].items():
                baseline_info += f"  {device}\n"
                baseline_info += f"    Total: {info['total'] / (1024**3):.1f} GB\n"
                baseline_info += f"    Used: {info['used'] / (1024**3):.1f} GB\n"
                baseline_info += f"    Free: {info['free'] / (1024**3):.1f} GB\n"
            
            baseline_text.insert('1.0', baseline_info)
            baseline_text.configure(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not get baseline information: {e}")
    
    def save_results(self):
        """Save test results to file"""
        if not hasattr(self, 'last_results') or not self.last_results:
            messagebox.showwarning("No Results", "No test results to save. Run a test first.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ],
            initialdir=".",
            title="Save Stress Test Results"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w') as f:
                        json.dump(self.last_results, f, indent=2, default=str)
                else:
                    with open(filename, 'w') as f:
                        f.write("HARDWARE STRESS TEST RESULTS\n")
                        f.write("="*50 + "\n\n")
                        f.write(self.stress_tester.format_results(self.last_results))
                        f.write(f"\n\nGenerated: {datetime.now().isoformat()}")
                
                messagebox.showinfo("Saved", f"Results saved to {filename}")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save results: {e}")
    
    def save_results_txt(self):
        """Save test results to comprehensive TXT file with maximum information"""
        if not hasattr(self, 'last_results') or not self.last_results:
            messagebox.showwarning("No Results", "No test results to save. Run a test first.")
            return
        
        try:
            from tkinter import filedialog
            from datetime import datetime
            import platform
            import os
            
            # Get default filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_type = self.last_results.get('test_type', 'test').replace(' ', '_')
            default_name = f"comprehensive_stress_test_{test_type}_{timestamp}.txt"
            
            # Ask user for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialdir=".",
                title="Save Comprehensive Test Results",
                initialfile=default_name
            )
            
            if filename:
                # Format results as comprehensive readable text
                with open(filename, 'w', encoding='utf-8') as f:
                    # Enhanced professional header with maximum system information
                    f.write("=" * 100 + "\n")
                    f.write("🔬 PC HARDWARE CHECKER - COMPREHENSIVE STRESS TEST REPORT\n")
                    f.write("=" * 100 + "\n")
                    f.write(f"📅 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"🖥️ Computer Name: {os.environ.get('COMPUTERNAME', 'Unknown')}\n")
                    f.write(f"👤 User: {os.environ.get('USERNAME', 'Unknown')}\n")
                    f.write(f"🏢 Domain: {os.environ.get('USERDOMAIN', 'Unknown')}\n")
                    f.write(f"🌐 Machine: {platform.node()}\n")
                    f.write(f"💻 OS: {platform.platform()}\n")
                    f.write(f"🐍 Python: {platform.python_version()}\n")
                    f.write(f"⚙️ Architecture: {platform.architecture()[0]}\n")
                    f.write("=" * 100 + "\n\n")
                    
                    # Test overview with enhanced details
                    f.write("📋 TEST EXECUTION SUMMARY\n")
                    f.write("=" * 50 + "\n")
                    f.write(f"🎯 Test Type: {self.last_results.get('test_type', 'Unknown')}\n")
                    f.write(f"⏱️ Duration: {self.last_results.get('duration', 'Unknown')} seconds\n")
                    f.write(f"✅ Status: {self.last_results.get('status', 'Unknown').upper()}\n")
                    f.write(f"🔧 Intensity: {self.last_results.get('intensity', 'Not specified')}\n")
                    f.write(f"🧮 Threads Used: {self.last_results.get('threads_used', 'Auto-detected')}\n")
                    f.write(f"💾 Memory Target: {self.last_results.get('memory_target_mb', 'N/A')} MB\n")
                    f.write(f"🕒 Start Time: {self.last_results.get('start_time', 'Unknown')}\n")
                    f.write(f"🏁 End Time: {self.last_results.get('end_time', 'Unknown')}\n")
                    f.write("\n")
                    
                    # Get comprehensive formatted results from stress tester
                    if hasattr(self.stress_tester, 'format_results'):
                        formatted_results = self.stress_tester.format_results(self.last_results)
                        f.write(formatted_results)
                    else:
                        # Enhanced fallback formatting with complete data
                        f.write("📊 COMPLETE TEST DATA DUMP\n")
                        f.write("=" * 50 + "\n\n")
                        self._write_complete_test_data(f, self.last_results, "")
                    
                    # Add detailed system information if available
                    f.write("\n\n")
                    f.write("🖥️ DETAILED SYSTEM ENVIRONMENT\n")
                    f.write("=" * 50 + "\n")
                    
                    # Environment variables
                    important_env_vars = [
                        'PROCESSOR_IDENTIFIER', 'PROCESSOR_ARCHITECTURE', 'NUMBER_OF_PROCESSORS',
                        'OS', 'USERPROFILE', 'TEMP', 'SystemRoot', 'ProgramFiles'
                    ]
                    for var in important_env_vars:
                        value = os.environ.get(var, 'Not Available')
                        f.write(f"🔹 {var}: {value}\n")
                    
                    # Memory information from psutil if available
                    try:
                        import psutil
                        f.write(f"\n🧠 SYSTEM MEMORY STATUS:\n")
                        memory = psutil.virtual_memory()
                        f.write(f"🔹 Total Memory: {memory.total / (1024**3):.2f} GB\n")
                        f.write(f"🔹 Available Memory: {memory.available / (1024**3):.2f} GB\n")
                        f.write(f"🔹 Memory Usage: {memory.percent:.1f}%\n")
                        f.write(f"🔹 Used Memory: {memory.used / (1024**3):.2f} GB\n")
                        f.write(f"🔹 Free Memory: {memory.free / (1024**3):.2f} GB\n")
                        
                        f.write(f"\n💿 DISK SPACE STATUS:\n")
                        for partition in psutil.disk_partitions():
                            try:
                                usage = psutil.disk_usage(partition.mountpoint)
                                f.write(f"🔹 Drive {partition.device}: {usage.free / (1024**3):.1f} GB free of {usage.total / (1024**3):.1f} GB\n")
                            except:
                                f.write(f"🔹 Drive {partition.device}: Access denied\n")
                    except ImportError:
                        f.write("🔹 Advanced system info requires psutil library\n")
                    
                    # Footer with comprehensive metadata
                    f.write("\n\n")
                    f.write("=" * 100 + "\n")
                    f.write("📊 REPORT METADATA & TECHNICAL INFORMATION\n")
                    f.write("=" * 100 + "\n")
                    f.write(f"📦 Software: PC Hardware Checker Professional\n")
                    f.write(f"🔬 Test Engine: Hardware Stress Tester v2.0\n")
                    f.write(f"📝 Report Format: Comprehensive TXT Export\n")
                    f.write(f"📏 Report Size: {len(str(self.last_results))} characters of raw data\n")
                    f.write(f"🗂️ Data Structure: {type(self.last_results).__name__}\n")
                    f.write(f"📋 Data Keys: {', '.join(self.last_results.keys()) if isinstance(self.last_results, dict) else 'N/A'}\n")
                    f.write(f"🕒 File Creation: {datetime.now().isoformat()}\n")
                    f.write(f"📁 File Path: {os.path.abspath(filename)}\n")
                    f.write("=" * 100 + "\n")
                    f.write("This comprehensive report contains all available test data,\n")
                    f.write("system information, and analysis results from the stress test.\n")
                    f.write("Report generated by PC Hardware Checker Professional.\n")
                    f.write("=" * 100 + "\n")
                
                messagebox.showinfo("Comprehensive Report Saved", 
                                   f"Complete stress test report saved to:\n{filename}\n\n"
                                   f"📊 Report contains maximum available information\n"
                                   f"📋 File size: {os.path.getsize(filename)} bytes\n"
                                   f"🕒 Generated: {datetime.now().strftime('%H:%M:%S')}")
                
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save comprehensive TXT results: {e}")
    
    def _write_complete_test_data(self, file, data, indent=""):
        """Helper method to write complete test data with all details"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    file.write(f"{indent}🔸 {key}:\n")
                    self._write_complete_test_data(file, value, indent + "    ")
                else:
                    file.write(f"{indent}🔹 {key}: {value}\n")
        elif isinstance(data, list):
            for i, item in enumerate(data, 1):
                if isinstance(item, dict):
                    file.write(f"{indent}📋 Entry {i}:\n")
                    for key, value in item.items():
                        if isinstance(value, (list, dict)):
                            file.write(f"{indent}    🔸 {key}:\n")
                            self._write_complete_test_data(file, value, indent + "        ")
                        else:
                            file.write(f"{indent}    🔹 {key}: {value}\n")
                else:
                    file.write(f"{indent}📌 Item {i}: {item}\n")
        else:
            file.write(f"{indent}{data}\n")
    
    def create_test_controls_left(self):
        """Create test controls for left panel with scrolling"""
        # Create main control frame
        control_frame = ttk.LabelFrame(self.left_panel, text="🎛️ Test Configuration", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(0, weight=1)
        control_frame.rowconfigure(0, weight=1)
        
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(control_frame, height=300)  # Fixed height for scrolling
        scrollbar = ttk.Scrollbar(control_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure column weight for the scrollable frame
        scrollable_frame.columnconfigure(1, weight=1)
        
        # Test type selection
        ttk.Label(scrollable_frame, text="Select Test Type:", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 10), columnspan=2)
        
        self.test_type = tk.StringVar(value="comprehensive")
        test_types = [
            ("🔥 Comprehensive System Test", "comprehensive"),
            ("🧠 CPU Benchmark & Stability", "cpu"),
            ("💾 Memory Performance & Stability", "memory"),
            ("💿 Storage Performance Test", "disk"),
            ("🎮 GPU Performance Test", "gpu"),
            ("🌐 Network Performance Test", "network"),
            ("🔧 Hardware Compatibility Test", "compatibility"),
            ("🌡️ Thermal Stress Test", "thermal")
        ]
        
        for i, (text, value) in enumerate(test_types):
            ttk.Radiobutton(scrollable_frame, text=text, variable=self.test_type, 
                           value=value, width=30).grid(row=i+1, column=0, sticky=tk.W, pady=1, columnspan=2)
        
        # Test parameters
        ttk.Separator(scrollable_frame, orient='horizontal').grid(row=len(test_types)+1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(scrollable_frame, text="Test Parameters:", font=('Segoe UI', 10, 'bold')).grid(row=len(test_types)+2, column=0, sticky=tk.W, columnspan=2)
        
        # Duration
        ttk.Label(scrollable_frame, text="Duration (seconds):").grid(row=len(test_types)+3, column=0, sticky=tk.W, pady=5)
        self.duration_var = tk.StringVar(value="60")
        duration_spinbox = ttk.Spinbox(scrollable_frame, from_=10, to=3600, width=10, textvariable=self.duration_var)
        duration_spinbox.grid(row=len(test_types)+3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # CPU Intensity  
        ttk.Label(scrollable_frame, text="CPU Intensity:").grid(row=len(test_types)+4, column=0, sticky=tk.W, pady=5)
        self.intensity_var = tk.StringVar(value="medium")
        intensity_combo = ttk.Combobox(scrollable_frame, textvariable=self.intensity_var, 
                                      values=["low", "medium", "high"], width=12, state="readonly")
        intensity_combo.grid(row=len(test_types)+4, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Memory Size
        ttk.Label(scrollable_frame, text="Memory Size (MB):").grid(row=len(test_types)+5, column=0, sticky=tk.W, pady=5)
        self.memory_size_var = tk.StringVar(value="1024")
        memory_spinbox = ttk.Spinbox(scrollable_frame, from_=128, to=8192, width=10, textvariable=self.memory_size_var)
        memory_spinbox.grid(row=len(test_types)+5, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Control buttons in 2 columns
        button_frame = ttk.LabelFrame(scrollable_frame, text="Actions", padding="10")
        button_frame.grid(row=len(test_types)+6, column=0, columnspan=2, pady=(15, 0), sticky=(tk.W, tk.E))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # Main action buttons (left column)
        self.start_button = ttk.Button(button_frame, text="🚀 Start Test", 
                                      command=self.start_test, style="Accent.TButton", width=18)
        self.start_button.grid(row=0, column=0, pady=5, padx=(0, 5), sticky=(tk.W, tk.E))
        
        self.stop_button = ttk.Button(button_frame, text="🛑 Stop Test", 
                                     command=self.stop_test, state="disabled", width=18)
        self.stop_button.grid(row=0, column=1, pady=5, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Analysis buttons (second row)
        ttk.Button(button_frame, text="📊 View Baseline", 
                  command=self.show_baseline, width=18).grid(row=1, column=0, pady=5, padx=(0, 5), sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="🔄 Reset Monitor", 
                  command=self.reset_monitoring, width=18).grid(row=1, column=1, pady=5, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Export buttons (third row)
        ttk.Button(button_frame, text="💾 Save as TXT", 
                  command=self.save_results_txt, width=18).grid(row=2, column=0, pady=5, padx=(0, 5), sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="📄 Save as JSON", 
                  command=self.save_results, width=18).grid(row=2, column=1, pady=5, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # File management buttons (fourth row)
        ttk.Button(button_frame, text="📂 View Saved Files", 
                  command=self.browse_saved_files, width=18).grid(row=3, column=0, pady=5, padx=(0, 5), sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="📋 Load Previous", 
                  command=self.load_previous_results, width=18).grid(row=3, column=1, pady=5, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Advanced file operations (fifth row)
        ttk.Button(button_frame, text="🔗 Combine Files", 
                  command=self.combine_multiple_files, width=18).grid(row=4, column=0, pady=5, padx=(0, 5), sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="💾 Export All Formats", 
                  command=self.export_all_formats, width=18).grid(row=4, column=1, pady=5, padx=(5, 0), sticky=(tk.W, tk.E))
    
    def create_progress_frame_left(self):
        """Create progress monitoring for left panel"""
        progress_frame = ttk.LabelFrame(self.left_panel, text="📈 Test Progress & Monitoring", padding="10")
        progress_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        self.left_panel.grid_rowconfigure(2, weight=1)
        
        # Progress bar
        ttk.Label(progress_frame, text="Progress:").grid(row=0, column=0, sticky=tk.W)
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=250)
        self.progress.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Status and time
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.time_label = ttk.Label(progress_frame, text="Time: 0:00")
        self.time_label.grid(row=2, column=1, sticky=tk.E, pady=5)
        
        # Real-time monitoring with professional interface
        ttk.Separator(progress_frame, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        ttk.Label(progress_frame, text="🔬 Professional System Monitoring:", font=('Segoe UI', 9, 'bold')).grid(row=4, column=0, columnspan=2, sticky=tk.W)
        
        # Create scrollable monitoring area
        monitor_container = ttk.Frame(progress_frame)
        monitor_container.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        monitor_container.columnconfigure(0, weight=1)
        monitor_container.rowconfigure(0, weight=1)
        
        # Canvas and scrollbar for scrolling
        monitor_canvas = tk.Canvas(monitor_container, height=150)
        monitor_scrollbar = ttk.Scrollbar(monitor_container, orient="vertical", command=monitor_canvas.yview)
        self.monitor_frame = ttk.Frame(monitor_canvas)
        
        self.monitor_frame.bind(
            "<Configure>",
            lambda e: monitor_canvas.configure(scrollregion=monitor_canvas.bbox("all"))
        )
        
        monitor_canvas.create_window((0, 0), window=self.monitor_frame, anchor="nw")
        monitor_canvas.configure(yscrollcommand=monitor_scrollbar.set)
        
        # Add mouse wheel scrolling
        def _on_monitor_mousewheel(event):
            monitor_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        monitor_canvas.bind("<MouseWheel>", _on_monitor_mousewheel)
        
        monitor_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        monitor_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Professional monitoring display
        self.create_professional_monitors()
    
    def create_professional_monitors(self):
        """Create comprehensive professional monitoring display"""
        # System Overview Section
        overview_frame = ttk.LabelFrame(self.monitor_frame, text="📊 System Overview", padding="5")
        overview_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        overview_frame.columnconfigure(1, weight=1)
        
        # CPU Section
        cpu_frame = ttk.LabelFrame(self.monitor_frame, text="🧠 Processor Monitoring", padding="5")
        cpu_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        cpu_frame.columnconfigure(1, weight=1)
        
        ttk.Label(cpu_frame, text="Usage:").grid(row=0, column=0, sticky=tk.W)
        self.cpu_monitor = ttk.Label(cpu_frame, text="0.0%", foreground='blue', font=('Consolas', 9, 'bold'))
        self.cpu_monitor.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(cpu_frame, text="Frequency:").grid(row=1, column=0, sticky=tk.W)
        self.cpu_freq_monitor = ttk.Label(cpu_frame, text="N/A GHz", foreground='blue', font=('Consolas', 9))
        self.cpu_freq_monitor.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(cpu_frame, text="Cores:").grid(row=2, column=0, sticky=tk.W)
        self.cpu_cores_monitor = ttk.Label(cpu_frame, text="N/A", foreground='blue', font=('Consolas', 9))
        self.cpu_cores_monitor.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Memory Section
        memory_frame = ttk.LabelFrame(self.monitor_frame, text="💾 Memory Monitoring", padding="5")
        memory_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=2)
        memory_frame.columnconfigure(1, weight=1)
        
        ttk.Label(memory_frame, text="Usage:").grid(row=0, column=0, sticky=tk.W)
        self.memory_monitor = ttk.Label(memory_frame, text="0.0%", foreground='green', font=('Consolas', 9, 'bold'))
        self.memory_monitor.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(memory_frame, text="Used/Total:").grid(row=1, column=0, sticky=tk.W)
        self.memory_detail_monitor = ttk.Label(memory_frame, text="0 GB / 0 GB", foreground='green', font=('Consolas', 9))
        self.memory_detail_monitor.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(memory_frame, text="Available:").grid(row=2, column=0, sticky=tk.W)
        self.memory_avail_monitor = ttk.Label(memory_frame, text="0 GB", foreground='green', font=('Consolas', 9))
        self.memory_avail_monitor.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Temperature Section
        temp_frame = ttk.LabelFrame(self.monitor_frame, text="🌡️ Thermal Monitoring", padding="5")
        temp_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=2)
        temp_frame.columnconfigure(1, weight=1)
        
        ttk.Label(temp_frame, text="CPU Temp:").grid(row=0, column=0, sticky=tk.W)
        self.temp_monitor = ttk.Label(temp_frame, text="N/A", foreground='red', font=('Consolas', 9, 'bold'))
        self.temp_monitor.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(temp_frame, text="Status:").grid(row=1, column=0, sticky=tk.W)
        self.temp_status_monitor = ttk.Label(temp_frame, text="Monitoring...", foreground='orange', font=('Consolas', 9))
        self.temp_status_monitor.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # GPU Section
        gpu_frame = ttk.LabelFrame(self.monitor_frame, text="🎮 Graphics Monitoring", padding="5")
        gpu_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=2)
        gpu_frame.columnconfigure(1, weight=1)
        
        ttk.Label(gpu_frame, text="Usage:").grid(row=0, column=0, sticky=tk.W)
        self.gpu_monitor = ttk.Label(gpu_frame, text="N/A", foreground='purple', font=('Consolas', 9, 'bold'))
        self.gpu_monitor.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(gpu_frame, text="Memory:").grid(row=1, column=0, sticky=tk.W)
        self.gpu_memory_monitor = ttk.Label(gpu_frame, text="N/A", foreground='purple', font=('Consolas', 9))
        self.gpu_memory_monitor.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Storage Section
        storage_frame = ttk.LabelFrame(self.monitor_frame, text="💿 Storage I/O Monitoring", padding="5")
        storage_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=2)
        storage_frame.columnconfigure(1, weight=1)
        
        ttk.Label(storage_frame, text="Read:").grid(row=0, column=0, sticky=tk.W)
        self.disk_read_monitor = ttk.Label(storage_frame, text="0 MB/s", foreground='orange', font=('Consolas', 9, 'bold'))
        self.disk_read_monitor.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(storage_frame, text="Write:").grid(row=1, column=0, sticky=tk.W)
        self.disk_write_monitor = ttk.Label(storage_frame, text="0 MB/s", foreground='orange', font=('Consolas', 9, 'bold'))
        self.disk_write_monitor.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(storage_frame, text="IOPS:").grid(row=2, column=0, sticky=tk.W)
        self.disk_iops_monitor = ttk.Label(storage_frame, text="0", foreground='orange', font=('Consolas', 9))
        self.disk_iops_monitor.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Network Section
        network_frame = ttk.LabelFrame(self.monitor_frame, text="🌐 Network I/O Monitoring", padding="5")
        network_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=2)
        network_frame.columnconfigure(1, weight=1)
        
        ttk.Label(network_frame, text="Upload:").grid(row=0, column=0, sticky=tk.W)
        self.network_up_monitor = ttk.Label(network_frame, text="0 KB/s", foreground='teal', font=('Consolas', 9, 'bold'))
        self.network_up_monitor.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(network_frame, text="Download:").grid(row=1, column=0, sticky=tk.W)
        self.network_down_monitor = ttk.Label(network_frame, text="0 KB/s", foreground='teal', font=('Consolas', 9, 'bold'))
        self.network_down_monitor.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(network_frame, text="Packets:").grid(row=2, column=0, sticky=tk.W)
        self.network_packets_monitor = ttk.Label(network_frame, text="0/s", foreground='teal', font=('Consolas', 9))
        self.network_packets_monitor.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Test Progress Section
        test_frame = ttk.LabelFrame(self.monitor_frame, text="🔬 Test Progress Details", padding="5")
        test_frame.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=2)
        test_frame.columnconfigure(1, weight=1)
        
        ttk.Label(test_frame, text="Current Phase:").grid(row=0, column=0, sticky=tk.W)
        self.test_phase_monitor = ttk.Label(test_frame, text="Idle", foreground='navy', font=('Consolas', 9, 'bold'))
        self.test_phase_monitor.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(test_frame, text="Operations:").grid(row=1, column=0, sticky=tk.W)
        self.test_ops_monitor = ttk.Label(test_frame, text="0", foreground='navy', font=('Consolas', 9))
        self.test_ops_monitor.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(test_frame, text="Errors:").grid(row=2, column=0, sticky=tk.W)
        self.test_errors_monitor = ttk.Label(test_frame, text="0", foreground='red', font=('Consolas', 9))
        self.test_errors_monitor.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
    
    def show_results_welcome(self):
        """Show welcome message in results area"""
        welcome_text = """🏁 PROFESSIONAL HARDWARE STRESS TESTING SUITE
===============================================================================

Welcome to enterprise-grade hardware diagnostics! This professional tool provides 
comprehensive testing with detailed analysis, performance metrics, and expert 
recommendations - comparable to AIDA64 and other professional benchmarking tools.

📊 COMPREHENSIVE TEST TYPES:
• 🔄 COMPREHENSIVE SYSTEM TEST - Complete multi-component analysis
• ⚡ CPU BENCHMARK & STABILITY - Deep processor performance & thermal testing
• 💾 MEMORY PERFORMANCE & STABILITY - RAM speed, stability & error checking
• 💿 STORAGE PERFORMANCE TEST - Disk I/O speed, latency & reliability
• 🎮 GPU PERFORMANCE TEST - Graphics processing power & thermal analysis
• 🌐 NETWORK PERFORMANCE TEST - Bandwidth, latency & connectivity analysis
• 🔧 HARDWARE COMPATIBILITY TEST - System component compatibility check
• 🌡️ THERMAL STRESS TEST - Advanced temperature monitoring & analysis

🔬 DETAILED ANALYSIS FOR EACH TEST:
✓ Test Methodology - What exactly is being tested and how
✓ Hardware Information - Detailed component specifications
✓ Performance Metrics - Comprehensive measurements and scoring
✓ What Went Well - Positive performance indicators
✓ Issues Identified - Problems detected with specific details
✓ Professional Recommendations - Expert advice for optimization
✓ Safety Analysis - Thermal and stability monitoring

🛡️ ADVANCED SAFETY FEATURES:
• Real-time temperature monitoring with critical alerts
• Automatic thermal throttling protection
• CPU/GPU overheating prevention
• Memory allocation safety limits
• Background process detection
• Performance variance analysis

⚡ PROFESSIONAL REPORTING FEATURES:
• AIDA64-style comprehensive analysis reports
• Performance scoring with industry-standard ratings
• Stability analysis with variance calculations
• Temperature profiling with thermal maps
• Hardware compatibility assessments
• Bottleneck identification and analysis
• Export to professional TXT and JSON formats

🎛️ CONFIGURABLE TEST PARAMETERS:
• Duration: 10 seconds to 1 hour (adjustable)
• CPU Intensity: Low/Medium/High (controls thread usage)
• Memory Size: 128MB to 8GB (configurable allocation)
• Real-time monitoring: Live performance graphs

📊 REAL-TIME MONITORING:
• CPU Usage: Live percentage with color-coded alerts
• Memory Usage: RAM consumption tracking
• Temperature: Multi-sensor thermal monitoring
• GPU Load: Graphics card utilization
• Disk I/O: Storage read/write speeds (MB/s)
• Network I/O: Data transfer rates (KB/s)

💾 PROFESSIONAL EXPORT OPTIONS:
• TXT Format: Human-readable detailed reports with full analysis
• JSON Format: Structured data for technical analysis
• Timestamped filenames for organized record keeping
• Complete test methodology and results documentation

🚀 QUICK START GUIDE:
1. 🎯 SELECT TEST TYPE: Choose from 8 professional test categories
2. ⚙️ CONFIGURE PARAMETERS: Adjust duration, intensity, and memory size
3. 🚀 START TESTING: Click "Start Test" to begin comprehensive analysis
4. 📈 MONITOR PROGRESS: Watch real-time metrics in the left panel
5. 📊 ANALYZE RESULTS: Review detailed professional analysis here
6. 💾 SAVE REPORTS: Export comprehensive results in TXT or JSON

🎯 PROFESSIONAL USE CASES:
• System performance benchmarking and validation
• Hardware stress testing before deployment
• Thermal performance analysis and cooling optimization
• Component compatibility verification
• Performance bottleneck identification
• System stability testing under load
• Pre-purchase hardware evaluation

Ready for professional-grade hardware analysis!
Configure your test parameters in the left panel and begin testing."""
        
        self.results_text.insert('1.0', welcome_text)
        self.results_text.configure(state='disabled')
    
    def reset_monitoring(self):
        """Reset monitoring displays"""
        try:
            # Reset monitor values
            self.cpu_monitor.configure(text="0%", foreground='blue')
            self.memory_monitor.configure(text="0%", foreground='green')
            self.temp_monitor.configure(text="N/A", foreground='red')
            self.gpu_monitor.configure(text="N/A", foreground='purple')
            self.disk_monitor.configure(text="0 MB/s", foreground='orange')
            self.network_monitor.configure(text="0 KB/s", foreground='teal')
            
            # Reset I/O tracking
            if hasattr(self, 'last_disk_io'):
                delattr(self, 'last_disk_io')
            if hasattr(self, 'last_net_io'):
                delattr(self, 'last_net_io')
                
            messagebox.showinfo("Reset", "Monitoring displays have been reset")
        except Exception as e:
            print(f"Reset error: {e}")
    
    def browse_saved_files(self):
        """Browse and view saved test result files"""
        try:
            import os
            from tkinter import filedialog
            
            # Look for saved files in current directory
            current_dir = "."
            saved_files = []
            
            # Find saved test files
            for file in os.listdir(current_dir):
                if (file.startswith("stress_test_") or file.startswith("comprehensive_stress_test_")) and \
                   (file.endswith(".txt") or file.endswith(".json")):
                    file_path = os.path.join(current_dir, file)
                    file_size = os.path.getsize(file_path)
                    file_time = os.path.getmtime(file_path)
                    saved_files.append((file, file_size, file_time))
            
            if not saved_files:
                messagebox.showinfo("No Saved Files", 
                                   "No saved test result files found in current directory.\n"
                                   "Files are saved with names starting with 'stress_test_' or 'comprehensive_stress_test_'")
                return
            
            # Create a window to show saved files
            files_window = tk.Toplevel(self.stress_frame)
            files_window.title("📂 Saved Test Result Files")
            files_window.geometry("800x600")
            files_window.configure(bg="#f0f0f0")
            
            # Make window resizable and center it
            files_window.resizable(True, True)
            files_window.transient(self.stress_frame)
            
            # Create listbox with file information
            main_frame = ttk.Frame(files_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            ttk.Label(main_frame, text="📋 Saved Test Result Files", 
                     font=('Segoe UI', 14, 'bold')).pack(pady=(0, 10))
            
            # Create treeview for file listing
            columns = ('File Name', 'Size', 'Date Modified', 'Type')
            tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15)
            
            # Configure columns
            tree.heading('File Name', text='📄 File Name')
            tree.heading('Size', text='📏 Size')
            tree.heading('Date Modified', text='📅 Date Modified')
            tree.heading('Type', text='📝 Type')
            
            tree.column('File Name', width=300)
            tree.column('Size', width=100)
            tree.column('Date Modified', width=150)
            tree.column('Type', width=100)
            
            # Add files to tree
            import datetime
            for file, size, mtime in sorted(saved_files, key=lambda x: x[2], reverse=True):
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                date_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                file_type = "TXT Report" if file.endswith('.txt') else "JSON Data"
                tree.insert('', 'end', values=(file, size_str, date_str, file_type))
            
            tree.pack(fill=tk.BOTH, expand=True)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            def open_selected_file():
                selection = tree.selection()
                if selection:
                    item = tree.item(selection[0])
                    filename = item['values'][0]
                    try:
                        import subprocess
                        subprocess.run(['notepad.exe', filename], check=True)
                    except:
                        messagebox.showinfo("Open File", f"Please open manually: {filename}")
            
            def load_selected_file():
                selection = tree.selection()
                if selection:
                    item = tree.item(selection[0])
                    filename = item['values'][0]
                    self.load_test_results_from_file(filename)
                    files_window.destroy()
            
            ttk.Button(button_frame, text="📂 Open in Notepad", 
                      command=open_selected_file).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame, text="📋 Load into Viewer", 
                      command=load_selected_file).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="❌ Close", 
                      command=files_window.destroy).pack(side=tk.RIGHT)
            
        except Exception as e:
            messagebox.showerror("Browse Error", f"Could not browse saved files: {e}")
    
    def load_previous_results(self):
        """Load previous test results from file"""
        try:
            filename = filedialog.askopenfilename(
                title="Load Previous Test Results",
                filetypes=[
                    ("All supported", "*.json;*.txt"),
                    ("JSON files", "*.json"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ],
                initialdir="."
            )
            
            if filename:
                self.load_test_results_from_file(filename)
                
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load test results: {e}")
    
    def load_test_results_from_file(self, filename):
        """Load and display test results from a saved file"""
        try:
            if filename.endswith('.json'):
                # Load JSON data
                with open(filename, 'r', encoding='utf-8') as f:
                    results_data = json.load(f)
                
                # Display the loaded data
                self.results_text.configure(state='normal')
                self.results_text.delete('1.0', tk.END)
                
                # Format and display loaded results
                display_text = f"📂 LOADED TEST RESULTS FROM FILE\n"
                display_text += "=" * 70 + "\n"
                display_text += f"📁 File: {os.path.basename(filename)}\n"
                display_text += f"📅 Loaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                display_text += "=" * 70 + "\n\n"
                
                # Use the stress tester formatter if possible
                if hasattr(self.stress_tester, 'format_results'):
                    formatted_results = self.stress_tester.format_results(results_data)
                    display_text += formatted_results
                else:
                    # Fallback display
                    display_text += "RAW LOADED DATA:\n"
                    display_text += "-" * 30 + "\n\n"
                    display_text += json.dumps(results_data, indent=2)
                
                self.results_text.insert('1.0', display_text)
                self.results_text.configure(state='disabled')
                
                # Store as current results for potential re-saving
                self.last_results = results_data
                
                messagebox.showinfo("Results Loaded", 
                                   f"Successfully loaded test results from:\n{os.path.basename(filename)}")
                
            else:
                # Load TXT file
                with open(filename, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # Display the text file content
                self.results_text.configure(state='normal')
                self.results_text.delete('1.0', tk.END)
                
                display_text = f"📂 LOADED REPORT FROM TEXT FILE\n"
                display_text += "=" * 70 + "\n"
                display_text += f"📁 File: {os.path.basename(filename)}\n"
                display_text += f"📅 Loaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                display_text += "=" * 70 + "\n\n"
                display_text += file_content
                
                self.results_text.insert('1.0', display_text)
                self.results_text.configure(state='disabled')
                
                messagebox.showinfo("Report Loaded", 
                                   f"Successfully loaded report from:\n{os.path.basename(filename)}")
                
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load file {filename}: {e}")
    
    def combine_multiple_files(self):
        """Combine information from multiple JSON and TXT files"""
        try:
            # Select multiple files
            files = filedialog.askopenfilenames(
                title="Select Multiple Test Result Files to Combine",
                filetypes=[
                    ("All Test Files", "*.json;*.txt"),
                    ("JSON files", "*.json"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ],
                initialdir="."
            )
            
            if not files:
                return
            
            combined_data = {
                "combined_analysis": {
                    "total_files": len(files),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "file_sources": []
                },
                "json_data": [],
                "text_reports": []
            }
            
            for file_path in files:
                try:
                    file_info = {
                        "filename": os.path.basename(file_path),
                        "size": os.path.getsize(file_path),
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    }
                    
                    if file_path.endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                        combined_data["json_data"].append({
                            "file_info": file_info,
                            "data": json_data
                        })
                    elif file_path.endswith('.txt'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            text_content = f.read()
                        combined_data["text_reports"].append({
                            "file_info": file_info,
                            "content": text_content
                        })
                    
                    combined_data["combined_analysis"]["file_sources"].append(file_info)
                    
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
                    continue
            
            # Display combined results
            self.results_text.configure(state='normal')
            self.results_text.delete('1.0', tk.END)
            
            display_text = f"🔗 COMBINED TEST RESULTS ANALYSIS\n"
            display_text += "=" * 80 + "\n"
            display_text += f"📅 Combined: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            display_text += f"📁 Total Files: {len(files)}\n"
            display_text += f"📊 JSON Files: {len(combined_data['json_data'])}\n"
            display_text += f"📄 Text Reports: {len(combined_data['text_reports'])}\n"
            display_text += "=" * 80 + "\n\n"
            
            # Summary of JSON data
            if combined_data["json_data"]:
                display_text += "📊 JSON TEST DATA SUMMARY\n"
                display_text += "-" * 50 + "\n"
                for i, json_entry in enumerate(combined_data["json_data"], 1):
                    file_info = json_entry["file_info"]
                    data = json_entry["data"]
                    display_text += f"\n{i}. 📁 {file_info['filename']}\n"
                    display_text += f"   📏 Size: {file_info['size']} bytes\n"
                    display_text += f"   📅 Modified: {file_info['modified']}\n"
                    
                    if 'test_type' in data:
                        display_text += f"   🔬 Test Type: {data['test_type']}\n"
                    if 'duration' in data:
                        display_text += f"   ⏱️ Duration: {data['duration']:.2f} seconds\n"
                    if 'status' in data:
                        display_text += f"   ✅ Status: {data['status']}\n"
                    
                    # Add key metrics summary
                    display_text += "   📈 Key Metrics:\n"
                    for key, value in data.items():
                        if key not in ['test_type', 'duration', 'status'] and not isinstance(value, (list, dict)):
                            display_text += f"      • {key}: {value}\n"
                    display_text += "\n"
            
            # Summary of text reports
            if combined_data["text_reports"]:
                display_text += "\n📄 TEXT REPORTS SUMMARY\n"
                display_text += "-" * 50 + "\n"
                for i, text_entry in enumerate(combined_data["text_reports"], 1):
                    file_info = text_entry["file_info"]
                    content = text_entry["content"]
                    display_text += f"\n{i}. 📁 {file_info['filename']}\n"
                    display_text += f"   📏 Size: {file_info['size']} bytes\n"
                    display_text += f"   📅 Modified: {file_info['modified']}\n"
                    display_text += f"   📝 Content Preview (first 200 chars):\n"
                    preview = content[:200].replace('\n', ' ')
                    display_text += f"      {preview}{'...' if len(content) > 200 else ''}\n\n"
            
            self.results_text.insert('1.0', display_text)
            self.results_text.configure(state='disabled')
            
            # Store combined data for export
            self.combined_results = combined_data
            
            messagebox.showinfo("Files Combined", 
                              f"Successfully combined {len(files)} files!\n"
                              f"JSON files: {len(combined_data['json_data'])}\n"
                              f"Text files: {len(combined_data['text_reports'])}\n\n"
                              f"Use 'Export All Formats' to save the combined analysis.")
            
        except Exception as e:
            messagebox.showerror("Combine Error", f"Could not combine files: {e}")
    
    def export_all_formats(self):
        """Export current results in all available formats (JSON, TXT, CSV)"""
        try:
            # Determine what data to export
            export_data = None
            data_source = ""
            
            if hasattr(self, 'combined_results') and self.combined_results:
                export_data = self.combined_results
                data_source = "combined"
            elif hasattr(self, 'last_results') and self.last_results:
                export_data = self.last_results
                data_source = "test"
            else:
                messagebox.showwarning("No Data", "No test results or combined data available to export.")
                return
            
            # Ask for base filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_base = f"{data_source}_results_{timestamp}"
            
            base_filename = filedialog.asksaveasfilename(
                title="Choose Base Filename for Multi-Format Export",
                defaultextension="",
                initialfile=default_base,
                filetypes=[("Base filename", "*")]
            )
            
            if not base_filename:
                return
            
            # Remove extension if provided
            if '.' in os.path.basename(base_filename):
                base_filename = os.path.splitext(base_filename)[0]
            
            exported_files = []
            
            # Export JSON
            try:
                json_filename = f"{base_filename}.json"
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                exported_files.append(f"📄 {os.path.basename(json_filename)}")
            except Exception as e:
                print(f"JSON export error: {e}")
            
            # Export TXT (comprehensive report)
            try:
                txt_filename = f"{base_filename}.txt"
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    # Write comprehensive header
                    f.write("=" * 100 + "\n")
                    f.write("🔬 COMPREHENSIVE MULTI-FORMAT TEST RESULTS EXPORT\n")
                    f.write("=" * 100 + "\n")
                    f.write(f"📅 Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"📊 Data Source: {data_source.title()} Results\n")
                    f.write(f"🖥️ Computer: {os.environ.get('COMPUTERNAME', 'Unknown')}\n")
                    f.write(f"👤 User: {os.environ.get('USERNAME', 'Unknown')}\n")
                    f.write("=" * 100 + "\n\n")
                    
                    # Write data based on type
                    if data_source == "combined":
                        self._write_combined_data_txt(f, export_data)
                    else:
                        self._write_test_data_txt(f, export_data)
                
                exported_files.append(f"📝 {os.path.basename(txt_filename)}")
            except Exception as e:
                print(f"TXT export error: {e}")
            
            # Export CSV (if data is suitable)
            try:
                csv_filename = f"{base_filename}.csv"
                self._export_csv_format(csv_filename, export_data, data_source)
                exported_files.append(f"📊 {os.path.basename(csv_filename)}")
            except Exception as e:
                print(f"CSV export error: {e}")
            
            if exported_files:
                messagebox.showinfo("Export Complete", 
                                  f"Successfully exported to multiple formats:\n\n" + 
                                  "\n".join(exported_files) + 
                                  f"\n\nBase location: {os.path.dirname(base_filename) or '.'}")
            else:
                messagebox.showerror("Export Failed", "No files were successfully exported.")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export files: {e}")
    
    def _write_combined_data_txt(self, file, data):
        """Write combined data to TXT format"""
        file.write("📊 COMBINED ANALYSIS OVERVIEW\n")
        file.write("-" * 50 + "\n")
        analysis = data.get("combined_analysis", {})
        file.write(f"Total Files Analyzed: {analysis.get('total_files', 0)}\n")
        file.write(f"Analysis Timestamp: {analysis.get('analysis_timestamp', 'Unknown')}\n")
        file.write(f"JSON Data Files: {len(data.get('json_data', []))}\n")
        file.write(f"Text Report Files: {len(data.get('text_reports', []))}\n\n")
        
        # Write JSON data details
        if data.get("json_data"):
            file.write("📄 JSON TEST DATA DETAILS\n")
            file.write("=" * 50 + "\n")
            for i, json_entry in enumerate(data["json_data"], 1):
                file.write(f"\n{i}. {json_entry['file_info']['filename']}\n")
                file.write(f"   Size: {json_entry['file_info']['size']} bytes\n")
                file.write(f"   Modified: {json_entry['file_info']['modified']}\n")
                file.write("   Data:\n")
                self._write_nested_data(file, json_entry["data"], "      ")
                file.write("\n")
        
        # Write text reports
        if data.get("text_reports"):
            file.write("\n📝 TEXT REPORTS CONTENT\n")
            file.write("=" * 50 + "\n")
            for i, text_entry in enumerate(data["text_reports"], 1):
                file.write(f"\n{i}. {text_entry['file_info']['filename']}\n")
                file.write(f"   Size: {text_entry['file_info']['size']} bytes\n")
                file.write(f"   Modified: {text_entry['file_info']['modified']}\n")
                file.write("   Content:\n")
                file.write("   " + "-" * 30 + "\n")
                # Indent each line of content
                for line in text_entry["content"].split('\n'):
                    file.write(f"   {line}\n")
                file.write("   " + "-" * 30 + "\n\n")
    
    def _write_test_data_txt(self, file, data):
        """Write test data to TXT format"""
        file.write("🔬 TEST RESULTS DETAILS\n")
        file.write("-" * 50 + "\n")
        
        # Basic test info
        file.write(f"Test Type: {data.get('test_type', 'Unknown')}\n")
        file.write(f"Duration: {data.get('duration', 'Unknown')} seconds\n")
        file.write(f"Status: {data.get('status', 'Unknown')}\n\n")
        
        # Write all data
        file.write("📊 COMPLETE TEST DATA\n")
        file.write("=" * 50 + "\n")
        self._write_nested_data(file, data, "")
    
    def _write_nested_data(self, file, data, indent=""):
        """Recursively write nested data structures"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    file.write(f"{indent}{key}:\n")
                    self._write_nested_data(file, value, indent + "  ")
                else:
                    file.write(f"{indent}{key}: {value}\n")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    file.write(f"{indent}[{i}]:\n")
                    self._write_nested_data(file, item, indent + "  ")
                else:
                    file.write(f"{indent}[{i}]: {item}\n")
        else:
            file.write(f"{indent}{data}\n")
    
    def _export_csv_format(self, filename, data, data_source):
        """Export data to CSV format"""
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Export Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(['Data Source', data_source.title()])
            writer.writerow([])  # Empty row
            
            if data_source == "combined":
                # Write combined data summary
                writer.writerow(['Category', 'Item', 'Value'])
                analysis = data.get("combined_analysis", {})
                writer.writerow(['Analysis', 'Total Files', analysis.get('total_files', 0)])
                writer.writerow(['Analysis', 'JSON Files', len(data.get('json_data', []))])
                writer.writerow(['Analysis', 'Text Files', len(data.get('text_reports', []))])
                
                # Write file sources
                writer.writerow([])
                writer.writerow(['File Sources'])
                writer.writerow(['Filename', 'Size (bytes)', 'Modified'])
                for file_info in analysis.get('file_sources', []):
                    writer.writerow([file_info.get('filename', ''), 
                                   file_info.get('size', ''), 
                                   file_info.get('modified', '')])
            else:
                # Write test data
                writer.writerow(['Test Property', 'Value'])
                self._write_dict_to_csv(writer, data, '')
    
    def _write_dict_to_csv(self, writer, data, prefix=''):
        """Helper to write dictionary data to CSV"""
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    if isinstance(value, list) and value and not isinstance(value[0], (dict, list)):
                        # Simple list - write as comma-separated values
                        writer.writerow([full_key, ', '.join(map(str, value))])
                    else:
                        # Complex nested structure
                        writer.writerow([full_key, f"[Complex Data - {type(value).__name__}]"])
                else:
                    writer.writerow([full_key, str(value)])
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    writer.writerow([f"{prefix}[{i}]", f"[Complex Data - {type(item).__name__}]"])
                else:
                    writer.writerow([f"{prefix}[{i}]", str(item)])
