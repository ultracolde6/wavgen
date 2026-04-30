import subprocess
import sys

while True:
    print("Starting rearrangement sequence...")
    # this file would just be modified to be the name and path of wavegen
    # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop.py"])
    # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop - 70 tweezerdrop to 40 new.py"])
    # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop - 70 tweezer.py"])
    # process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop - 70 tweezerdrop to 46.py"])
    process = subprocess.Popen([sys.executable, "rearrangement_sequence_loop_frames-downto-40.py"])
    current_process = process
    
    print("Trigger has been missed. Wavegen has died. Restarting...")
