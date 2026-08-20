import subprocess
import sys
import signal
import atexit
import time

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

restart_count = 0
restart_delay = 2

# earlier I had added this thing to kill the process fully on exit - this ended up interfering with the automatic restart of runner
# Now fixing it to not have that problem... oops
while True:
    try:
        print("Starting rearrangement sequence...")
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop.py"])
        # process = subprocess.Popen([sys.executable, "rearrangement_double_sort_multidrop_dropsingle.py"])
        process = subprocess.Popen([sys.executable, "rearrangement_double_sort_multidrop_dropdoublev2.py"])
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop.py"])
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop_mcm.py"])
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop - 70 tweezerdrop to 40.py"]) # Used for MW/Chi measurement.
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop - 70 tweezerdrop to 40 new.py"])
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop - 70 tweezer.py"])
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop - 70 tweezerdrop to 46.py"])
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_loop_frames-downto-40.py"])
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_loop_frames.py"])
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_loop_frames-70-downto-40_perp_contrast.py"])   # use for free space perp contrast run
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_loop_frames-downto-40_101.44.py"])   # use for spins as of 3/12/26
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_loop_frames-downto-40_101.44_v2.py"]) # use for spins as of 1/13/26
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop.py"]) # use for multi-loop Rydberg and uw spectroscopy as of 1/14/26
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_loop_frames_rydberg_add_loading_sweep_v2.py"]) # use for multi-loop Rydberg with sweep to larger spacing 7/10/26
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_loop_frames_rydberg_centergroup_sidereservoir.py"]) # use for multi-loop Rydberg with sweep to larger spacing 7/10/26

        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_loop_frames_rydberg_blockade_v2.py"])  # use for multi-loop Rydberg blockaded Rabi
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop_blockade.py"]) # use for multi-loop Rydberg and uw spectroscopy as of 1/14/26
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop - 40 tweezerdrop to 22.py"])
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop_40twz_101.44.py"])

        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_loop_frames-downto-40_101.44.py"])   # use for spins as of 3/12/26
        # process = subprocess.Popen([sys.executable, "rearrangement_sequence_loop_frames-downto-40_final_spin_detect.py"])
        current_process = process
        return_code = process.wait()
        
        # Process has exited
        current_process = None
        restart_count += 1
        
        if return_code == 0:
            print("Process exited normally (return code 0).")
            # break

        else:
            print(f"Process exited with error code {return_code} (exception or error occurred).")
            print(f"Restarting... (restart count: {restart_count})")
            time.sleep(restart_delay)  
            
    except KeyboardInterrupt:
        print("\nReceived KeyboardInterrupt. Cleaning up...")
        cleanup_process()
        sys.exit(0)

    except Exception as e:
        print(f"Exception occurred while running subprocess: {e}")
        cleanup_process()
        restart_count += 1
        print(f"Restarting... (restart count: {restart_count})")
        time.sleep(restart_delay)