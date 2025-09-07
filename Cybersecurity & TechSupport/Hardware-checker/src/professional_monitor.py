#!/usr/bin/env python3
"""
Professional Hardware Monitor - AIDA64 Style
Real-time hardware monitoring with professional interface
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import psutil
from datetime import datetime

# Import formatting utilities
try:
    from formatting_utils import format_number, format_bytes, format_speed, format_percentage
except ImportError:
    try:
        from .formatting_utils import format_number, format_bytes, format_speed, format_percentage
    except ImportError:
        try:
            import src.formatting_utils as formatting_utils
            format_number = formatting_utils.format_number
            format_bytes = formatting_utils.format_bytes
            format_speed = formatting_utils.format_speed
            format_percentage = formatting_utils.format_percentage
        except ImportError:
            # Fallback formatting functions
            def format_number(value, decimal_places=2, unit=""):
                if value is None:
                    return "N/A"
                try:
                    if abs(value) >= 1000000:
                        return f"{value/1000000:.{decimal_places}f}M{unit}"
                    elif abs(value) >= 1000:
                        return f"{value/1000:.{decimal_places}f}K{unit}"
                    else:
                        return f"{value:.{decimal_places}f}{unit}"
                except:
                    return "N/A"
            
            def format_bytes(bytes_value, decimal_places=2):
                if bytes_value is None or bytes_value < 0:
                    return "N/A"
                try:
                    if bytes_value >= 1024**3:
                        return f"{bytes_value / (1024**3):.{decimal_places}f} GB"
                    elif bytes_value >= 1024**2:
                        return f"{bytes_value / (1024**2):.{decimal_places}f} MB"
                    elif bytes_value >= 1024:
                        return f"{bytes_value / 1024:.{decimal_places}f} KB"
                    else:
                        return f"{bytes_value:.0f} B"
                except:
                    return "N/A"
            
            def format_speed(speed_bps, decimal_places=2):
                return format_bytes(speed_bps, decimal_places).replace(" ", "/s ")
            
            def format_percentage(value, decimal_places=1):
                if value is None:
                    return "N/A"
                try:
                    return f"{value:.{decimal_places}f}%"
                except:
                    return "N/A"

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.animation as animation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False


class ProfessionalHardwareMonitor:
    def __init__(self, parent_notebook):
        self.parent_notebook = parent_notebook
        self.monitoring = False
        self.data_history = {
            'timestamps': [],
            'cpu_usage': [],
            'memory_usage': [],
            'temperatures': [],
            'gpu_usage': [],
            'disk_read': [],
            'disk_write': [],
            'network_sent': [],
            'network_recv': []
        }
        self.max_data_points = 100  # Keep last 100 data points
        
        self.create_professional_monitor()
        
    def create_professional_monitor(self):
        """Create professional monitoring interface"""
        # Main monitoring frame
        self.monitor_frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.monitor_frame, text="📊 Real-Time Monitor")
        
        # Configure grid
        self.monitor_frame.columnconfigure(0, weight=1)
        self.monitor_frame.rowconfigure(1, weight=1)
        
        # Control panel
        self.create_control_panel()
        
        # Main monitoring area
        self.create_monitoring_area()
        
        # Status bar
        self.create_status_bar()
        
    def create_control_panel(self):
        """Create monitoring control panel"""
        control_frame = ttk.LabelFrame(self.monitor_frame, text="Monitoring Controls", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        # Start/Stop buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0, sticky=tk.W)
        
        self.start_button = ttk.Button(button_frame, text="🚀 Start Monitoring", 
                                      command=self.start_monitoring, style="Accent.TButton")
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop Monitoring", 
                                     command=self.stop_monitoring, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=5)
        
        ttk.Button(button_frame, text="📄 Export Data", 
                  command=self.export_data).grid(row=0, column=2, padx=5)
        
        ttk.Button(button_frame, text="🔄 Clear History", 
                  command=self.clear_history).grid(row=0, column=3, padx=5)
        
        # Update interval
        interval_frame = ttk.Frame(control_frame)
        interval_frame.grid(row=0, column=1, sticky=tk.E, padx=(50, 0))
        
        ttk.Label(interval_frame, text="Update Interval:").grid(row=0, column=0, padx=5)
        self.interval_var = tk.StringVar(value="1.0")
        interval_spinbox = ttk.Spinbox(interval_frame, from_=0.5, to=10.0, width=5, 
                                      textvariable=self.interval_var, increment=0.5)
        interval_spinbox.grid(row=0, column=1, padx=5)
        ttk.Label(interval_frame, text="seconds").grid(row=0, column=2, padx=5)
        
    def create_monitoring_area(self):
        """Create main monitoring display area"""
        # Create notebook for different monitoring views
        monitor_notebook = ttk.Notebook(self.monitor_frame)
        monitor_notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)
        
        # Overview tab
        self.create_overview_tab(monitor_notebook)
        
        # Detailed tabs
        self.create_cpu_tab(monitor_notebook)
        self.create_memory_tab(monitor_notebook)
        self.create_disk_tab(monitor_notebook)
        self.create_network_tab(monitor_notebook)
        self.create_gpu_tab(monitor_notebook)
        
        # Temperature tab
        self.create_temperature_tab(monitor_notebook)
        
    def create_overview_tab(self, notebook):
        """Create system overview monitoring tab"""
        overview_frame = ttk.Frame(notebook)
        notebook.add(overview_frame, text="🖥️ System Overview")
        
        # Configure grid
        overview_frame.columnconfigure(0, weight=1)
        overview_frame.columnconfigure(1, weight=1)
        overview_frame.rowconfigure(0, weight=1)
        
        # Real-time values panel
        values_frame = ttk.LabelFrame(overview_frame, text="Current Values", padding="10")
        values_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # System info labels
        self.system_labels = {}
        
        labels = [
            ("🧠 CPU Usage", "cpu_usage"),
            ("💾 Memory Usage", "memory_usage"),
            ("🌡️ CPU Temperature", "cpu_temp"),
            ("🎮 GPU Usage", "gpu_usage"),
            ("🌡️ GPU Temperature", "gpu_temp"),
            ("💿 Disk Read", "disk_read"),
            ("💿 Disk Write", "disk_write"),
            ("🌐 Network Up", "network_up"),
            ("🌐 Network Down", "network_down"),
            ("⚡ CPU Frequency", "cpu_freq"),
            ("💾 Memory Available", "memory_avail"),
            ("🔄 System Uptime", "uptime")
        ]
        
        for i, (label_text, key) in enumerate(labels):
            row = i % 6
            col = 0 if i < 6 else 2
            
            ttk.Label(values_frame, text=label_text, font=('Segoe UI', 10, 'bold')).grid(
                row=row, column=col, sticky=tk.W, padx=5, pady=2)
            
            value_label = ttk.Label(values_frame, text="--", font=('Segoe UI', 12), foreground='blue')
            value_label.grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=2)
            
            self.system_labels[key] = value_label
        
        # Chart panel (if matplotlib available)
        if MATPLOTLIB_AVAILABLE:
            self.create_overview_chart(overview_frame)
        else:
            # Text-based history if no matplotlib
            history_frame = ttk.LabelFrame(overview_frame, text="History (Text)", padding="10")
            history_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
            
            self.history_text = tk.Text(history_frame, height=20, font=('Consolas', 9))
            self.history_text.pack(fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(history_frame, orient='vertical', command=self.history_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.history_text.configure(yscrollcommand=scrollbar.set)
    
    def create_overview_chart(self, parent):
        """Create overview chart with matplotlib"""
        chart_frame = ttk.LabelFrame(parent, text="Performance Charts", padding="10")
        chart_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(10, 6), dpi=80)
        self.fig.patch.set_facecolor('#f0f0f0')
        
        # Create subplots
        self.ax_cpu = self.fig.add_subplot(2, 2, 1)
        self.ax_memory = self.fig.add_subplot(2, 2, 2)
        self.ax_disk = self.fig.add_subplot(2, 2, 3)
        self.ax_network = self.fig.add_subplot(2, 2, 4)
        
        # Configure subplots with professional formatting
        import matplotlib.ticker as ticker
        
        self.ax_cpu.set_title("CPU Usage (%)", fontsize=10, fontweight='bold')
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.grid(True, alpha=0.3)
        self.ax_cpu.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        
        self.ax_memory.set_title("Memory Usage (%)", fontsize=10, fontweight='bold')
        self.ax_memory.set_ylim(0, 100)
        self.ax_memory.grid(True, alpha=0.3)
        self.ax_memory.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        
        self.ax_disk.set_title("Disk I/O (MB/s)", fontsize=10, fontweight='bold')
        self.ax_disk.grid(True, alpha=0.3)
        self.ax_disk.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:.1f}'))
        
        self.ax_network.set_title("Network I/O (KB/s)", fontsize=10, fontweight='bold')
        self.ax_network.grid(True, alpha=0.3)
        self.ax_network.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:.1f}'))
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def create_cpu_tab(self, notebook):
        """Create detailed CPU monitoring tab"""
        cpu_frame = ttk.Frame(notebook)
        notebook.add(cpu_frame, text="🧠 CPU Details")
        
        # Configure frame for scrolling
        cpu_frame.columnconfigure(0, weight=1)
        cpu_frame.rowconfigure(0, weight=1)
        
        # Create scrollable text frame
        text_frame = ttk.Frame(cpu_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        # CPU info and per-core monitoring with scrollbar
        cpu_text = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
        cpu_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=cpu_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        cpu_text.configure(yscrollcommand=scrollbar.set)
        
        self.cpu_detail_text = cpu_text
        
    def create_memory_tab(self, notebook):
        """Create detailed memory monitoring tab"""
        memory_frame = ttk.Frame(notebook)
        notebook.add(memory_frame, text="💾 Memory Details")
        
        # Configure frame for scrolling
        memory_frame.columnconfigure(0, weight=1)
        memory_frame.rowconfigure(0, weight=1)
        
        # Create scrollable text frame
        text_frame = ttk.Frame(memory_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        memory_text = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
        memory_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=memory_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        memory_text.configure(yscrollcommand=scrollbar.set)
        
        self.memory_detail_text = memory_text
        
    def create_disk_tab(self, notebook):
        """Create disk I/O monitoring tab"""
        disk_frame = ttk.Frame(notebook)
        notebook.add(disk_frame, text="💿 Disk I/O")
        
        # Configure frame for scrolling
        disk_frame.columnconfigure(0, weight=1)
        disk_frame.rowconfigure(0, weight=1)
        
        # Create scrollable text frame
        text_frame = ttk.Frame(disk_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        disk_text = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
        disk_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=disk_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        disk_text.configure(yscrollcommand=scrollbar.set)
        
        self.disk_detail_text = disk_text
        
    def create_network_tab(self, notebook):
        """Create network monitoring tab"""
        network_frame = ttk.Frame(notebook)
        notebook.add(network_frame, text="🌐 Network I/O")
        
        # Configure frame for scrolling
        network_frame.columnconfigure(0, weight=1)
        network_frame.rowconfigure(0, weight=1)
        
        # Create scrollable text frame
        text_frame = ttk.Frame(network_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        network_text = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
        network_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=network_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        network_text.configure(yscrollcommand=scrollbar.set)
        
        self.network_detail_text = network_text
        
    def create_gpu_tab(self, notebook):
        """Create GPU monitoring tab"""
        gpu_frame = ttk.Frame(notebook)
        notebook.add(gpu_frame, text="🎮 GPU Details")
        
        # Configure frame for scrolling
        gpu_frame.columnconfigure(0, weight=1)
        gpu_frame.rowconfigure(0, weight=1)
        
        # Create scrollable text frame
        text_frame = ttk.Frame(gpu_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        gpu_text = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
        gpu_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=gpu_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        gpu_text.configure(yscrollcommand=scrollbar.set)
        
        self.gpu_detail_text = gpu_text
        
    def create_temperature_tab(self, notebook):
        """Create temperature monitoring tab"""
        temp_frame = ttk.Frame(notebook)
        notebook.add(temp_frame, text="🌡️ Temperatures")
        
        # Configure frame for scrolling
        temp_frame.columnconfigure(0, weight=1)
        temp_frame.rowconfigure(0, weight=1)
        
        # Create scrollable text frame
        text_frame = ttk.Frame(temp_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        temp_text = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
        temp_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=temp_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        temp_text.configure(yscrollcommand=scrollbar.set)
        
        self.temp_detail_text = temp_text
        
    def create_status_bar(self):
        """Create status bar"""
        self.status_frame = ttk.Frame(self.monitor_frame)
        self.status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready to start monitoring")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.data_points_label = ttk.Label(self.status_frame, text="Data points: 0")
        self.data_points_label.grid(row=0, column=1, sticky=tk.E)
        
    def start_monitoring(self):
        """Start real-time monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.status_label.configure(text="Monitoring active...")
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_label.configure(text="Monitoring stopped")
        
    def monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect data
                self.collect_system_data()
                
                # Update displays
                self.monitor_frame.after(0, self.update_displays)
                
                # Sleep for update interval
                interval = float(self.interval_var.get())
                time.sleep(interval)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                break
    
    def collect_system_data(self):
        """Collect current system data"""
        timestamp = time.time()
        
        # CPU data
        cpu_usage = psutil.cpu_percent(interval=0.1)
        cpu_freq = psutil.cpu_freq()
        
        # Memory data
        memory = psutil.virtual_memory()
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        
        # Network I/O
        network_io = psutil.net_io_counters()
        
        # Temperature (if available)
        try:
            # Try Windows-specific temperature monitoring first
            try:
                from windows_temperature import get_max_temperature
                max_temp = get_max_temperature()
            except ImportError:
                try:
                    from .windows_temperature import get_max_temperature
                    max_temp = get_max_temperature()
                except ImportError:
                    try:
                        import src.windows_temperature as windows_temperature
                        get_max_temperature = windows_temperature.get_max_temperature
                        max_temp = get_max_temperature()
                    except ImportError:
                        # Fallback: try psutil (works on Linux)
                        try:
                            temps = psutil.sensors_temperatures()
                            max_temp = 0
                            if temps:
                                for name, entries in temps.items():
                                    for entry in entries:
                                        if entry.current > max_temp:
                                            max_temp = entry.current
                        except AttributeError:
                            # psutil.sensors_temperatures not available on Windows
                            max_temp = 0
        except Exception as e:
            print(f"Temperature monitoring error: {e}")
            max_temp = 0
            
        # GPU data (if available)
        gpu_usage = 0
        gpu_temp = 0
        if GPUTIL_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_usage = gpu.load * 100
                    gpu_temp = gpu.temperature
            except:
                pass
        
        # Calculate I/O rates
        disk_read_rate = 0
        disk_write_rate = 0
        network_sent_rate = 0
        network_recv_rate = 0
        
        if hasattr(self, 'last_disk_io') and self.last_disk_io and disk_io:
            time_diff = timestamp - self.last_timestamp
            if time_diff > 0:
                disk_read_rate = (disk_io.read_bytes - self.last_disk_io.read_bytes) / time_diff / (1024 * 1024)  # MB/s
                disk_write_rate = (disk_io.write_bytes - self.last_disk_io.write_bytes) / time_diff / (1024 * 1024)  # MB/s
        
        if hasattr(self, 'last_network_io') and self.last_network_io and network_io:
            time_diff = timestamp - self.last_timestamp
            if time_diff > 0:
                network_sent_rate = (network_io.bytes_sent - self.last_network_io.bytes_sent) / time_diff / 1024  # KB/s
                network_recv_rate = (network_io.bytes_recv - self.last_network_io.bytes_recv) / time_diff / 1024  # KB/s
        
        # Store current values
        self.current_data = {
            'timestamp': timestamp,
            'cpu_usage': cpu_usage,
            'cpu_freq': cpu_freq.current if cpu_freq else 0,
            'memory_usage': memory.percent,
            'memory_available': memory.available / (1024**3),  # GB
            'cpu_temp': max_temp,
            'gpu_usage': gpu_usage,
            'gpu_temp': gpu_temp,
            'disk_read': disk_read_rate,
            'disk_write': disk_write_rate,
            'network_sent': network_sent_rate,
            'network_recv': network_recv_rate,
            'uptime': (time.time() - psutil.boot_time()) / 3600  # hours
        }
        
        # Add to history
        self.add_to_history(self.current_data)
        
        # Store for next calculation
        self.last_disk_io = disk_io
        self.last_network_io = network_io
        self.last_timestamp = timestamp
        
    def add_to_history(self, data):
        """Add data point to history"""
        # Add to history
        self.data_history['timestamps'].append(data['timestamp'])
        self.data_history['cpu_usage'].append(data['cpu_usage'])
        self.data_history['memory_usage'].append(data['memory_usage'])
        self.data_history['temperatures'].append(data['cpu_temp'])
        self.data_history['gpu_usage'].append(data['gpu_usage'])
        self.data_history['disk_read'].append(data['disk_read'])
        self.data_history['disk_write'].append(data['disk_write'])
        self.data_history['network_sent'].append(data['network_sent'])
        self.data_history['network_recv'].append(data['network_recv'])
        
        # Keep only last N data points
        for key in self.data_history:
            if len(self.data_history[key]) > self.max_data_points:
                self.data_history[key] = self.data_history[key][-self.max_data_points:]
    
    def update_displays(self):
        """Update all displays with current data"""
        if not hasattr(self, 'current_data'):
            return
            
        data = self.current_data
        
        # Update overview labels
        self.system_labels['cpu_usage'].configure(text=f"{data['cpu_usage']:.1f}%")
        self.system_labels['memory_usage'].configure(text=f"{data['memory_usage']:.1f}%")
        self.system_labels['cpu_temp'].configure(text=f"{data['cpu_temp']:.0f}°C" if data['cpu_temp'] > 0 else "N/A")
        self.system_labels['gpu_usage'].configure(text=f"{data['gpu_usage']:.1f}%" if data['gpu_usage'] > 0 else "N/A")
        self.system_labels['gpu_temp'].configure(text=f"{data['gpu_temp']:.0f}°C" if data['gpu_temp'] > 0 else "N/A")
        self.system_labels['disk_read'].configure(text=f"{data['disk_read']:.1f} MB/s")
        self.system_labels['disk_write'].configure(text=f"{data['disk_write']:.1f} MB/s")
        self.system_labels['network_up'].configure(text=f"{data['network_sent']:.1f} KB/s")
        self.system_labels['network_down'].configure(text=f"{data['network_recv']:.1f} KB/s")
        self.system_labels['cpu_freq'].configure(text=f"{data['cpu_freq']:.0f} MHz")
        self.system_labels['memory_avail'].configure(text=f"{data['memory_available']:.1f} GB")
        self.system_labels['uptime'].configure(text=f"{data['uptime']:.1f} hours")
        
        # Update status
        self.data_points_label.configure(text=f"Data points: {len(self.data_history['timestamps'])}")
        
        # Update charts if available
        if MATPLOTLIB_AVAILABLE and hasattr(self, 'fig'):
            self.update_charts()
            
        # Update detail texts
        self.update_detail_texts()
    
    def update_charts(self):
        """Update matplotlib charts"""
        if len(self.data_history['timestamps']) < 2:
            return
            
        # Clear axes
        self.ax_cpu.clear()
        self.ax_memory.clear()
        self.ax_disk.clear()
        self.ax_network.clear()
        
        # Plot data
        timestamps = self.data_history['timestamps']
        
        # CPU chart
        self.ax_cpu.plot(timestamps, self.data_history['cpu_usage'], 'b-', linewidth=2, label='CPU')
        self.ax_cpu.set_title("CPU Usage (%)", fontsize=10, fontweight='bold')
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.grid(True, alpha=0.3)
        
        # Memory chart
        self.ax_memory.plot(timestamps, self.data_history['memory_usage'], 'g-', linewidth=2, label='Memory')
        self.ax_memory.set_title("Memory Usage (%)", fontsize=10, fontweight='bold')
        self.ax_memory.set_ylim(0, 100)
        self.ax_memory.grid(True, alpha=0.3)
        
        # Disk chart
        self.ax_disk.plot(timestamps, self.data_history['disk_read'], 'r-', linewidth=2, label='Read')
        self.ax_disk.plot(timestamps, self.data_history['disk_write'], 'orange', linewidth=2, label='Write')
        self.ax_disk.set_title("Disk I/O (MB/s)", fontsize=10, fontweight='bold')
        self.ax_disk.legend(fontsize=8)
        self.ax_disk.grid(True, alpha=0.3)
        
        # Network chart
        self.ax_network.plot(timestamps, self.data_history['network_sent'], 'purple', linewidth=2, label='Sent')
        self.ax_network.plot(timestamps, self.data_history['network_recv'], 'teal', linewidth=2, label='Received')
        self.ax_network.set_title("Network I/O (KB/s)", fontsize=10, fontweight='bold')
        self.ax_network.legend(fontsize=8)
        self.ax_network.grid(True, alpha=0.3)
        
        # Refresh canvas
        self.canvas.draw()
    
    def update_detail_texts(self):
        """Update detailed monitoring texts"""
        if not hasattr(self, 'current_data') or not self.current_data:
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # CPU details
        if hasattr(self, 'cpu_detail_text'):
            try:
                cpu_info = f"🧠 CPU MONITORING - {timestamp}\n"
                cpu_info += "=" * 50 + "\n\n"
                cpu_info += f"Overall Usage: {self.current_data['cpu_usage']:.1f}%\n"
                cpu_info += f"Current Frequency: {self.current_data['cpu_freq']:.0f} MHz\n"
                cpu_info += f"Temperature: {self.current_data['cpu_temp']:.0f}°C\n"
                cpu_info += f"Physical Cores: {psutil.cpu_count(logical=False)}\n"
                cpu_info += f"Logical Cores: {psutil.cpu_count(logical=True)}\n"
                
                # CPU frequency details
                try:
                    freq = psutil.cpu_freq()
                    if freq:
                        cpu_info += f"Base Frequency: {freq.min:.0f} MHz\n"
                        cpu_info += f"Max Frequency: {freq.max:.0f} MHz\n"
                except:
                    pass
                
                cpu_info += "\nPer-Core Usage:\n"
                cpu_info += "-" * 20 + "\n"
                
                # Per-core usage
                try:
                    per_core = psutil.cpu_percent(percpu=True, interval=0.1)
                    for i, usage in enumerate(per_core):
                        status = "🔥" if usage > 80 else "🟡" if usage > 60 else "✅"
                        cpu_info += f"Core {i:2d}: {usage:5.1f}% {status}\n"
                except:
                    cpu_info += "Per-core data not available\n"
                
                # CPU times
                try:
                    cpu_times = psutil.cpu_times()
                    cpu_info += f"\nCPU Times:\n"
                    cpu_info += f"User: {cpu_times.user:.1f}s\n"
                    cpu_info += f"System: {cpu_times.system:.1f}s\n"
                    cpu_info += f"Idle: {cpu_times.idle:.1f}s\n"
                except:
                    pass
                
                self.cpu_detail_text.delete('1.0', tk.END)
                self.cpu_detail_text.insert('1.0', cpu_info)
            except Exception as e:
                print(f"CPU detail update error: {e}")
        
        # Memory details
        if hasattr(self, 'memory_detail_text'):
            try:
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                mem_info = f"💾 MEMORY MONITORING - {timestamp}\n"
                mem_info += "=" * 50 + "\n\n"
                mem_info += "Virtual Memory:\n"
                mem_info += f"Total: {memory.total / (1024**3):.2f} GB\n"
                mem_info += f"Available: {memory.available / (1024**3):.2f} GB\n"
                mem_info += f"Used: {memory.used / (1024**3):.2f} GB\n"
                mem_info += f"Usage: {memory.percent:.1f}%\n"
                mem_info += f"Free: {memory.free / (1024**3):.2f} GB\n"
                
                if swap.total > 0:
                    mem_info += f"\nSwap Memory:\n"
                    mem_info += f"Total: {swap.total / (1024**3):.2f} GB\n"
                    mem_info += f"Used: {swap.used / (1024**3):.2f} GB\n"
                    mem_info += f"Free: {swap.free / (1024**3):.2f} GB\n"
                    mem_info += f"Usage: {swap.percent:.1f}%\n"
                else:
                    mem_info += f"\nSwap: Not configured\n"
                
                # Memory status
                if memory.percent > 90:
                    mem_info += f"\n🔴 Memory Status: CRITICAL - Very high usage\n"
                elif memory.percent > 75:
                    mem_info += f"\n🟡 Memory Status: HIGH - Monitor closely\n"
                else:
                    mem_info += f"\n✅ Memory Status: NORMAL\n"
                
                self.memory_detail_text.delete('1.0', tk.END)
                self.memory_detail_text.insert('1.0', mem_info)
            except Exception as e:
                print(f"Memory detail update error: {e}")
        
        # Disk details
        if hasattr(self, 'disk_detail_text'):
            try:
                disk_info = f"💿 DISK I/O MONITORING - {timestamp}\n"
                disk_info += "=" * 50 + "\n\n"
                
                # Disk I/O counters
                try:
                    disk_io = psutil.disk_io_counters()
                    if disk_io:
                        disk_info += "Overall I/O Statistics:\n"
                        disk_info += f"Read Count: {disk_io.read_count:,}\n"
                        disk_info += f"Write Count: {disk_io.write_count:,}\n"
                        disk_info += f"Read Bytes: {disk_io.read_bytes / (1024**3):.2f} GB\n"
                        disk_info += f"Write Bytes: {disk_io.write_bytes / (1024**3):.2f} GB\n"
                        disk_info += f"Read Time: {disk_io.read_time:,} ms\n"
                        disk_info += f"Write Time: {disk_io.write_time:,} ms\n"
                except:
                    disk_info += "I/O statistics not available\n"
                
                # Current rates
                disk_info += f"\nCurrent Rates:\n"
                disk_info += f"Read Speed: {format_number(self.current_data['disk_read'], 2, ' MB/s')}\n"
                disk_info += f"Write Speed: {format_number(self.current_data['disk_write'], 2, ' MB/s')}\n"
                
                # Disk usage by partition - improved error handling
                disk_info += f"\nDisk Usage by Partition:\n"
                disk_info += "-" * 30 + "\n"
                try:
                    partitions = psutil.disk_partitions()
                    if not partitions:
                        disk_info += "No disk partitions detected\n"
                    else:
                        partition_count = 0
                        for partition in partitions:
                            try:
                                # Skip non-disk partitions (network drives, etc.)
                                if not partition.mountpoint or partition.fstype == '':
                                    continue
                                    
                                # Use shutil.disk_usage for better Windows compatibility
                                try:
                                    import shutil
                                    usage = shutil.disk_usage(partition.mountpoint)
                                except ImportError:
                                    usage = psutil.disk_usage(partition.mountpoint)
                                
                                partition_count += 1
                                
                                # Format partition info safely
                                total_gb = usage.total / (1024**3)
                                used_gb = usage.used / (1024**3)
                                free_gb = usage.free / (1024**3)
                                usage_percent = (usage.used / usage.total) * 100
                                
                                disk_info += f"{partition.device} ({partition.fstype})\n"
                                disk_info += f"  Mount: {partition.mountpoint}\n"
                                disk_info += f"  Total: {total_gb:.1f} GB\n"
                                disk_info += f"  Used: {used_gb:.1f} GB ({usage_percent:.1f}%)\n"
                                disk_info += f"  Free: {free_gb:.1f} GB\n"
                                
                                # Status indicators
                                if usage_percent > 90:
                                    disk_info += f"  Status: 🔴 CRITICAL - Low space!\n"
                                elif usage_percent > 80:
                                    disk_info += f"  Status: 🟡 HIGH - Monitor space\n"
                                else:
                                    disk_info += f"  Status: ✅ NORMAL\n"
                                disk_info += "\n"
                                
                            except (PermissionError, OSError) as e:
                                # Skip inaccessible partitions but show count
                                disk_info += f"{partition.device}: Access denied\n"
                                continue
                            except Exception as e:
                                disk_info += f"{partition.device}: Error - {str(e)}\n"
                                continue
                        
                        if partition_count == 0:
                            disk_info += "No accessible disk partitions found\n"
                            
                except Exception as e:
                    disk_info += f"Partition detection error: {str(e)}\n"
                    print(f"Partition detection error: {e}")
                
                self.disk_detail_text.delete('1.0', tk.END)
                self.disk_detail_text.insert('1.0', disk_info)
            except Exception as e:
                print(f"Disk detail update error: {e}")
        
        # Network details
        if hasattr(self, 'network_detail_text'):
            try:
                net_info = f"🌐 NETWORK MONITORING - {timestamp}\n"
                net_info += "=" * 50 + "\n\n"
                
                # Current rates
                net_info += f"Current Network Activity:\n"
                net_info += f"Upload Speed: {format_number(self.current_data['network_sent'], 2, ' KB/s')}\n"
                net_info += f"Download Speed: {format_number(self.current_data['network_recv'], 2, ' KB/s')}\n\n"
                
                # Network I/O statistics
                try:
                    net_io = psutil.net_io_counters()
                    if net_io:
                        net_info += "Overall Network Statistics:\n"
                        net_info += f"Bytes Sent: {net_io.bytes_sent / (1024**2):.1f} MB\n"
                        net_info += f"Bytes Received: {net_io.bytes_recv / (1024**2):.1f} MB\n"
                        net_info += f"Packets Sent: {net_io.packets_sent:,}\n"
                        net_info += f"Packets Received: {net_io.packets_recv:,}\n"
                        net_info += f"Errors In: {net_io.errin}\n"
                        net_info += f"Errors Out: {net_io.errout}\n"
                        net_info += f"Drops In: {net_io.dropin}\n"
                        net_info += f"Drops Out: {net_io.dropout}\n"
                except:
                    net_info += "Network statistics not available\n"
                
                # Network interfaces
                net_info += f"\nNetwork Interfaces:\n"
                net_info += "-" * 25 + "\n"
                try:
                    interfaces = psutil.net_if_addrs()
                    stats = psutil.net_if_stats()
                    
                    for interface, addresses in interfaces.items():
                        net_info += f"{interface}:\n"
                        
                        # Interface status
                        if interface in stats:
                            stat = stats[interface]
                            status = "🟢 UP" if stat.isup else "🔴 DOWN"
                            net_info += f"  Status: {status}\n"
                            if stat.speed > 0:
                                net_info += f"  Speed: {stat.speed} Mbps\n"
                            net_info += f"  MTU: {stat.mtu}\n"
                        
                        # Addresses
                        for addr in addresses:
                            if addr.family.name == 'AF_INET':
                                net_info += f"  IPv4: {addr.address}\n"
                            elif addr.family.name == 'AF_INET6':
                                net_info += f"  IPv6: {addr.address}\n"
                            elif addr.family.name == 'AF_LINK':
                                net_info += f"  MAC: {addr.address}\n"
                        net_info += "\n"
                except:
                    net_info += "Interface information not available\n"
                
                self.network_detail_text.delete('1.0', tk.END)
                self.network_detail_text.insert('1.0', net_info)
            except Exception as e:
                print(f"Network detail update error: {e}")
        
        # GPU details
        if hasattr(self, 'gpu_detail_text'):
            try:
                gpu_info = f"🎮 GPU MONITORING - {timestamp}\n"
                gpu_info += "=" * 50 + "\n\n"
                
                if GPUTIL_AVAILABLE:
                    try:
                        gpus = GPUtil.getGPUs()
                        if gpus:
                            for i, gpu in enumerate(gpus):
                                gpu_info += f"GPU {i}: {gpu.name}\n"
                                gpu_info += f"Load: {gpu.load*100:.1f}%\n"
                                gpu_info += f"Memory Used: {gpu.memoryUsed} MB / {gpu.memoryTotal} MB\n"
                                gpu_info += f"Memory Usage: {(gpu.memoryUsed/gpu.memoryTotal)*100:.1f}%\n"
                                gpu_info += f"Temperature: {gpu.temperature}°C\n"
                                gpu_info += f"Driver Version: {gpu.driver}\n"
                                
                                # GPU status
                                if gpu.load > 0.9:
                                    gpu_info += f"Status: 🔥 VERY HIGH LOAD\n"
                                elif gpu.load > 0.7:
                                    gpu_info += f"Status: 🟡 HIGH LOAD\n"
                                else:
                                    gpu_info += f"Status: ✅ NORMAL\n"
                                
                                if gpu.temperature > 80:
                                    gpu_info += f"Thermal: 🔴 HOT - Monitor closely\n"
                                elif gpu.temperature > 70:
                                    gpu_info += f"Thermal: 🟡 WARM - Normal under load\n"
                                else:
                                    gpu_info += f"Thermal: ✅ COOL\n"
                                
                                gpu_info += "\n"
                        else:
                            gpu_info += "No GPU detected or GPU monitoring not available\n"
                    except Exception as e:
                        gpu_info += f"GPU monitoring error: {e}\n"
                else:
                    gpu_info += "GPUtil library not available\n"
                    gpu_info += "Install with: pip install GPUtil\n"
                
                self.gpu_detail_text.delete('1.0', tk.END)
                self.gpu_detail_text.insert('1.0', gpu_info)
            except Exception as e:
                print(f"GPU detail update error: {e}")
        
        # Temperature details - Windows compatible
        if hasattr(self, 'temp_detail_text'):
            try:
                # Use Windows-specific temperature monitoring
                try:
                    from windows_temperature import get_detailed_temperature_info
                    temp_info = get_detailed_temperature_info()
                except ImportError:
                    try:
                        from .windows_temperature import get_detailed_temperature_info
                        temp_info = get_detailed_temperature_info()
                    except ImportError:
                        try:
                            import src.windows_temperature as windows_temperature
                            get_detailed_temperature_info = windows_temperature.get_detailed_temperature_info
                            temp_info = get_detailed_temperature_info()
                        except ImportError:
                            # Fallback if module not available
                            temp_info = f"🌡️ TEMPERATURE MONITORING - {timestamp}\n"
                            temp_info += "=" * 50 + "\n\n"
                            temp_info += "❌ Windows temperature module not available\n"
                            temp_info += "Temperature monitoring requires Windows-specific drivers\n"
                            temp_info += "Try using hardware manufacturer tools for temperature monitoring\n"
                            
                            if hasattr(self, 'current_data') and self.current_data.get('cpu_temp', 0) > 0:
                                temp_info += f"\nEstimated Temperature: {self.current_data['cpu_temp']:.1f}°C\n"
                
                self.temp_detail_text.delete('1.0', tk.END)
                self.temp_detail_text.insert('1.0', temp_info)
            except Exception as e:
                print(f"Temperature detail update error: {e}")
    
    def clear_history(self):
        """Clear all monitoring history"""
        for key in self.data_history:
            self.data_history[key] = []
        self.data_points_label.configure(text="Data points: 0")
        
        if MATPLOTLIB_AVAILABLE and hasattr(self, 'fig'):
            # Clear charts
            self.ax_cpu.clear()
            self.ax_memory.clear() 
            self.ax_disk.clear()
            self.ax_network.clear()
            self.canvas.draw()
    
    def export_data(self):
        """Export monitoring data to file"""
        if not self.data_history['timestamps']:
            return
            
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Monitoring Data"
            )
            
            if filename:
                import csv
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Header
                    headers = ['Timestamp', 'CPU_Usage_%', 'Memory_Usage_%', 'CPU_Temp_C', 
                              'GPU_Usage_%', 'Disk_Read_MB/s', 'Disk_Write_MB/s', 
                              'Network_Sent_KB/s', 'Network_Recv_KB/s']
                    writer.writerow(headers)
                    
                    # Data
                    for i in range(len(self.data_history['timestamps'])):
                        row = [
                            datetime.fromtimestamp(self.data_history['timestamps'][i]).strftime('%Y-%m-%d %H:%M:%S'),
                            self.data_history['cpu_usage'][i],
                            self.data_history['memory_usage'][i],
                            self.data_history['temperatures'][i],
                            self.data_history['gpu_usage'][i],
                            self.data_history['disk_read'][i],
                            self.data_history['disk_write'][i],
                            self.data_history['network_sent'][i],
                            self.data_history['network_recv'][i]
                        ]
                        writer.writerow(row)
                        
                self.status_label.configure(text=f"Data exported to {filename}")
                
        except Exception as e:
            self.status_label.configure(text=f"Export error: {e}")
