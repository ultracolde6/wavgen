import wavgen
from wavgen import utilities
from wavgen.utilities import *
from wavgen.spectrum import *
from wavgen.constants import *
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

if __name__=='__main__':

    ntraps = 80  # this is the num of tweezers we want
    keep_num = 0
    spacing = 0.4E6
    startfreq = 104E6 - ntraps//2 * spacing


    folder_name = 'jiggle_waveforms'
    # create a new folder for waveforms to be saved to, if it doesn't already exist
    new_path = Path(folder_name)
    isdir = os.path.isdir(new_path)
    if not isdir:
        os.mkdir(f'{folder_name}')
        print(f'directory created')

    filename = Path(folder_name, 'drop_8.h5')

    if os.access(filename, os.F_OK):  # ...retrieve the Waveforms from file.
        print('Read file!')
        A = utilities.from_file(filename, 'A')
    else:
        f_list = np.array([startfreq + j * spacing for j in range(ntraps)])
        idx0 = int(ntraps/2-keep_num/2)
        f_list_static = f_list[idx0:idx0+keep_num]
        f_list_jiggle = np.concatenate((f_list[:idx0],f_list[idx0+keep_num:]))


        magsA = np.ones(ntraps)
        phase_diff = np.arange(ntraps) / (ntraps - 1) * 2 * np.pi
        phasesA = np.cumsum(phase_diff)

        A = wavgen.waveform.Superposition(freq_A, phases=phasesA)  # One via the default constructor...


        A.compute_waveform(filename, 'A')