"""
GUI Components Module
Modern, user-friendly interface for PC Hardware Checker
Designed for non-technical users
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import sys
import threading
from datetime import datetime
import os
import platform


class ModernGUI:
    def __init__(self, root, hardware_detector):
        self.root = root
        self.detector = hardware_detector
        self.hardware_data = {}
        
        # Configure style
        self.style = ttk.Style()
        self.configure_styles()
        
        # Create main interface
        self.create_main_interface()
        
        # Load initial data
        self.refresh_all_data()
    
    def configure_styles(self):
        """Configure modern styling for the interface"""
        self.style.theme_use('clam')
        
        # Configure colors and fonts
        self.style.configure('Title.TLabel', 
                           font=('Segoe UI', 16, 'bold'),
                           foreground='#2c3e50')
        
        self.style.configure('Heading.TLabel',
                           font=('Segoe UI', 12, 'bold'),
                           foreground='#34495e')
        
        self.style.configure('Info.TLabel',
                           font=('Segoe UI', 10),
                           foreground='#2c3e50')
        
        self.style.configure('Custom.Treeview',
                           background='white',
                           foreground='#2c3e50',
                           font=('Segoe UI', 9))
        
        self.style.configure('Custom.Treeview.Heading',
                           font=('Segoe UI', 10, 'bold'),
                           foreground='#2c3e50')
    
    def create_main_interface(self):
        """Create the main user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="PC Hardware Checker", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)
        
        # Left panel - Navigation
        self.create_navigation_panel(main_frame)
        
        # Right panel - Content
        self.create_content_panel(main_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
    
    def create_navigation_panel(self, parent):
        """Create the navigation panel with menu options"""
        nav_frame = ttk.LabelFrame(parent, text="Hardware Categories", padding="10")
        nav_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Navigation buttons
        nav_buttons = [
            ("🖥️ System Overview", self.show_system_overview),
            ("🧠 Processor (CPU)", self.show_cpu_info),
            ("💾 Memory (RAM)", self.show_memory_info),
            ("💿 Storage Drives", self.show_disk_info),
            ("🎮 Graphics (GPU)", self.show_gpu_info),
            ("🌐 Network", self.show_network_info),
            ("🔧 Motherboard", self.show_motherboard_info),
            ("📊 Real-Time Monitor", self.show_professional_monitor),
            ("🔥 Stress Tests", lambda: self.safe_show_stress_tests()),
            ("📊 Complete Report", self.show_complete_report)
        ]
        
        self.nav_buttons = {}
        for i, (text, command) in enumerate(nav_buttons):
            btn = ttk.Button(nav_frame, text=text, command=command, width=20)
            btn.grid(row=i, column=0, pady=2, sticky=(tk.W, tk.E))
            self.nav_buttons[text] = btn
        
        nav_frame.columnconfigure(0, weight=1)
        
        # Refresh and Export buttons
        ttk.Separator(nav_frame, orient='horizontal').grid(row=len(nav_buttons), column=0, sticky=(tk.W, tk.E), pady=10)
        
        refresh_btn = ttk.Button(nav_frame, text="🔄 Refresh Data", command=self.refresh_all_data)
        refresh_btn.grid(row=len(nav_buttons)+1, column=0, pady=2, sticky=(tk.W, tk.E))
        
        export_btn = ttk.Button(nav_frame, text="💾 Save Report", command=self.export_report)
        export_btn.grid(row=len(nav_buttons)+2, column=0, pady=2, sticky=(tk.W, tk.E))
        
        help_btn = ttk.Button(nav_frame, text="❓ Help", command=self.show_help)
        help_btn.grid(row=len(nav_buttons)+3, column=0, pady=2, sticky=(tk.W, tk.E))
    
    def create_content_panel(self, parent):
        """Create the main content panel"""
        self.content_frame = ttk.LabelFrame(parent, text="Hardware Information", padding="10")
        self.content_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # Create notebook for tabbed content
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initial welcome tab
        self.create_welcome_tab()
        
        # Professional monitoring tab will be created when user clicks the button
    
    def create_status_bar(self, parent):
        """Create status bar"""
        self.status_frame = ttk.Frame(parent)
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready - Click a category to view hardware information")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress = ttk.Progressbar(self.status_frame, mode='indeterminate')
        self.progress.grid(row=0, column=1, sticky=tk.E, padx=(10, 0))
        
        self.status_frame.columnconfigure(0, weight=1)
    
    def create_welcome_tab(self):
        """Create welcome/overview tab"""
        welcome_frame = ttk.Frame(self.notebook)
        self.notebook.add(welcome_frame, text="Welcome")
        
        welcome_text = tk.Text(welcome_frame, wrap=tk.WORD, height=20, font=('Segoe UI', 11))
        welcome_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(welcome_frame, orient='vertical', command=welcome_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        welcome_text.configure(yscrollcommand=scrollbar.set)
        
        welcome_content = """Welcome to PC Hardware Checker!

This tool helps you understand all the hardware components in your computer. It's designed to be easy to use, even if you're not technically minded.

What can you check?

🖥️ System Overview - Basic information about your computer and Windows version
🧠 Processor (CPU) - The "brain" of your computer that does all the calculations
💾 Memory (RAM) - Temporary storage that helps your computer run programs quickly
💿 Storage Drives - Hard drives and SSDs where your files and programs are stored
🎮 Graphics (GPU) - Handles all the visual display and gaming performance
🌐 Network - Information about your internet and network connections
🔧 Motherboard - The main board that connects all components together
📊 Complete Report - See everything at once and save a detailed report

How to use this tool:

1. Click on any category in the left menu to see detailed information
2. Use the "Refresh Data" button to update all information
3. Use "Save Report" to export all information to a file
4. Click "Help" if you need more assistance

The information is presented in simple terms with explanations for non-technical users.

Compatible with all Windows versions including Windows 7, 8, 10, and 11.

Click any category to get started!"""
        
        welcome_text.insert('1.0', welcome_content)
        welcome_text.configure(state='disabled')
        
        welcome_frame.columnconfigure(0, weight=1)
        welcome_frame.rowconfigure(0, weight=1)
    

    def create_stress_testing_tab(self):
        """Create stress testing tab"""
        try:
            # Try both relative and absolute imports
            try:
                from stress_test_gui import StressTestGUI
            except ImportError:
                try:
                    from .stress_test_gui import StressTestGUI
                except ImportError:
                    import src.stress_test_gui as stress_test_gui
                    StressTestGUI = stress_test_gui.StressTestGUI
            
            self.stress_test_gui = StressTestGUI(self.notebook)
        except ImportError as e:
            print(f"Stress testing import error: {e}")  # Debug output
            # Create a placeholder tab if stress testing is not available
            placeholder_frame = ttk.Frame(self.notebook)
            self.notebook.add(placeholder_frame, text="🔥 Stress Tests")
            
            placeholder_text = tk.Text(placeholder_frame, wrap=tk.WORD, height=20, font=('Segoe UI', 11))
            placeholder_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
            
            placeholder_content = f"""Hardware Stress Testing - Import Error

The stress testing module could not be loaded.
Error: {str(e)}

To enable stress testing:
1. Run: install_essential.bat (first)
2. Run: install_stress_simple.bat (second)
3. Restart the application

Or manually install:
pip install numpy py-cpuinfo --user

Stress testing features include:
• CPU stress testing with multiple intensity levels
• Memory stress testing and stability checks
• Disk performance and endurance testing
• GPU stress testing capabilities
• Comprehensive system stress testing
• Real-time monitoring during tests
• Detailed performance reports

Current Python path: {sys.path}"""
            
            placeholder_text.insert('1.0', placeholder_content)
            placeholder_text.configure(state='disabled')
            
            placeholder_frame.columnconfigure(0, weight=1)
            placeholder_frame.rowconfigure(0, weight=1)
        except Exception as e:
            print(f"Unexpected stress testing error: {e}")  # Debug output
            # Create error tab for any other issues
            error_frame = ttk.Frame(self.notebook)
            self.notebook.add(error_frame, text="🔥 Stress Tests")
            
            error_text = tk.Text(error_frame, wrap=tk.WORD, height=20, font=('Segoe UI', 11))
            error_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
            
            error_content = f"""Hardware Stress Testing - Unexpected Error

An unexpected error occurred while setting up stress testing.
Error: {str(e)}
Type: {type(e).__name__}

Please try:
1. Restart the application
2. Check if numpy is installed: python -c "import numpy"
3. Run install_stress_simple.bat

If the problem persists, stress testing may not be compatible with your system configuration."""
            
            error_text.insert('1.0', error_content)
            error_text.configure(state='disabled')
            
            error_frame.columnconfigure(0, weight=1)
            error_frame.rowconfigure(0, weight=1)
    
    def show_system_overview(self):
        """Display system overview information"""
        self.update_status("Loading system information...")
        self.start_progress()
        
        def load_data():
            try:
                system_info = self.detector.get_system_info()
                self.root.after(0, lambda: self.display_system_info(system_info))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Error loading system info: {str(e)}"))
            finally:
                self.root.after(0, self.stop_progress)
        
        threading.Thread(target=load_data, daemon=True).start()
    
    def show_cpu_info(self):
        """Display CPU information"""
        self.update_status("Loading processor information...")
        self.start_progress()
        
        def load_data():
            try:
                cpu_info = self.detector.get_cpu_info()
                self.root.after(0, lambda: self.display_cpu_info(cpu_info))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Error loading CPU info: {str(e)}"))
            finally:
                self.root.after(0, self.stop_progress)
        
        threading.Thread(target=load_data, daemon=True).start()
    
    def show_memory_info(self):
        """Display memory information"""
        self.update_status("Loading memory information...")
        self.start_progress()
        
        def load_data():
            try:
                memory_info = self.detector.get_memory_info()
                self.root.after(0, lambda: self.display_memory_info(memory_info))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Error loading memory info: {str(e)}"))
            finally:
                self.root.after(0, self.stop_progress)
        
        threading.Thread(target=load_data, daemon=True).start()
    
    def show_disk_info(self):
        """Display disk information"""
        self.update_status("Loading storage information...")
        self.start_progress()
        
        def load_data():
            try:
                disk_info = self.detector.get_disk_info()
                self.root.after(0, lambda: self.display_disk_info(disk_info))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Error loading disk info: {str(e)}"))
            finally:
                self.root.after(0, self.stop_progress)
        
        threading.Thread(target=load_data, daemon=True).start()
    
    def show_gpu_info(self):
        """Display GPU information"""
        self.update_status("Loading graphics information...")
        self.start_progress()
        
        def load_data():
            try:
                gpu_info = self.detector.get_gpu_info()
                self.root.after(0, lambda: self.display_gpu_info(gpu_info))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Error loading GPU info: {str(e)}"))
            finally:
                self.root.after(0, self.stop_progress)
        
        threading.Thread(target=load_data, daemon=True).start()
    
    def show_network_info(self):
        """Display network information"""
        self.update_status("Loading network information...")
        self.start_progress()
        
        def load_data():
            try:
                network_info = self.detector.get_network_info()
                self.root.after(0, lambda: self.display_network_info(network_info))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Error loading network info: {str(e)}"))
            finally:
                self.root.after(0, self.stop_progress)
        
        threading.Thread(target=load_data, daemon=True).start()
    
    def show_motherboard_info(self):
        """Display motherboard information"""
        self.update_status("Loading motherboard information...")
        self.start_progress()
        
        def load_data():
            try:
                mb_info = self.detector.get_motherboard_info()
                self.root.after(0, lambda: self.display_motherboard_info(mb_info))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Error loading motherboard info: {str(e)}"))
            finally:
                self.root.after(0, self.stop_progress)
        
        threading.Thread(target=load_data, daemon=True).start()
    
    def show_stress_tests(self):
        """Show stress testing tab"""
        try:
            # Switch to the stress tests tab
            for i in range(self.notebook.index("end")):
                tab_text = self.notebook.tab(i, "text")
                if "Stress Tests" in tab_text or "🔥" in tab_text:
                    self.notebook.select(i)
                    self.update_status("Stress testing tools ready")
                    return
            
            # If tab not found, create it
            print("Stress testing tab not found, recreating...")
            self.create_stress_testing_tab()
            # Try to select it again
            for i in range(self.notebook.index("end")):
                tab_text = self.notebook.tab(i, "text")
                if "Stress Tests" in tab_text or "🔥" in tab_text:
                    self.notebook.select(i)
                    break
            
        except Exception as e:
            print(f"Error showing stress tests: {e}")
            self.update_status("Error accessing stress testing")
    
    def safe_show_stress_tests(self):
        """Show stress testing in main content area like other features"""
        try:
            print("Stress Tests button clicked")  # Debug output
            self.update_status("Loading stress testing...")
            
            # Clear content and show stress testing interface
            self.clear_content()
            
            # Create stress testing tab in main content area
            stress_frame = ttk.Frame(self.notebook)
            self.notebook.add(stress_frame, text="🔥 Hardware Stress Testing")
            
            try:
                # Try to import and create stress testing GUI
                try:
                    from stress_test_gui import StressTestGUI
                except ImportError:
                    try:
                        from .stress_test_gui import StressTestGUI
                    except ImportError:
                        import src.stress_test_gui as stress_test_gui
                        StressTestGUI = stress_test_gui.StressTestGUI
                
                # Create a notebook within the stress frame for the stress testing GUI
                stress_notebook = ttk.Notebook(stress_frame)
                stress_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Create the stress testing GUI
                stress_gui = StressTestGUI(stress_notebook)
                
                print("Stress testing GUI created successfully")
                self.update_status("Stress testing interface loaded")
                
            except ImportError as e:
                print(f"Stress testing import error: {e}")
                self.show_stress_testing_placeholder(stress_frame, str(e))
                
            except Exception as e:
                print(f"Stress testing creation error: {e}")
                self.show_stress_testing_error(stress_frame, str(e))
            
            # Select the stress testing tab
            self.notebook.select(stress_frame)
            
        except Exception as e:
            print(f"Error in safe_show_stress_tests: {e}")
            messagebox.showerror("Error", f"Cannot access stress testing: {str(e)}")
            self.update_status("Error loading stress testing")
    
    def show_stress_testing_placeholder(self, parent, error_msg):
        """Show placeholder when stress testing is not available"""
        placeholder_text = tk.Text(parent, wrap=tk.WORD, height=20, font=('Segoe UI', 11))
        placeholder_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        placeholder_content = f"""Hardware Stress Testing - Not Available

The stress testing module could not be loaded.
Error: {error_msg}

To enable stress testing:
1. Run: install_essential.bat (first)
2. Run: install_stress_simple.bat (second)
3. Restart the application

Or manually install:
pip install numpy py-cpuinfo --user

Stress testing features include:
• CPU stress testing with multiple intensity levels
• Memory stress testing and stability checks
• Disk performance and endurance testing
• GPU stress testing capabilities
• Comprehensive system stress testing
• Real-time monitoring during tests
• Detailed performance reports"""
        
        placeholder_text.insert('1.0', placeholder_content)
        placeholder_text.configure(state='disabled')
    
    def show_stress_testing_error(self, parent, error_msg):
        """Show error when stress testing fails unexpectedly"""
        error_text = tk.Text(parent, wrap=tk.WORD, height=20, font=('Segoe UI', 11))
        error_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        error_content = f"""Hardware Stress Testing - Error

An unexpected error occurred while setting up stress testing.
Error: {error_msg}

Please try:
1. Restart the application
2. Check if numpy is installed: python -c "import numpy"
3. Run install_stress_simple.bat

If the problem persists, stress testing may not be compatible 
with your system configuration."""
        
        error_text.insert('1.0', error_content)
        error_text.configure(state='disabled')
    
    def show_professional_monitor(self):
        """Show the professional real-time monitoring interface"""
        self.clear_content()
        
        # Create or reuse professional monitor tab
        try:
            # Check if we have the professional monitor available
            try:
                from professional_monitor import ProfessionalHardwareMonitor
            except ImportError:
                try:
                    from .professional_monitor import ProfessionalHardwareMonitor
                except ImportError:
                    import src.professional_monitor as professional_monitor
                    ProfessionalHardwareMonitor = professional_monitor.ProfessionalHardwareMonitor
            
            # The ProfessionalHardwareMonitor expects a notebook as parent
            # It will create its own tab, so we pass the main notebook directly
            self.professional_monitor = ProfessionalHardwareMonitor(self.notebook)
            
            # Start monitoring immediately
            self.professional_monitor.start_monitoring()
            
        except ImportError:
            # Fallback if professional monitor not available
            self.show_professional_monitor_placeholder()
        except Exception as e:
            print(f"Error creating professional monitor: {e}")
            self.show_professional_monitor_error(str(e))
    
    def show_professional_monitor_placeholder(self):
        """Show placeholder when professional monitor is not available"""
        placeholder_frame = ttk.Frame(self.notebook)
        self.notebook.add(placeholder_frame, text="📊 Real-Time Monitor")
        
        ttk.Label(placeholder_frame, 
                 text="📊 Real-Time Hardware Monitor\n\n"
                      "Advanced monitoring requires additional packages.\n"
                      "Run: install_stress_testing.bat\n\n"
                      "Features when available:\n"
                      "• Live performance charts\n"
                      "• Real-time system monitoring\n"
                      "• Professional analysis tools",
                 font=('Arial', 12),
                 justify=tk.CENTER).pack(expand=True)
    
    def show_professional_monitor_error(self, error_msg):
        """Show error when professional monitor fails to load"""
        error_frame = ttk.Frame(self.notebook)
        self.notebook.add(error_frame, text="📊 Monitor Error")
        
        ttk.Label(error_frame, 
                 text=f"📊 Real-Time Monitor Error\n\n"
                      f"Error: {error_msg}\n\n"
                      f"Troubleshooting:\n"
                      f"• Run install_stress_testing.bat\n"
                      f"• Check Python environment\n"
                      f"• Restart the application",
                 font=('Arial', 11),
                 justify=tk.CENTER).pack(expand=True)
    
    def show_complete_report(self):
        """Display complete hardware report"""
        self.update_status("Loading complete hardware report...")
        self.start_progress()
        
        def load_data():
            try:
                all_info = self.detector.get_all_hardware_info()
                self.hardware_data = all_info
                self.root.after(0, lambda: self.display_complete_report(all_info))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Error loading complete report: {str(e)}"))
            finally:
                self.root.after(0, self.stop_progress)
        
        threading.Thread(target=load_data, daemon=True).start()
    
    def display_system_info(self, info):
        """Display system information in a formatted way"""
        self.clear_content()
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="System Overview")
        
        # Configure frame for scrolling
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # Create scrollable text widget
        text_widget = self.create_scrollable_text(frame)
        
        content = "💻 SYSTEM OVERVIEW\n"
        content += "=" * 50 + "\n\n"
        content += "This shows basic information about your computer and operating system.\n\n"
        
        for key, value in info.items():
            content += f"📋 {key}: {value}\n"
        
        content += "\n\nWhat does this mean?\n"
        content += "• Computer Name: How your computer identifies itself on networks\n"
        content += "• Operating System: The version of Windows you're running\n"
        content += "• Architecture: Whether your system is 32-bit or 64-bit\n"
        content += "• Processor: Basic information about your CPU\n"
        content += "• System Uptime: How long your computer has been running since last restart\n"
        
        text_widget.insert('1.0', content)
        text_widget.configure(state='disabled')
        
        self.update_status("System overview loaded successfully")
    
    def display_cpu_info(self, info):
        """Display CPU information"""
        self.clear_content()
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Processor (CPU)")
        
        # Configure frame for scrolling
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        text_widget = self.create_scrollable_text(frame)
        
        content = "🧠 PROCESSOR (CPU) INFORMATION\n"
        content += "=" * 50 + "\n\n"
        content += "The CPU is the 'brain' of your computer that processes all instructions.\n\n"
        
        for key, value in info.items():
            if key == "CPU Usage Per Core":
                content += f"📊 {key}:\n"
                for core_info in value:
                    content += f"    {core_info}\n"
            else:
                content += f"⚡ {key}: {value}\n"
        
        content += "\n\nWhat does this mean?\n"
        content += "• Physical/Logical Cores: More cores = better multitasking\n"
        content += "• Frequency (MHz): Higher = faster processing speed\n"
        content += "• CPU Usage: How hard your processor is currently working\n"
        content += "• Cache: Fast temporary storage for the CPU\n"
        content += "• Socket: The connection type on your motherboard\n"
        
        text_widget.insert('1.0', content)
        text_widget.configure(state='disabled')
        
        self.update_status("CPU information loaded successfully")
    
    def display_memory_info(self, info):
        """Display memory information"""
        self.clear_content()
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Memory (RAM)")
        
        # Configure frame for scrolling
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        text_widget = self.create_scrollable_text(frame)
        
        content = "💾 MEMORY (RAM) INFORMATION\n"
        content += "=" * 50 + "\n\n"
        content += "RAM is temporary storage that helps your computer run programs quickly.\n\n"
        
        for key, value in info.items():
            if key == "Memory Modules":
                content += f"🔧 {key}:\n"
                for i, module in enumerate(value, 1):
                    content += f"    Module {i}:\n"
                    for mod_key, mod_value in module.items():
                        content += f"      {mod_key}: {mod_value}\n"
                content += "\n"
            else:
                content += f"📊 {key}: {value}\n"
        
        content += "\n\nWhat does this mean?\n"
        content += "• Total RAM: How much memory your computer has\n"
        content += "• Available/Used: How much memory is currently free/in use\n"
        content += "• RAM Usage %: Percentage of memory currently being used\n"
        content += "• Swap/Virtual Memory: Extra memory space on your hard drive\n"
        content += "• Memory Speed (MHz): How fast your RAM operates\n"
        content += "• Higher RAM = smoother multitasking and faster program loading\n"
        
        text_widget.insert('1.0', content)
        text_widget.configure(state='disabled')
        
        self.update_status("Memory information loaded successfully")
    
    def display_disk_info(self, info):
        """Display disk information"""
        self.clear_content()
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Storage Drives")
        
        # Configure frame for scrolling
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        text_widget = self.create_scrollable_text(frame)
        
        content = "💿 STORAGE DRIVES INFORMATION\n"
        content += "=" * 50 + "\n\n"
        content += "Storage drives are where your files, programs, and operating system are saved.\n\n"
        
        # Check for errors first
        if "Error" in info:
            content += "⚠️ ERROR DETECTED\n"
            content += "-" * 20 + "\n"
            content += f"Error: {info['Error']}\n"
            if "Basic Info" in info:
                content += f"Suggestion: {info['Basic Info']}\n"
            content += "\n"
        
        for section_key, section_value in info.items():
            if section_key in ["Error", "Basic Info"]:
                continue  # Already handled above
                
            content += f"📁 {section_key.upper()}\n"
            content += "-" * 30 + "\n"
            
            if isinstance(section_value, list):
                for i, item in enumerate(section_value, 1):
                    if isinstance(item, dict):
                        if "Error" in item:
                            content += f"  ⚠️ Error: {item['Error']}\n"
                        elif "Message" in item:
                            content += f"  ℹ️ {item['Message']}\n"
                        else:
                            content += f"  Drive {i}:\n"
                            for key, value in item.items():
                                content += f"    {key}: {value}\n"
                    else:
                        content += f"  {item}\n"
                    content += "\n"
            elif isinstance(section_value, dict):
                if "Error" in section_value:
                    content += f"  ⚠️ Error: {section_value['Error']}\n"
                elif "Message" in section_value:
                    content += f"  ℹ️ {section_value['Message']}\n"
                else:
                    for key, value in section_value.items():
                        content += f"  {key}: {value}\n"
            else:
                content += f"  {section_value}\n"
            content += "\n"
        
        content += "What does this mean?\n"
        content += "• Total Size: How much storage space the drive has\n"
        content += "• Used/Free: How much space is occupied/available\n"
        content += "• File System: How the drive organizes data (NTFS, FAT32, etc.)\n"
        content += "• Drive Letters: C:, D:, etc. - how Windows identifies drives\n"
        content += "• Interface: How the drive connects (SATA, NVMe, USB, etc.)\n"
        content += "• SSD drives are faster than traditional hard drives (HDD)\n\n"
        content += "TROUBLESHOOTING:\n"
        content += "• If you see errors, try running as administrator\n"
        content += "• Some drives may require special permissions to access\n"
        content += "• Physical disk info requires WMI (Windows Management)\n"
        
        text_widget.insert('1.0', content)
        text_widget.configure(state='disabled')
        
        self.update_status("Storage information loaded successfully")
    
    def display_gpu_info(self, info):
        """Display GPU information"""
        self.clear_content()
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Graphics (GPU)")
        
        # Configure frame for scrolling
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        text_widget = self.create_scrollable_text(frame)
        
        content = "🎮 GRAPHICS (GPU) INFORMATION\n"
        content += "=" * 50 + "\n\n"
        content += "The GPU handles all visual display, gaming, and graphics processing.\n\n"
        
        for i, gpu in enumerate(info, 1):
            content += f"Graphics Card {i}:\n"
            content += "-" * 20 + "\n"
            for key, value in gpu.items():
                content += f"  🎯 {key}: {value}\n"
            content += "\n"
        
        content += "What does this mean?\n"
        content += "• GPU Name: The model and manufacturer of your graphics card\n"
        content += "• Video Memory: Dedicated memory for graphics (more = better for gaming)\n"
        content += "• GPU Load: How hard your graphics card is currently working\n"
        content += "• Temperature: Current heat level (should stay under 80°C)\n"
        content += "• Driver Version: Software that controls your graphics card\n"
        content += "• Dedicated GPUs are better for gaming than integrated graphics\n"
        
        text_widget.insert('1.0', content)
        text_widget.configure(state='disabled')
        
        self.update_status("Graphics information loaded successfully")
    
    def display_network_info(self, info):
        """Display network information"""
        self.clear_content()
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Network")
        
        # Configure frame for scrolling
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        text_widget = self.create_scrollable_text(frame)
        
        content = "🌐 NETWORK INFORMATION\n"
        content += "=" * 50 + "\n\n"
        content += "Network information shows how your computer connects to the internet and other devices.\n\n"
        
        for key, value in info.items():
            if key == "Interfaces":
                content += f"🔌 Network {key}:\n"
                content += "-" * 30 + "\n"
                for interface in value:
                    interface_name = interface.get('Interface', 'Unknown')
                    content += f"📡 {interface_name}\n"
                    
                    # Status and connection info
                    status = interface.get('Status', 'Unknown')
                    speed = interface.get('Speed', 'Unknown')
                    content += f"   Status: {status}\n"
                    if speed != 'Unknown':
                        content += f"   Speed: {speed}\n"
                    
                    # MAC Address
                    mac = interface.get('MAC_Address', '')
                    if mac:
                        content += f"   MAC Address: {mac}\n"
                    
                    # IPv4 Addresses
                    ipv4_addresses = interface.get('IPv4_Addresses', [])
                    if ipv4_addresses:
                        content += "   IPv4 Addresses:\n"
                        for addr in ipv4_addresses:
                            ip = addr.get('IP', 'Unknown')
                            netmask = addr.get('Netmask', '')
                            content += f"     • {ip}"
                            if netmask:
                                content += f" (Netmask: {netmask})"
                            content += "\n"
                    
                    # IPv6 Addresses
                    ipv6_addresses = interface.get('IPv6_Addresses', [])
                    if ipv6_addresses:
                        content += "   IPv6 Addresses:\n"
                        for addr in ipv6_addresses:
                            ip = addr.get('IP', 'Unknown')
                            content += f"     • {ip}\n"
                    
                    content += "\n"
                    
            elif key == "Network I/O Statistics":
                content += f"📊 {key}:\n"
                content += "-" * 30 + "\n"
                for stat_key, stat_value in value.items():
                    formatted_key = stat_key.replace('_', ' ').title()
                    content += f"📈 {formatted_key}: {stat_value}\n"
                content += "\n"
            else:
                content += f"🏠 {key}: {value}\n"
        
        content += "\nWhat does this mean?\n"
        content += "• Hostname: Your computer's name on the network\n"
        content += "• Network Interfaces: Different ways your computer can connect (WiFi, Ethernet, etc.)\n"
        content += "• IP Addresses: Unique numbers that identify your computer on networks\n"
        content += "• Bytes Sent/Received: How much data has been transferred\n"
        content += "• Ethernet = wired connection, WiFi = wireless connection\n"
        
        text_widget.insert('1.0', content)
        text_widget.configure(state='disabled')
        
        self.update_status("Network information loaded successfully")
    
    def display_motherboard_info(self, info):
        """Display motherboard information"""
        self.clear_content()
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Motherboard")
        
        # Configure frame for scrolling
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        text_widget = self.create_scrollable_text(frame)
        
        content = "🔧 MOTHERBOARD INFORMATION\n"
        content += "=" * 50 + "\n\n"
        content += "The motherboard is the main circuit board that connects all your computer components.\n\n"
        
        # Check for errors and messages first
        has_error = False
        for key, value in info.items():
            if "Error" in key or key == "Error":
                content += f"⚠️ {key}: {value}\n"
                has_error = True
            elif key in ["Message", "WMI Status", "Suggestion", "Alternative"]:
                content += f"ℹ️ {key}: {value}\n"
            else:
                content += f"⚙️ {key}: {value}\n"
        
        content += "\n\nWhat does this mean?\n"
        content += "• Manufacturer: The company that made your motherboard\n"
        content += "• Product/Model: The specific motherboard model\n"
        content += "• BIOS: Basic Input/Output System - firmware that starts your computer\n"
        content += "• BIOS Version: The version of your system firmware\n"
        content += "• Serial Number: Unique identifier for your motherboard\n"
        content += "• System Manufacturer/Model: Overall computer brand and model\n"
        content += "• The motherboard determines what components you can upgrade\n\n"
        
        if has_error:
            content += "TROUBLESHOOTING:\n"
            content += "• Try running the application as administrator\n"
            content += "• WMI (Windows Management Instrumentation) may be disabled\n"
            content += "• Check Windows Services - ensure 'Windows Management Instrumentation' is running\n"
            content += "• Some corporate systems restrict WMI access\n"
            content += "• Alternative: Open 'System Information' (msinfo32) or Device Manager\n"
            content += "• Alternative: Check BIOS setup during computer startup\n"
        
        text_widget.insert('1.0', content)
        text_widget.configure(state='disabled')
        
        status_msg = "Motherboard information loaded"
        if has_error:
            status_msg += " (with limitations - see troubleshooting tips)"
        self.update_status(status_msg)
    
    def display_complete_report(self, all_info):
        """Display complete hardware report"""
        self.clear_content()
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Complete Report")
        
        # Configure frame for scrolling
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        text_widget = self.create_scrollable_text(frame)
        
        content = "📊 COMPLETE HARDWARE REPORT\n"
        content += "=" * 60 + "\n"
        content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "=" * 60 + "\n\n"
        
        for section_name, section_data in all_info.items():
            content += f"\n{section_name.upper()}\n"
            content += "-" * len(section_name) + "\n"
            
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    if isinstance(value, list):
                        content += f"{key}:\n"
                        for item in value:
                            if isinstance(item, dict):
                                for sub_key, sub_value in item.items():
                                    content += f"  {sub_key}: {sub_value}\n"
                            else:
                                content += f"  {item}\n"
                    else:
                        content += f"{key}: {value}\n"
            elif isinstance(section_data, list):
                for i, item in enumerate(section_data, 1):
                    content += f"Item {i}:\n"
                    if isinstance(item, dict):
                        for key, value in item.items():
                            content += f"  {key}: {value}\n"
                    else:
                        content += f"  {item}\n"
            content += "\n"
        
        text_widget.insert('1.0', content)
        text_widget.configure(state='disabled')
        
        self.update_status("Complete report loaded successfully")
    
    def create_scrollable_text(self, parent):
        """Create a scrollable text widget"""
        text_frame = ttk.Frame(parent)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10), 
                             bg='white', fg='#2c3e50')
        text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        return text_widget
    
    def clear_content(self):
        """Clear the content notebook"""
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
    
    def refresh_all_data(self):
        """Refresh all hardware data"""
        self.update_status("Refreshing all hardware data...")
        self.start_progress()
        
        def load_data():
            try:
                self.hardware_data = self.detector.get_all_hardware_info()
                self.root.after(0, lambda: self.update_status("All data refreshed successfully"))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Error refreshing data: {str(e)}"))
            finally:
                self.root.after(0, self.stop_progress)
        
        threading.Thread(target=load_data, daemon=True).start()
    
    def export_report(self):
        """Export hardware report to file with maximum information"""
        if not self.hardware_data:
            self.hardware_data = self.detector.get_all_hardware_info()
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ],
            title="Save Hardware Report"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.hardware_data, f, indent=2, default=str)
                else:
                    # Enhanced TXT export with maximum information
                    with open(filename, 'w', encoding='utf-8') as f:
                        # Professional header
                        f.write("=" * 80 + "\n")
                        f.write("🔬 PC HARDWARE CHECKER - COMPREHENSIVE SYSTEM REPORT\n")
                        f.write("=" * 80 + "\n")
                        f.write(f"📅 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"🖥️ Computer Name: {os.environ.get('COMPUTERNAME', 'Unknown')}\n")
                        f.write(f"👤 User: {os.environ.get('USERNAME', 'Unknown')}\n")
                        f.write(f"🏢 Domain: {os.environ.get('USERDOMAIN', 'Unknown')}\n")
                        f.write("=" * 80 + "\n\n")
                        
                        # Write each section with enhanced formatting
                        for section_name, section_data in self.hardware_data.items():
                            f.write(f"📊 {section_name.upper()}\n")
                            f.write("=" * (len(section_name) + 4) + "\n\n")
                            
                            if isinstance(section_data, dict):
                                # Handle dictionary data with proper formatting
                                for key, value in section_data.items():
                                    if isinstance(value, (list, dict)):
                                        f.write(f"🔸 {key}:\n")
                                        self._write_complex_data(f, value, indent="    ")
                                    else:
                                        f.write(f"🔹 {key}: {value}\n")
                            elif isinstance(section_data, list):
                                # Handle list data
                                for i, item in enumerate(section_data, 1):
                                    f.write(f"📋 Item {i}:\n")
                                    if isinstance(item, dict):
                                        for key, value in item.items():
                                            f.write(f"    🔹 {key}: {value}\n")
                                    else:
                                        f.write(f"    {item}\n")
                            else:
                                f.write(f"{section_data}\n")
                            f.write("\n" + "-" * 60 + "\n\n")
                        
                        # Add footer with additional information
                        f.write("=" * 80 + "\n")
                        f.write("📊 REPORT SUMMARY & METADATA\n")
                        f.write("=" * 80 + "\n")
                        f.write(f"📦 Software Version: PC Hardware Checker Professional\n")
                        f.write(f"💻 Operating System: {platform.platform()}\n")
                        f.write(f"🐍 Python Version: {platform.python_version()}\n")
                        f.write(f"⚙️ Architecture: {platform.architecture()[0]}\n")
                        f.write(f"🔧 Processor: {platform.processor()}\n")
                        f.write(f"🌐 Network Name: {platform.node()}\n")
                        f.write(f"📝 Report Size: {len(str(self.hardware_data))} characters\n")
                        f.write(f"🕒 Generation Time: {datetime.now().isoformat()}\n")
                        f.write("=" * 80 + "\n")
                        f.write("This report contains comprehensive hardware information\n")
                        f.write("collected by PC Hardware Checker Professional.\n")
                        f.write("All data reflects the system state at the time of generation.\n")
                        f.write("=" * 80 + "\n")
                
                messagebox.showinfo("Export Complete", f"Comprehensive hardware report saved to:\n{filename}")
                self.update_status(f"Enhanced report exported to {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to save report:\n{str(e)}")
    
    def _write_complex_data(self, file, data, indent=""):
        """Helper method to write complex nested data structures"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    file.write(f"{indent}🔸 {key}:\n")
                    self._write_complex_data(file, value, indent + "    ")
                else:
                    file.write(f"{indent}🔹 {key}: {value}\n")
        elif isinstance(data, list):
            for i, item in enumerate(data, 1):
                if isinstance(item, dict):
                    file.write(f"{indent}📋 Entry {i}:\n")
                    for key, value in item.items():
                        file.write(f"{indent}    🔹 {key}: {value}\n")
                else:
                    file.write(f"{indent}📌 {item}\n")
        else:
            file.write(f"{indent}{data}\n")
    
    def show_help(self):
        """Show help information"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - PC Hardware Checker Professional")
        help_window.geometry("800x700")
        help_window.configure(bg="#f0f0f0")
        
        # Make window resizable and center it
        help_window.resizable(True, True)
        help_window.transient(self.root)
        help_window.grab_set()
        
        help_text = tk.Text(help_window, wrap=tk.WORD, font=('Segoe UI', 10), 
                           bg='white', fg='#2c3e50')
        help_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        help_content = """PC Hardware Checker Professional - Complete Help Guide

WHAT IS THIS PROFESSIONAL TOOL?
This is an enterprise-grade hardware diagnostic application that provides comprehensive analysis 
of your computer's components. It combines basic hardware information with advanced stress 
testing capabilities, comparable to professional tools like AIDA64.

🖥️ MAIN FEATURES:

1. HARDWARE INFORMATION
- Detailed component specifications and real-time monitoring
- Professional-grade hardware detection and analysis
- Compatibility verification and bottleneck identification

2. STRESS TESTING SUITE
- 8 comprehensive test types for complete system analysis
- Real-time monitoring with color-coded alerts
- AIDA64-style detailed reporting with expert recommendations

3. REAL-TIME MONITORING
- Live performance charts and graphs (CPU, Memory, Disk, Network)
- Temperature monitoring with thermal analysis
- Multi-sensor data collection and professional visualization

📊 HARDWARE INFORMATION CATEGORIES:

🖥️ System Overview
- Computer specifications, Windows version, and system information
- Uptime tracking and user account details
- Platform and architecture information

🧠 Processor (CPU)  
- CPU model, cores, frequency, and architecture details
- Real-time usage monitoring and thermal information
- Performance characteristics and capabilities

💾 Memory (RAM)
- RAM capacity, usage statistics, and module information
- Memory speed, type, and configuration details
- Available vs. used memory with detailed breakdown

💿 Storage Drives
- Drive specifications, capacity, and performance metrics
- Disk usage by partition with detailed space analysis
- Drive type identification (SSD/HDD) and health status

🎮 Graphics (GPU)
- Graphics card model, memory, and specifications
- GPU utilization and performance monitoring
- Video memory usage and driver information

🌐 Network Interfaces
- Network adapter specifications and connection status
- Data transfer statistics and network performance
- IPv4/IPv6 configuration and MAC addresses

🔧 Motherboard & BIOS
- Motherboard manufacturer, model, and chipset information
- BIOS version, settings, and system configuration
- Hardware compatibility and upgrade potential

🔥 PROFESSIONAL STRESS TESTING:

🔄 Comprehensive System Test
- Complete multi-component stress testing
- System-wide performance analysis and bottleneck identification
- Thermal monitoring across all components

⚡ CPU Benchmark & Stability
- Multi-threaded computational stress testing
- Performance scoring with industry-standard ratings
- Thermal analysis and stability variance calculations

💾 Memory Performance & Stability
- RAM speed testing and error checking
- Memory allocation and deallocation stress testing
- Stability analysis under heavy memory loads

💿 Storage Performance Test
- Disk I/O speed testing and latency analysis
- Sequential and random read/write performance
- Storage reliability and thermal monitoring

🎮 GPU Performance Test
- Graphics processing stress testing
- GPU memory and thermal analysis
- 3D rendering performance evaluation

🌐 Network Performance Test
- Bandwidth testing and latency analysis
- Network connectivity and stability testing
- Data transfer performance evaluation

🔧 Hardware Compatibility Test
- Component compatibility verification
- System stability under mixed workloads
- Hardware interaction analysis

🌡️ Thermal Stress Test
- Advanced temperature monitoring and analysis
- Thermal throttling detection and cooling efficiency
- Multi-sensor thermal mapping

📈 REAL-TIME MONITORING FEATURES:

📊 Professional Charts & Graphs
- Live CPU, Memory, Disk I/O, and Network performance charts
- Historical data tracking with professional visualization
- Color-coded alerts and threshold monitoring

🌡️ Temperature Monitoring
- Multi-sensor temperature tracking (CPU, GPU, System)
- Thermal analysis with safety alerts
- Cooling efficiency evaluation

⚡ Performance Metrics
- Real-time usage statistics with professional formatting
- Performance scoring and stability analysis
- Bottleneck identification and optimization recommendations

💾 EXPORT & REPORTING:

📄 Professional Reports
- TXT Format: Human-readable detailed analysis reports
- JSON Format: Structured data for technical analysis
- Timestamped files for organized record keeping

📊 Report Contents
- Complete test methodology and results
- Hardware specifications and performance metrics
- Professional recommendations and optimization advice
- Safety analysis and thermal evaluation

🚀 HOW TO USE THIS TOOL:

BASIC HARDWARE INFORMATION:
1. Click any category in the left navigation menu
2. View detailed information with explanations
3. Use "Refresh Data" to update all information
4. Export reports using "Save Report" button

PROFESSIONAL STRESS TESTING:
1. Click "🔥 Stress Tests" in the navigation menu
2. Select test type and configure parameters (duration, intensity, memory)
3. Click "🚀 Start Test" to begin comprehensive analysis
4. Monitor real-time progress in the left panel
5. Review detailed analysis results in the right panel
6. Save professional reports using "💾 Save as TXT" or "📄 Save as JSON"

REAL-TIME MONITORING:
1. Click "📊 Real-Time Monitor" for live performance charts
2. View CPU, Memory, Disk I/O, Network, and Temperature data
3. Monitor multiple tabs for detailed component analysis
4. Use for system optimization and performance tuning

🛡️ SAFETY FEATURES:
- Automatic thermal protection and overheating prevention
- Safe memory allocation limits and background process detection
- Real-time monitoring with critical alerts
- Professional safety thresholds based on industry standards

🎯 PROFESSIONAL USE CASES:
- System performance benchmarking and validation
- Hardware stress testing before deployment
- Thermal performance analysis and cooling optimization
- Component compatibility verification
- Performance bottleneck identification
- System stability testing under load
- Pre-purchase hardware evaluation

COMPATIBILITY & REQUIREMENTS:
- Windows 7, 8, 10, 11 (32-bit and 64-bit)
- Administrator privileges recommended for full functionality
- Stress testing requires additional Python libraries (auto-installed)

TROUBLESHOOTING:
- Run as administrator for complete hardware detection
- Use installation scripts (install.bat) for dependency setup
- Check firewall settings if network tests fail
- Ensure adequate cooling before running stress tests

Need technical support? This tool provides enterprise-grade diagnostics comparable to 
professional hardware testing suites. For advanced features, refer to the comprehensive 
documentation and professional analysis reports generated by each test."""
        
        help_text.insert('1.0', help_content)
        help_text.configure(state='disabled')
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
    
    def start_progress(self):
        """Start progress bar"""
        self.progress.start(10)
    
    def stop_progress(self):
        """Stop progress bar"""
        self.progress.stop()
    
    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)
        self.update_status("Error occurred - see details in dialog")
