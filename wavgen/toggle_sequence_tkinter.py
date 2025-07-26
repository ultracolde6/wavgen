import os
import sys
import time
import logging
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import numpy as np
from pathlib import Path
import psutil

# Import real wavgen modules
try:
    import wavgen
    from wavgen import Card, Waveform, utilities
    from wavgen.waveform import Superposition
    from wavgen.utilities import from_file_simple
    from wavgen.spectrum import *
    from wavgen.constants import *
    HARDWARE_AVAILABLE = True
except ImportError:
    print("Warning: wavgen module not found. Using simulated mode.")
    HARDWARE_AVAILABLE = False
    # Fallback simulated classes
    class Card:
        def __init__(self):
            self.is_running = False
            self.amplitude = 80
            self.has_waveform = False
            
        def setup_channels(self, amplitude=80, ch0=True, ch1=False, use_filter=False):
            self.amplitude = amplitude
            print(f"Simulated: Card setup - amplitude={amplitude}")
            
        def load_waveforms(self, waveform):
            self.has_waveform = True
            print(f"Simulated: Card loaded waveform")
            
        def wiggle_output(self, duration=0):
            self.is_running = True
            print(f"Simulated: Card started output")
            
        def stop_output(self):
            self.is_running = False
            print("Simulated: Card stopped output")
            
        def get_status(self):
            return {
                'is_running': self.is_running,
                'amplitude': self.amplitude,
                'has_waveform': self.has_waveform
            }
    
    class Waveform:
        def __init__(self, name="waveform"):
            self.name = name
            
    class Superposition:
        def __init__(self, name="superposition"):
            self.name = name
            
    def from_file_simple(filename, key):
        return Waveform(f"loaded_from_{filename}_{key}")

