from wavgen.waveform import Superposition, Sweep1, Sweep_sequence, Sweep_loop
from time import time
import wavgen.constants
from wavgen import utilities
import os
import numpy as np
from pathlib import Path


if __name__ == '__main__':

    ntraps = 40  # this is the num of tweezers we want0
    spacing = 0.799E6
    startfreq = 87.89E6
    ind = 20
    folder_name = 'waveforms_160_40Twz_5lambda_v1'

    # create a new folder for waveforms to be saved to, if it doesn't already exist
    new_path = Path(folder_name)
    isdir = os.path.isdir(new_path)
    if not isdir:
        os.mkdir(f'{folder_name}')
        print(f'directory created')

    name_temp = f'sweep_single_{ind}_back.h5'
    filename = Path(folder_name, name_temp)
    # If we have already computed the Waveforms...
    if os.access(filename, os.F_OK):  # ...retrieve the Waveforms from file.
        print('file exists')
        AB = utilities.from_file(filename, 'AB')

    else:
        ## Define Waveform parameters ##
        print('computing new file')
        phase_diff = np.arange(ntraps) / (ntraps - 1) * 2 * np.pi
        phasesB = np.cumsum(phase_diff)

        freq_B = [startfreq + j * spacing for j in range(ntraps)]
        print(freq_B)
        phasesA = phasesB

        freq_A = freq_B
        freq_A[ind] += 0.04E6

        print(freq_B)

        ## Superpositions defined with lists of frequencies ##
        A = Superposition(freq_A, phases=phasesA) #, mags=magsA)

        B = Superposition(freq_B, phases=phasesB) #, mags=magsB)

        # ## A Sweep between the 2 previously defined stationary waves ##
        AB = Sweep_sequence(A, B, sweep_time=0.16, ramp='cosine', segment = False)

        AB.compute_waveform(filename, 'AB')
