import subprocess
import sys
import signal
import atexit

current_process = None

def cleanup_process():
    """Kill the subprocess if it's still running."""
    global current_process
    if current_process is not None:
        try:
            # Windows commands to kill process and all its children
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(current_process.pid)], 
                         capture_output=True, check=False)
            current_process = None
            print("\nSubprocess terminated.")
        except (ProcessLookupError, OSError, ValueError):
            current_process = None

def signal_handler(signum, frame):
    """Handle termination signals."""
    print(f"\nReceived signal {signum}. Cleaning up...")
    cleanup_process()
    sys.exit(0)

# Handlers that kill process if we terminate it
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

# Register cleanup function to run on exit
atexit.register(cleanup_process)

while True:
    print("Starting rearrangement sequence...")
    # this file would just be modified to be the name and path of wavegen
    # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop.py"])
    # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop - 70 tweezer.py"])
    process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop - 70 tweezerdrop to 40.py"])
    # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop - 70 tweezerdrop to 46.py"])
    
    current_process = process
    
    try:
        process.wait()
    except KeyboardInterrupt:
        cleanup_process()
        sys.exit(0)
    
    current_process = None
    print("Trigger has been missed. Wavegen has died. Restarting...")