class TkinterSequenceController:
    """Tkinter-based sequence controller with embedded configuration fields."""
    
    def __init__(self, use_simulation=False):  # Changed default to False
        """Initialize the controller with real hardware by default."""
        self.use_simulation = use_simulation
        self.running = False
        self.current_mode = None
        self.current_process = None
        self.selected_mode = None  # Track which mode is selected (but not running)
        self.execution_started = False  # Track if execution has been started
        
        # Initialize parameters
        self.static_params = self.get_default_static_params()
        self.sorting_params = self.get_default_sorting_params()
        
        # Setup logging
        self.setup_logging()
        
        # Initialize card - always try real hardware first
        self.card = None
        self.hardware_available = False
        
        try:
            # Always try real hardware first
            if HARDWARE_AVAILABLE:
                self.card = wavgen.Card()
                self.hardware_available = True
                self.logger.info("Real hardware initialized successfully")
            else:
                raise ImportError("wavgen module not available")
                
        except Exception as e:
            # Fallback to simulated card on any exception
            self.logger.warning(f"Real hardware failed: {e}")
            self.logger.info("Falling back to simulated hardware")
            self.card = Card()  # Use simulated card
            self.hardware_available = False
            self.use_simulation = True
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Wavgen Controller - Embedded Configuration")
        self.root.geometry("1200x800")
        
        # Setup window close handler to wipe logs
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Setup GUI
        self.setup_gui()
        
        # Status update thread
        self.status_queue = queue.Queue()
        self.update_status()
        
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('toggle_controller.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_default_static_params(self):
        """Get default static mode parameters."""
        return {
            'folder_name': 'waveforms_80_40Twz_5lambda_susc-meas',
            'filename': 'static.h5',
            'use_filter': False
        }
        
    def get_default_sorting_params(self):
        """Get default sorting mode parameters."""
        return {
            'path_folder': 'waveforms_80_40Twz_5lambda_susc-meas',
            'multi_trig': False,
            'startfreq': 88.0,
            'spacing': 0.8,
            'ntraps': 40,
            'AXA_list': [['static.h5', 'static.h5', 'static.h5']],
            'drop_list': ['static.h5']
        }
        
    def setup_gui(self):
        """Setup the main GUI with embedded configuration fields."""
        # Configure modern styling
        style = ttk.Style()
        style.theme_use('clam')  # Use clam theme for modern look
        
        # Define Dracula-inspired dark color scheme
        bg_color = '#282a36'      # Dark background
        frame_bg = '#44475a'      # Slightly lighter frame background
        accent_color = '#bd93f9'  # Purple accent
        text_color = '#f8f8f2'    # Light text
        secondary_color = '#6272a4'  # Blue-gray secondary
        highlight_color = '#ff79c6'  # Pink highlight
        success_color = '#50fa7b'    # Green for success states
        
        # Configure styles
        style.configure('Title.TLabel', font=('Arial', 18, 'bold'), foreground=accent_color)
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'), foreground=text_color)
        style.configure('Status.TLabel', font=('Courier', 11, 'bold'), foreground=text_color)
        style.configure('Modern.TLabelframe', background=frame_bg, relief='solid', borderwidth=1)
        style.configure('Modern.TLabelframe.Label', font=('Arial', 12, 'bold'), foreground=accent_color, background=frame_bg)
        style.configure('Modern.TButton', font=('Arial', 11, 'bold'), padding=5)
        
        # Additional dark theme styling
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=text_color)
        style.configure('TEntry', fieldbackground=frame_bg, foreground=text_color, insertcolor=accent_color)
        style.configure('TCheckbutton', background=bg_color, foreground=text_color)
        style.configure('TLabelframe', background=frame_bg)
        style.configure('TLabelframe.Label', background=frame_bg, foreground=accent_color)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        
        # Set dark background color
        self.root.configure(bg=bg_color)
        main_frame.configure(style='Modern.TFrame')
        
        # Title with modern styling
        title_label = ttk.Label(main_frame, text="WAVGEN CONTROLLER", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 15))
        
        # Status frame (left side) - made smaller
        status_frame = ttk.LabelFrame(main_frame, text="System Status", style='Modern.TLabelframe', padding="8")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 8), pady=(0, 10))
        
        self.status_text = tk.StringVar(value="Initializing...")
        status_label = ttk.Label(status_frame, textvariable=self.status_text, style='Status.TLabel')
        status_label.pack(anchor=tk.W)
        
        # Configuration frame - brings static and sorting closer together
        config_frame = ttk.Frame(main_frame)
        config_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        config_frame.columnconfigure(0, weight=1)
        config_frame.columnconfigure(1, weight=1)
        
        # Static parameters frame (left side) - closer to sorting
        static_frame = ttk.LabelFrame(config_frame, text="Static Parameters", style='Modern.TLabelframe', padding="10")
        static_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Static parameter fields with better spacing
        ttk.Label(static_frame, text="Folder Name:", font=('Arial', 11, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=3)
        self.static_folder_var = tk.StringVar(value=self.static_params['folder_name'])
        ttk.Entry(static_frame, textvariable=self.static_folder_var, width=28).grid(row=0, column=1, padx=(8, 0), pady=3)
        
        ttk.Label(static_frame, text="Filename:", font=('Arial', 11, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=3)
        self.static_filename_var = tk.StringVar(value=self.static_params['filename'])
        ttk.Entry(static_frame, textvariable=self.static_filename_var, width=28).grid(row=1, column=1, padx=(8, 0), pady=3)
        
        ttk.Label(static_frame, text="Use Filter:", font=('Arial', 11, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=3)
        self.static_filter_var = tk.BooleanVar(value=self.static_params['use_filter'])
        ttk.Checkbutton(static_frame, variable=self.static_filter_var).grid(row=2, column=1, padx=(8, 0), pady=3, sticky=tk.W)
        
        # Sorting parameters frame (right side) - closer to static
        sorting_frame = ttk.LabelFrame(config_frame, text="Sorting Parameters", style='Modern.TLabelframe', padding="10")
        sorting_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # Sorting parameter fields with better spacing
        ttk.Label(sorting_frame, text="Path Folder:", font=('Arial', 11, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=3)
        self.sorting_path_var = tk.StringVar(value=self.sorting_params['path_folder'])
        ttk.Entry(sorting_frame, textvariable=self.sorting_path_var, width=28).grid(row=0, column=1, padx=(8, 0), pady=3)
        
        ttk.Label(sorting_frame, text="Multi Trigger:", font=('Arial', 11, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=3)
        self.sorting_trigger_var = tk.BooleanVar(value=self.sorting_params['multi_trig'])
        ttk.Checkbutton(sorting_frame, variable=self.sorting_trigger_var).grid(row=1, column=1, padx=(8, 0), pady=3, sticky=tk.W)
        
        ttk.Label(sorting_frame, text="Start Frequency (MHz):", font=('Arial', 11, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=3)
        self.sorting_freq_var = tk.StringVar(value=str(self.sorting_params['startfreq']))
        ttk.Entry(sorting_frame, textvariable=self.sorting_freq_var, width=28).grid(row=2, column=1, padx=(8, 0), pady=3)
        
        ttk.Label(sorting_frame, text="Spacing (MHz):", font=('Arial', 11, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=3)
        self.sorting_spacing_var = tk.StringVar(value=str(self.sorting_params['spacing']))
        ttk.Entry(sorting_frame, textvariable=self.sorting_spacing_var, width=28).grid(row=3, column=1, padx=(8, 0), pady=3)
        
        ttk.Label(sorting_frame, text="Number of Traps:", font=('Arial', 11, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=3)
        self.sorting_traps_var = tk.StringVar(value=str(self.sorting_params['ntraps']))
        ttk.Entry(sorting_frame, textvariable=self.sorting_traps_var, width=28).grid(row=4, column=1, padx=(8, 0), pady=3)
        
        # AXA List - individual entries with better styling
        ttk.Label(sorting_frame, text="AXA List:", font=('Arial', 11, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=3)
        axa_frame = ttk.Frame(sorting_frame)
        axa_frame.grid(row=5, column=1, padx=(8, 0), pady=3, sticky=tk.W)
        
        self.axa_vars = []
        for i in range(3):  # Assuming 3 elements in AXA list
            var = tk.StringVar(value=self.sorting_params['AXA_list'][0][i] if i < len(self.sorting_params['AXA_list'][0]) else 'static.h5')
            self.axa_vars.append(var)
            ttk.Entry(axa_frame, textvariable=var, width=12).grid(row=0, column=i, padx=2)
        
        ttk.Label(sorting_frame, text="Drop List:", font=('Arial', 11, 'bold')).grid(row=6, column=0, sticky=tk.W, pady=3)
        self.sorting_drop_var = tk.StringVar(value=self.sorting_params['drop_list'][0] if self.sorting_params['drop_list'] else 'static.h5')
        ttk.Entry(sorting_frame, textvariable=self.sorting_drop_var, width=28).grid(row=6, column=1, padx=(8, 0), pady=3)
        
        # Control buttons frame with modern styling
        button_frame = ttk.LabelFrame(main_frame, text="Control Panel", style='Modern.TLabelframe', padding="10")
        button_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Mode selection buttons (always enabled)
        mode_frame = ttk.Frame(button_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mode_frame, text="Select Mode:", font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        self.static_select_button = ttk.Button(mode_frame, text="Static Mode", command=self.select_static_mode, style='Modern.TButton')
        self.static_select_button.pack(side=tk.LEFT, padx=3)
        self.sorting_select_button = ttk.Button(mode_frame, text="Sorting Mode", command=self.select_sorting_mode, style='Modern.TButton')
        self.sorting_select_button.pack(side=tk.LEFT, padx=3)
        
        # Execution control buttons
        exec_frame = ttk.Frame(button_frame)
        exec_frame.pack(fill=tk.X, pady=5)
        ttk.Label(exec_frame, text="Execution Control:", font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        self.start_execution_button = ttk.Button(exec_frame, text="START EXECUTION", command=self.start_execution, style='Modern.TButton', state='disabled')
        self.start_execution_button.pack(side=tk.LEFT, padx=3)
        self.stop_execution_button = ttk.Button(exec_frame, text="STOP EXECUTION", command=self.stop_execution, style='Modern.TButton', state='disabled')
        self.stop_execution_button.pack(side=tk.LEFT, padx=3)
        
        # Parameter and utility buttons
        util_frame = ttk.Frame(button_frame)
        util_frame.pack(fill=tk.X, pady=5)
        self.update_button = ttk.Button(util_frame, text="Update Parameters", command=self.update_parameters, style='Modern.TButton')
        self.update_button.pack(side=tk.LEFT, padx=3)
        self.restart_button = ttk.Button(util_frame, text="Restart Execution", command=self.restart_current_mode, style='Modern.TButton', state='disabled')
        self.restart_button.pack(side=tk.LEFT, padx=3)
        self.kill_button = ttk.Button(util_frame, text="Kill Program", command=self.kill_program, style='Modern.TButton')
        self.kill_button.pack(side=tk.LEFT, padx=3)
        
        # Logs frame with modern styling
        logs_frame = ttk.LabelFrame(main_frame, text="Recent Logs", style='Modern.TLabelframe', padding="8")
        logs_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Configure logs text widget with dark theme styling
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=6, width=120, font=('Courier', 10, 'bold'), 
                                                 bg=frame_bg, fg=text_color, insertbackground=accent_color)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure row weights for better layout
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
    def update_parameters(self):
        """Update parameters from GUI fields."""
        try:
            # Update static parameters
            self.static_params['folder_name'] = self.static_folder_var.get()
            self.static_params['filename'] = self.static_filename_var.get()
            self.static_params['use_filter'] = self.static_filter_var.get()
            
            # Update sorting parameters
            self.sorting_params['path_folder'] = self.sorting_path_var.get()
            self.sorting_params['multi_trig'] = self.sorting_trigger_var.get()
            self.sorting_params['startfreq'] = float(self.sorting_freq_var.get())
            self.sorting_params['spacing'] = float(self.sorting_spacing_var.get())
            self.sorting_params['ntraps'] = int(self.sorting_traps_var.get())
            
            # Update AXA list from individual entries
            axa_entries = [var.get() for var in self.axa_vars]
            self.sorting_params['AXA_list'] = [axa_entries]  # Single row of AXA entries
            
            # Handle drop list - automatically format as Python list
            drop_input = self.sorting_drop_var.get().strip()
            if drop_input:
                # If user typed just a filename, wrap it in a list
                if not drop_input.startswith('['):
                    self.sorting_params['drop_list'] = [drop_input]
                else:
                    # If user typed a proper list format, parse it
                    try:
                        self.sorting_params['drop_list'] = eval(drop_input)
                    except:
                        self.sorting_params['drop_list'] = [drop_input]
            else:
                self.sorting_params['drop_list'] = ['static.h5']
            
            self.logger.info("Parameters updated successfully")
            messagebox.showinfo("Success", "Parameters updated successfully!")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid parameter value: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error updating parameters: {e}")
            
    def update_status(self):
        """Update status display."""
        try:
            status = self.get_status()
            
            # Get card status if available
            card_info = ""
            if self.card and hasattr(self.card, 'get_status'):
                try:
                    card_status = self.card.get_status()
                    card_info = f"Card: {card_status.get('is_running', 'N/A')} | Amp: {card_status.get('amplitude', 'N/A')} | Wave: {card_status.get('has_waveform', 'N/A')}"
                except Exception as e:
                    card_info = f"Card: Error - {e}"
            
            status_text = f"""Mode: {status['mode']}
Running: {status['running']}
Hardware: {'Available' if status['hardware_available'] else 'Simulated'}
Process: {status.get('process_status', 'none')}
{card_info}"""
            
            self.status_text.set(status_text)
            
            # Update logs
            recent_logs = self.get_recent_logs(10)
            self.logs_text.delete(1.0, tk.END)
            self.logs_text.insert(tk.END, recent_logs)
            
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")
        
        # Schedule next update
        self.root.after(1000, self.update_status)
        
    def get_recent_logs(self, lines=10):
        """Get recent log entries."""
        try:
            with open('toggle_controller.log', 'r') as f:
                all_logs = f.readlines()
                recent_logs = all_logs[-lines:] if len(all_logs) >= lines else all_logs
                return ''.join(recent_logs)
        except FileNotFoundError:
            return "No log file found."
        except Exception as e:
            return f"Error reading logs: {e}"
            
    def get_status(self):
        """Get current status information."""
        status = {
            'mode': self.current_mode or 'idle',
            'running': self.running,
            'hardware_available': self.hardware_available,
            'use_simulation': self.use_simulation,
            'static_params': self.static_params,
            'sorting_params': self.sorting_params
        }
        
        if self.current_mode == "sorting" and self.current_process:
            if isinstance(self.current_process, threading.Thread):
                status['process_status'] = 'running with auto-restart' if self.current_process.is_alive() else 'stopped'
            else:
                status['process_status'] = 'running' if self.current_process.poll() is None else 'stopped'
        elif self.current_process:
            status['process_status'] = 'running' if self.current_process.poll() is None else 'stopped'
        else:
            status['process_status'] = 'none'
            
        return status
        
    def start_system(self):
        """Start the system and enable all control buttons."""
        try:
            self.logger.info("Starting system...")
            self.system_started = True
            
            # Enable all control buttons
            self.static_button.config(state='normal')
            self.sorting_button.config(state='normal')
            self.restart_button.config(state='normal')
            self.stop_button.config(state='normal')
            self.update_button.config(state='normal')
            
            # Disable start button
            self.start_button.config(state='disabled')
            
            self.logger.info("System started successfully. All controls enabled.")
            messagebox.showinfo("System Started", "System is now active. You can now use all control buttons.")
            
        except Exception as e:
            error_msg = f"Error starting system: {e}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def select_static_mode(self):
        """Select static mode (does not start execution)."""
        self.selected_mode = "static"
        self.static_select_button.config(style='Modern.TButton')  # Highlight selected
        self.sorting_select_button.config(style='Modern.TButton')  # Unhighlight other
        self.start_execution_button.config(state='normal')  # Enable start button
        self.logger.info("Static mode selected. Click START EXECUTION to begin.")
        messagebox.showinfo("Mode Selected", "Static mode selected. Click START EXECUTION to begin superposition.")
    
    def select_sorting_mode(self):
        """Select sorting mode (does not start execution)."""
        self.selected_mode = "sorting"
        self.sorting_select_button.config(style='Modern.TButton')  # Highlight selected
        self.static_select_button.config(style='Modern.TButton')  # Unhighlight other
        self.start_execution_button.config(state='normal')  # Enable start button
        self.logger.info("Sorting mode selected. Click START EXECUTION to begin.")
        messagebox.showinfo("Mode Selected", "Sorting mode selected. Click START EXECUTION to begin sorting sequence.")
    
    def start_execution(self):
        """Start execution of the selected mode."""
        if not self.selected_mode:
            messagebox.showwarning("No Mode Selected", "Please select a mode first (Static or Sorting).")
            return
            
        try:
            self.logger.info(f"Starting execution of {self.selected_mode} mode...")
            self.execution_started = True
            
            # Disable mode selection buttons
            self.static_select_button.config(state='disabled')
            self.sorting_select_button.config(state='disabled')
            self.start_execution_button.config(state='disabled')
            
            # Enable execution control buttons
            self.stop_execution_button.config(state='normal')
            self.restart_button.config(state='normal')
            
            # Start the selected mode
            if self.selected_mode == "static":
                self.start_static_mode()
            elif self.selected_mode == "sorting":
                self.start_sorting_mode()
            
            self.logger.info(f"Execution started for {self.selected_mode} mode.")
            
        except Exception as e:
            error_msg = f"Error starting execution: {e}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            
    def start_static_mode(self):
        """Start static superposition mode - always try real hardware first."""
        try:
            # Stop any existing process first
            if self.current_process or self.running:
                self.logger.info("Stopping existing process before starting static mode...")
                self.stop_current_process()
                time.sleep(0.5)  # Brief pause for cleanup
                
            self.logger.info("Starting static superposition mode...")
            
            # Update parameters first
            self.update_parameters()
            
            # Always try real hardware first
            try:
                folder_name = self.static_params['folder_name']
                filename = Path(folder_name, self.static_params['filename'])
                
                # Check if file exists
                if os.access(filename, os.F_OK):
                    print('Read file!')
                    A = from_file_simple(filename, 'A')
                else:
                    raise FileNotFoundError(f"File {filename} not found")
                
                # Initialize card
                dwCard = wavgen.Card()
                
                # Setup channels
                dwCard.setup_channels(amplitude=80, use_filter=self.static_params['use_filter'])
                
                # Load waveforms
                dwCard.load_waveforms(A)
                print('outputting')
                dwCard.wiggle_output(duration=0)
                
                self.logger.info("Real hardware static mode started successfully")
                
            except Exception as e:
                self.logger.warning(f"Real hardware failed: {e}")
                self.logger.info("Falling back to simulated static mode")
                
                # Fallback to simulated
                if self.card:
                    self.card.setup_channels(amplitude=80, use_filter=self.static_params['use_filter'])
                    waveform = Waveform(f"static_{self.static_params['filename']}")
                    self.card.load_waveforms(waveform)
                    self.card.wiggle_output()
                self.logger.info("Simulated static mode started")
                
            self.current_mode = "static"
            self.running = True
            self.logger.info("Static mode started successfully.")
            
        except Exception as e:
            error_msg = f"Error starting static mode: {e}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            
    def start_sorting_mode(self):
        """Start sorting mode with automatic restart logic like runner.py."""
        if not self.execution_started:
            messagebox.showwarning("No Execution Running", "Please click START EXECUTION first.")
            return
            
        try:
            # Stop any existing process first
            if self.current_process or self.running:
                self.logger.info("Stopping existing process before starting sorting mode...")
                self.stop_current_process()
                time.sleep(0.5)  # Brief pause for cleanup
                
            self.logger.info("Starting sorting mode with automatic restart...")
            
            # Update parameters first
            self.update_parameters()
            
            # Create temporary script with current parameters
            script_content = self.create_sorting_script()
            temp_script_path = "temp_sorting_script.py"
            
            try:
                with open(temp_script_path, 'w') as f:
                    f.write(script_content)
                
                # Start sorting process with automatic restart logic (like runner.py)
                def run_sorting_with_restart():
                    while self.running and self.current_mode == "sorting":
                        try:
                            self.logger.info("Starting rearrangement sequence...")
                            
                            # Run sorting script as subprocess
                            process = subprocess.Popen(
                                [sys.executable, temp_script_path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True
                            )
                            
                            # Wait for process to complete
                            process.wait()
                            
                            # If we get here, process has died - restart it
                            if self.running and self.current_mode == "sorting":
                                self.logger.warning("Trigger has been missed. Wavegen has died. Restarting...")
                                print("Trigger has been missed. Wavegen has died. Restarting...")
                                time.sleep(1)  # Brief pause before restart
                            else:
                                break  # Exit loop if mode changed or stopped
                                
                        except Exception as e:
                            self.logger.error(f"Error in sorting process: {e}")
                            if self.running and self.current_mode == "sorting":
                                self.logger.info("Restarting sorting process after error...")
                                time.sleep(2)  # Longer pause after error
                            else:
                                break
                
                # Start the restart loop in a separate thread
                self.current_process = threading.Thread(target=run_sorting_with_restart, daemon=True)
                self.current_process.start()
                
                self.current_mode = "sorting"
                self.running = True
                self.logger.info("Sorting mode started with automatic restart.")
                
            except Exception as e:
                self.logger.error(f"Error starting sorting subprocess: {e}")
                # Fallback to simulated mode
                print("Simulated: Starting sorting sequence with restart logic")
                print("Simulated: Sorting mode started successfully")
                self.current_mode = "sorting"
                self.running = True
                self.logger.info("Fallback to simulated sorting mode")
            
        except Exception as e:
            error_msg = f"Error starting sorting mode: {e}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            
    def create_sorting_script(self):
        """Create a temporary sorting script with exact same logic as rearrangement_sequence_double_sort_multidrop.py."""
        script = f'''#!/usr/bin/env python3
import sys
import os
import time
import numpy as np
from pathlib import Path
import h5py
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from image_analysis import analyze_image
from wavgen.utilities import *
from wavgen.spectrum import *
from wavgen.constants import *

# Parameters from GUI
path_folder = "{self.sorting_params['path_folder']}"
multi_trig = {self.sorting_params['multi_trig']}
startfreq = {self.sorting_params['startfreq']}
spacing = {self.sorting_params['spacing']}
ntraps = {self.sorting_params['ntraps']}
AXA_list = {self.sorting_params['AXA_list']}
drop_list = {self.sorting_params['drop_list']}

# Calculate tweezer frequencies exactly like original
tweezer_freq_list = [startfreq + j * spacing for j in range(ntraps)]
num_tweezers = len(tweezer_freq_list)
N_cycle = np.lcm(len(AXA_list), len(drop_list))

# Include sorting waveforms exactly like original
sort_list_L = [f'sweep_{{num}}.h5' for num in range(1, ntraps)]
sort_list_R = [f'sweep_{{num}}R.h5' for num in range(1, ntraps)]
sort_list = np.concatenate((sort_list_L, sort_list_R))
wf_list = []

# Load waveforms exactly like original
for filename in sort_list:
    if os.access(Path(path_folder, filename), os.F_OK):
        wav_temp = utilities.from_file(Path(path_folder, filename), 'AB')
        wf_list.append(wav_temp)

# Include static waveform
wav_temp = utilities.from_file(Path(path_folder, 'static.h5'), 'A')
wf_list.append(wav_temp)

# Include drop waveforms
for filename in drop_list:
    wf_list.append(utilities.from_file_simple(Path(path_folder, filename), 'A'))

# Include multi trig AXA waveforms
flattened_AXA_list = [item for row in AXA_list for item in row]
for filename in flattened_AXA_list:
    wf_list.append(utilities.from_file_simple(Path(path_folder, filename), 'A'))

segment_list = range(len(wf_list))

# Initialize card exactly like original
hCard = spcm_hOpen(create_string_buffer(b'/dev/spcm0'))

# Setup channels exactly like original
def setup_channels(amplitude=DEF_AMP, ch0=True, ch1=False, use_filter=False):
    if ch0 and ch1:
        print('Multi-Channel Support Not Yet Supported!')
        print('Defaulting to Ch1 only.')
        ch0 = False
    assert 80 <= amplitude <= (1000 if use_filter else 480), "Amplitude must within interval: [80 - 2000]"
    if amplitude != int(amplitude):
        amplitude = int(amplitude)
        print("Rounding amplitude to required integer value: ", amplitude)
    CHAN = 0x00000000
    amp = int32(amplitude)
    if ch0:
        spcm_dwSetParam_i32(hCard, SPC_ENABLEOUT0, 1)
        CHAN = CHAN ^ CHANNEL0
        spcm_dwSetParam_i32(hCard, SPC_AMP0, amp)
        spcm_dwSetParam_i64(hCard, SPC_FILTER0, int64(use_filter))
    if ch1:
        spcm_dwSetParam_i32(hCard, SPC_ENABLEOUT1, 1)
        CHAN = CHAN ^ CHANNEL1
        spcm_dwSetParam_i32(hCard, SPC_AMP1, amp)
        spcm_dwSetParam_i64(hCard, SPC_FILTER1, int64(use_filter))
    spcm_dwSetParam_i32(hCard, SPC_CHENABLE, CHAN)

def _setup_clock():
    spcm_dwSetParam_i32(hCard, SPC_CLOCKMODE, SPC_CM_EXTREFCLOCK)
    spcm_dwSetParam_i32(hCard, SPC_REFERENCECLOCK, 10000000)
    spcm_dwSetParam_i64(hCard, SPC_SAMPLERATE, int64(int(SAMP_FREQ)))
    spcm_dwSetParam_i32(hCard, SPC_CLOCKOUT, 0)
    check_clock = int64(0)
    spcm_dwGetParam_i64(hCard, SPC_SAMPLERATE, byref(check_clock))
    print("Achieved Sampling Rate: ", check_clock.value)

def _write_segment(wavs, pv_buf, pn_buf, offset=0):
    total_so_far = offset
    for wav in wavs:
        size = min(wav.SampleLength, NUMPY_MAX)
        so_far = 0
        spcm_dwInvalidateBuf(hCard, SPCM_BUF_DATA)
        wav.load(pn_buf, 0, size)
        spcm_dwDefTransfer_i64(hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, int32(0), pv_buf, uint64(0), uint64(size * 2))
        dwError = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)

# Setup channels and clock exactly like original
setup_channels(amplitude=85, use_filter=False)
_setup_clock()

# Set up card mode exactly like original
start_step = 0
max_segments = len(wf_list)
spcm_dwSetParam_i32(hCard, SPC_CARDMODE, SPC_REP_STD_SEQUENCE)
spcm_dwSetParam_i32(hCard, SPC_TRIG_ORMASK, SPC_TM_NONE)
spcm_dwSetParam_i32(hCard, SPC_TRIG_ORMASK, SPC_TMASK_EXT0)
spcm_dwSetParam_i32(hCard, SPC_TRIG_EXT0_LEVEL0, 1500)
spcm_dwSetParam_i32(hCard, SPC_TRIG_EXT0_MODE, SPC_TM_POS)
spcm_dwSetParam_i32(hCard, SPC_SEQMODE_MAXSEGMENTS, max_segments)
spcm_dwSetParam_i32(hCard, SPC_SEQMODE_STARTSTEP, start_step)

# Create buffers and write segments exactly like original
pv_buf_list = []
pn_buf_list = []
for j in range(len(segment_list)):
    pv_buf = pvAllocMemPageAligned(wf_list[j].SampleLength * 2)
    pv_buf_list.append(pv_buf)
    pn_buf_list.append(cast(pv_buf, ptr16))
for j in range(len(segment_list)):
    print(wf_list[j].SampleLength)
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_WRITESEGMENT, segment_list[j])
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_SEGMENTSIZE, wf_list[j].SampleLength)
    _write_segment([wf_list[j]], pv_buf_list[j], pn_buf_list[j], offset=0)

# Set up static configuration exactly like original
lStep = 0
llSegment = 2*num_tweezers-2
llLoop = 1
llNext = 1
llCondition = SPCSEQ_ENDLOOPONTRIG
print('first trigger')
llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

lStep = 1
llSegment = 2*num_tweezers-2
llLoop = 1
llNext = 0
llCondition = SPCSEQ_ENDLOOPALWAYS
llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

# Event handler class for the two sorts
class TestEventHandler(PatternMatchingEventHandler):
    def __init__(self, Cycle_num, drop_num, AXA_num, *args, **kwargs):
        super(TestEventHandler, self).__init__(*args, **kwargs)
        self.last_created = None
        self.Cycle_num = Cycle_num
        self.AXA_num = AXA_num
        self.drop_num = drop_num
        self.drop_counter = 0
        self.AXA_counter = 0
        self.i_counter = 0
        self.previous_time = time.time()
        self.current_time = time.time()
        self.shot_counter = 0
        self.tic = time.perf_counter()
        self.bad_shot_list = []

    def on_created(self, event):
        tic_1 = time.perf_counter()
        path = event.src_path
        if path != self.last_created:
            self.last_created = path
            print(f'{{event.src_path}} has been created!')
            time.sleep(0.05)
            try:
                hf = h5py.File(f'{{event.src_path}} ', 'r')
            except:
                time.sleep(0.05)
                hf = h5py.File(f'{{event.src_path}} ', 'r')
                print('exception')
            print('read file')
            im_array = np.array(hf['frame-00'])
            hf.close()
            atom_count, empty_list = analyze_image(im_array, tweezer_freq_list, num_tweezers)
            print(atom_count, empty_list)
            tic_2 = time.perf_counter()
            try:
                print('tic_2-tic_1', tic_2-tic_1)
                time_diff = tic_2-tic_1
            except:
                time_diff = 0
            if time_diff > 0.8:
                print('skipping')
                self.bad_shot_list.append(self.shot_counter+1)
                lStep = 1
                llSegment = 2 * num_tweezers - 2
                llLoop = 1
                llNext = 0
                llCondition = SPCSEQ_ENDLOOPALWAYS
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
            else:
                if 0 < atom_count:
                    segment_queue_L = []
                    segment_queue_R = []
                    # Now divide into left and right sides of the boundary
                    mask_empty = np.diff(empty_list) > 1
                    for i in range(len(mask_empty)):
                        if mask_empty[i] and empty_list[0] == 0:
                            empty_list_reduced = empty_list[i+1:]
                            break
                        else:
                            empty_list_reduced = empty_list
                    for i in range(len(mask_empty)):
                        if mask_empty[-1-i] and empty_list[-1] == num_tweezers-1:
                            empty_list_reduced = empty_list_reduced[:-1-i]
                            break
                    
                    # Now divide into left and right sides of the boundary
                    empty_list_reduced = np.sort(empty_list_reduced)
                    print('empty_list_reduced:', empty_list_reduced)
                    num_empty = len(empty_list)
                    boundary = empty_list[int(num_empty / 2)]
                    print('boundary:', boundary)
                    mask_L = empty_list_reduced <= boundary
                    mask_R = empty_list_reduced > boundary
                    empty_list_L = empty_list_reduced[mask_L]
                    empty_list_R = empty_list_reduced[mask_R]
                    for i in empty_list_L:
                        if i > 0:
                            segment_queue_L.append(segment_list[i - 1])
                    for i in empty_list_R:
                        if i < num_tweezers-1:
                            segment_queue_R.append(segment_list[2*(num_tweezers-1)-i-1])
                    segment_queue_R = np.flip(segment_queue_R)
                    print(f'segment_queue_L = {{segment_queue_L}}')
                    print(f'segment_queue_R = {{segment_queue_R}}')

                    if len(segment_queue_L) > 0:
                        print('left sorting')
                        for k in range(len(segment_queue_L) - 1):
                            lStep = k + 1
                            llSegment = segment_queue_L[k]
                            llLoop = 1
                            llNext = k + 2
                            llCondition = SPCSEQ_ENDLOOPALWAYS
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = len(segment_queue_L)
                        llSegment = segment_queue_L[-1]
                        llLoop = 1
                        if len(segment_queue_R) > 0:
                            llNext = len(segment_queue_L) + 1
                        else:
                            print('dropping')
                            llNext = 2*num_tweezers + 21
                            llCondition = SPCSEQ_ENDLOOPALWAYS
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        if len(segment_queue_R) > 0:
                            print('right sorting 1')
                            for k in range(len(segment_queue_R) - 1):
                                lStep = len(segment_queue_L) + k + 1
                                llSegment = segment_queue_R[k]
                                llLoop = 1
                                llNext = len(segment_queue_L) + k + 2
                                llCondition = SPCSEQ_ENDLOOPALWAYS
                                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                            lStep = len(segment_queue_L) + len(segment_queue_R)
                            llSegment = segment_queue_R[-1]
                            llLoop = 1
                            llNext = 2*num_tweezers + 21
                            llCondition = SPCSEQ_ENDLOOPALWAYS
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        else:
                            lStep = 2 * num_tweezers + 100
                            llSegment = 2 * num_tweezers - 2
                            llLoop = 1
                            llNext = 0
                            llCondition = SPCSEQ_ENDLOOPALWAYS
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    elif len(segment_queue_R) > 0 and len(segment_queue_L) == 0:
                        print('right sorting 2')
                        for k in range(len(segment_queue_R) - 1):
                            lStep = k + 1
                            llSegment = segment_queue_R[k]
                            llLoop = 1
                            llNext = k + 2
                            llCondition = SPCSEQ_ENDLOOPALWAYS
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = len(segment_queue_R)
                        llSegment = segment_queue_R[-1]
                        llLoop = 1
                        llNext = 2 * num_tweezers + 21
                        llCondition = SPCSEQ_ENDLOOPALWAYS
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    else:
                        lStep = 1
                        llLoop = 1
                        llSegment = 2*num_tweezers-1 + self.drop_counter
                        llNext = 0
                        llCondition = SPCSEQ_ENDLOOPALWAYS
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 21
                    print(f"####################{{self.drop_counter}}###################")
                    llSegment = 2 * num_tweezers - 1 + self.drop_counter
                    llLoop = int(10 * 0.001 * SAMP_FREQ / wf_list[llSegment].SampleLength)
                    llNext = 2 * num_tweezers + 100
                    llCondition = SPCSEQ_ENDLOOPALWAYS
                    tic1 = time.perf_counter()
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    # Start of AXA
                    if multi_trig == True:
                        lStep = 2 * num_tweezers + 100
                        llSegment = 2 * num_tweezers - 2
                        llLoop = 1
                        llNext = 2 * num_tweezers + 22
                        llCondition = SPCSEQ_ENDLOOPONTRIG
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = 2 * num_tweezers + 22
                        llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter))
                        llLoop = 1
                        llNext = 2 * num_tweezers + 23
                        llCondition = SPCSEQ_ENDLOOPALWAYS
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = 2 * num_tweezers + 23
                        llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter) + 1)
                        llLoop = 1
                        llNext = 2 * num_tweezers + 24
                        llCondition = SPCSEQ_ENDLOOPONTRIG
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                        toc1 = time.perf_counter()
                        lStep = 2 * num_tweezers + 24
                        llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter) + 2)
                        llLoop = 1
                        llNext = 2 * num_tweezers + 25
                        llCondition = SPCSEQ_ENDLOOPALWAYS
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = 2 * num_tweezers + 25
                        llSegment = 2 * num_tweezers - 2
                        llLoop = 1
                        llNext = 0
                        llCondition = SPCSEQ_ENDLOOPONTRIG
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    else:
                        lStep = 2 * num_tweezers + 100
                        llSegment = 2 * num_tweezers - 2
                        llLoop = 1
                        llNext = 0
                        llCondition = SPCSEQ_ENDLOOPALWAYS
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                else:
                    lStep = 1
                    llSegment = 2*num_tweezers-1 + self.drop_counter
                    llLoop = int(5 * 0.001 * SAMP_FREQ / wf_list[llSegment].SampleLength)
                    llNext = 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                print(f'Cycle {{self.i_counter:0.0f}} of {{self.Cycle_num:0.0f}}')
                self.current_time = time.time()
                print("********************************")
                print(f'Cycle {{self.drop_counter:0.0f}} of {{self.drop_num:0.0f}} in drop waveforms')
                print(f'Cycle {{self.AXA_counter:0.0f}} of {{self.AXA_num:0.0f}} in AXA waveforms')
                print("*******************************")
                self.i_counter = (self.i_counter + 1) % self.Cycle_num
                self.drop_counter = (self.drop_counter + 1) % self.drop_num
                self.AXA_counter = (self.AXA_counter + 1) % self.AXA_num
                self.previous_time = self.current_time
                self.shot_counter += 1
                print('shot', self.shot_counter)
                toc = time.perf_counter()
                print(f'analysis took {{toc - self.tic:0.6f}} seconds')
                print('bad_shot_list:', self.bad_shot_list)
                self.tic = toc

def main():
    try:
        # Set up watchdog
        print('watchdog')
        patterns = ["*"]
        ignore_patterns = None
        ignore_directories = False
        case_sensitive = True
        missed_trigger_event = False
        my_event_handler = TestEventHandler(N_cycle, len(drop_list), len(AXA_list), patterns, ignore_patterns, ignore_directories, case_sensitive)

        # Set up observer paths
        path = Path('C:/', 'Users', 'CavityQED', 'Desktop', 'fluo_images_delete_1')
        path_2 = Path('C:/', 'Users', 'CavityQED', 'Desktop', 'fluo_images_delete_2')
        go_recursively = True
        my_observer = Observer()
        my_observer.schedule(my_event_handler, path_2, recursive=go_recursively)
        my_observer.schedule(my_event_handler, path, recursive=go_recursively)

        # Start card exactly like original
        WAIT = M2CMD_CARD_WAITTRIGGER
        spcm_dwSetParam_i32(hCard, SPC_TIMEOUT, int(1))
        dwError = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_START)
        count = 0
        while dwError == ERR_CLOCKNOTLOCKED:
            print("Clock not Locked, giving it a moment to adjust...")
            count += 1
            time.sleep(0.1)
            dwError = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_START)
            if count == 10:
                print('count 10')
                break
        print('Clock Locked')
        spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_ENABLETRIGGER)
        spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_FORCETRIGGER)
        print('TriggerEnabled')

        # Start observer
        my_observer.start()
        try:
            while not missed_trigger_event:
                time.sleep(1)
        except KeyboardInterrupt:
            my_observer.stop()
            my_observer.join()
            print(f"missed_trigger_event={{missed_trigger_event}}")

    except Exception as e:
        print(f"Error in sorting script: {{e}}")
        raise

if __name__ == "__main__":
    main()
'''
        return script
            
    def stop_current_process(self):
        """Stop the current process and clean up properly."""
        try:
            if self.current_process:
                self.logger.info(f"Stopping {self.current_mode} mode...")
                
                if self.current_mode == "sorting" and isinstance(self.current_process, threading.Thread):
                    # For sorting mode, stop the restart loop
                    self.running = False
                    self.current_mode = None
                    
                    # Wait for thread to finish
                    if self.current_process.is_alive():
                        self.logger.info("Waiting for sorting thread to finish...")
                        self.current_process.join(timeout=3)  # Wait up to 3 seconds
                        
                        # Force kill if still alive
                        if self.current_process.is_alive():
                            self.logger.warning("Thread did not stop gracefully, forcing termination")
                    
                    self.logger.info("Sorting process stopped.")
                    
                elif hasattr(self.current_process, 'terminate'):
                    # For subprocess, terminate gracefully
                    try:
                        self.current_process.terminate()
                        self.current_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.logger.warning("Process did not terminate gracefully, killing forcefully")
                        self.current_process.kill()
                        self.current_process.wait(timeout=2)
                    self.logger.info("Subprocess stopped.")
                
                # Clean up card output if running
                if self.card and hasattr(self.card, 'is_running') and self.card.is_running:
                    try:
                        self.card.stop_output()
                        self.logger.info("Card output stopped.")
                    except Exception as e:
                        self.logger.warning(f"Error stopping card output: {e}")
                
                # Reset state
                self.current_process = None
                self.running = False
                self.current_mode = None
                
        except Exception as e:
            self.logger.error(f"Error stopping process: {e}")
            # Force cleanup even if error occurs
            self.current_process = None
            self.running = False
            self.current_mode = None
            
    def restart_current_mode(self):
        """Restart current mode with proper cleanup."""
        if not self.execution_started:
            messagebox.showwarning("No Execution Running", "Please start execution first.")
            return
            
        if self.current_mode:
            self.logger.info(f"Restarting {self.current_mode} mode...")
            
            # Store current mode
            mode_to_restart = self.current_mode
            
            # Stop current process first
            self.stop_current_process()
            
            # Brief pause to ensure cleanup
            time.sleep(0.5)
            
            # Restart the mode
            if mode_to_restart == "static":
                self.start_static_mode()
            elif mode_to_restart == "sorting":
                self.start_sorting_mode()
            else:
                self.logger.warning(f"Unknown mode to restart: {mode_to_restart}")
        else:
            self.logger.warning("No current mode to restart")
            
    def kill_program(self):
        """Kill the program with complete cleanup."""
        self.logger.info("Killing program...")
        
        try:
            # Stop any running processes
            self.stop_current_process()
            
            # Stop card output if running
            if self.card and hasattr(self.card, 'is_running') and self.card.is_running:
                try:
                    self.card.stop_output()
                    self.logger.info("Card output stopped during shutdown.")
                except Exception as e:
                    self.logger.warning(f"Error stopping card during shutdown: {e}")
            
            # Clean up any temporary files
            temp_script_path = "temp_sorting_script.py"
            if os.path.exists(temp_script_path):
                try:
                    os.remove(temp_script_path)
                    self.logger.info("Temporary script file cleaned up.")
                except Exception as e:
                    self.logger.warning(f"Error removing temporary file: {e}")
            
            self.logger.info("Program shutdown complete.")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        finally:
            # Always quit the GUI if it exists
            if hasattr(self, 'root') and self.root:
                try:
                    self.root.quit()
                except Exception as e:
                    self.logger.warning(f"Error quitting GUI: {e}")
        
    def on_closing(self):
        """Handle window closing - wipe logs and cleanup."""
        self.logger.info("GUI closing - wiping logs and cleaning up...")
        
        try:
            # Stop any running processes
            self.stop_current_process()
            
            # Stop card output if running
            if self.card and hasattr(self.card, 'is_running') and self.card.is_running:
                try:
                    self.card.stop_output()
                    self.logger.info("Card output stopped during shutdown.")
                except Exception as e:
                    self.logger.warning(f"Error stopping card during shutdown: {e}")
            
            # Clean up any temporary files
            temp_script_path = "temp_sorting_script.py"
            if os.path.exists(temp_script_path):
                try:
                    os.remove(temp_script_path)
                    self.logger.info("Temporary script file cleaned up.")
                except Exception as e:
                    self.logger.warning(f"Error removing temporary file: {e}")
            
            # Wipe the log file
            try:
                with open('toggle_controller.log', 'w') as f:
                    f.write("")  # Clear the file
                self.logger.info("Log file wiped successfully.")
            except Exception as e:
                self.logger.warning(f"Error wiping log file: {e}")
            
            self.logger.info("GUI shutdown complete.")
            
        except Exception as e:
            self.logger.error(f"Error during GUI shutdown: {e}")
        
        finally:
            # Always destroy the window
            self.root.destroy()
        
    def run(self):
        """Run the GUI."""
        self.root.mainloop()

    def stop_execution(self):
        """Stop execution by killing the actual processes and hardware output."""
        try:
            self.logger.info("Stopping execution - killing processes and hardware output...")
            
            # For static mode - stop the card output immediately
            if self.current_mode == "static":
                if self.card and hasattr(self.card, 'is_running') and self.card.is_running:
                    try:
                        self.card.stop_output()
                        self.logger.info("Static mode card output stopped.")
                    except Exception as e:
                        self.logger.warning(f"Error stopping static card output: {e}")
                
                # Also try to stop any real hardware card
                try:
                    if HARDWARE_AVAILABLE:
                        dwCard = wavgen.Card()
                        dwCard.stop_output()
                        self.logger.info("Real hardware static output stopped.")
                except Exception as e:
                    self.logger.warning(f"Error stopping real hardware: {e}")
            
            # For sorting mode - kill the subprocess and stop card
            elif self.current_mode == "sorting":
                # Stop the restart loop thread
                if self.current_process and isinstance(self.current_process, threading.Thread):
                    self.running = False
                    if self.current_process.is_alive():
                        self.logger.info("Stopping sorting thread...")
                        self.current_process.join(timeout=2)
                        if self.current_process.is_alive():
                            self.logger.warning("Thread did not stop gracefully")
                
                # Kill any running subprocess
                try:
                    # Find and kill the temp_sorting_script.py process
                    import psutil
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            if proc.info['cmdline'] and 'temp_sorting_script.py' in ' '.join(proc.info['cmdline']):
                                proc.terminate()
                                self.logger.info(f"Killed sorting subprocess PID: {proc.info['pid']}")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                except Exception as e:
                    self.logger.warning(f"Error killing sorting subprocess: {e}")
                
                # Stop card output
                if self.card and hasattr(self.card, 'is_running') and self.card.is_running:
                    try:
                        self.card.stop_output()
                        self.logger.info("Sorting mode card output stopped.")
                    except Exception as e:
                        self.logger.warning(f"Error stopping sorting card output: {e}")
            
            # Clean up temporary files
            temp_script_path = "temp_sorting_script.py"
            if os.path.exists(temp_script_path):
                try:
                    os.remove(temp_script_path)
                    self.logger.info("Temporary script file cleaned up.")
                except Exception as e:
                    self.logger.warning(f"Error removing temporary file: {e}")
            
            # Reset all state
            self.current_process = None
            self.running = False
            self.current_mode = None
            self.execution_started = False
            self.selected_mode = None
            
            # Reset GUI buttons
            self.static_select_button.config(state='normal')
            self.sorting_select_button.config(state='normal')
            self.start_execution_button.config(state='normal')
            self.stop_execution_button.config(state='disabled')
            self.restart_button.config(state='disabled')
            
            self.logger.info("Execution stopped - all processes and hardware output killed.")
            messagebox.showinfo("Execution Stopped", "All processes and hardware output have been stopped.")
            
        except Exception as e:
            error_msg = f"Error stopping execution: {e}"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)

def main():
    """Main function to run the Tkinter-based Wavgen Controller."""
    print("Initializing  Wavgen Controller...")
    
    # Always try real hardware by default
    controller = TkinterSequenceController(use_simulation=False)
    
    try:
        controller.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        controller.kill_program()
    except Exception as e:
        print(f"Unexpected error: {e}")
        controller.kill_program()

if __name__ == '__main__':
    main() 