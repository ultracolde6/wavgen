import subprocess
import time
import sys

while True:
    print("Starting rearrangement sequence...")
    # this file would just be modified to be the name and path of wavegen
    process = subprocess.Popen([sys.executable, "rearrangement_sequence_double_sort_multidrop.py"])
    process.wait()
    print("Trigger has been missed. Wavegen has died. Restarting...")