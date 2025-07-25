import wavgen
from wavgen import utilities
from wavgen.waveform import SingleJiggle, SuperpositionJiggle, Superposition
from wavgen.utilities import *
from wavgen.spectrum import *
from wavgen.constants import *
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path



if __name__=='__main__':
    folder_name = 'jiggle_waveforms'
    # create a new folder for waveforms to be saved to, if it doesn't already exist
    new_path = Path(folder_name)
    isdir = os.path.isdir(new_path)
    if not isdir:
        os.mkdir(f'{folder_name}')
        print(f'directory created')
    mod_freq = 64e3
    mod_amp = 0.4e6
    filename = Path(folder_name, f'jiggle_amp={mod_amp*1e-3:.1f}kHz_freq={mod_freq*1e-3:.1f}kHz.h5')
    # filename = Path(folder_name, 'drop_1_twz20.h5')

    if os.access(filename, os.F_OK) and False:  # ...retrieve the Waveforms from file.
        print('Read file!')
        A = utilities.from_file(filename, 'A')
    else:
        spacing = 0.4E6
        ntraps = 80 #60
        startfreq =  104E6 - ntraps//2 * spacing  # 80.248E6 # 99E6 0.719E6 * 125
        base_freqs = np.array([startfreq + spacing * j for j in range(ntraps)])

        if ntraps == 1:
            base_phases = [0]
        else:
            phase_diff = np.arange(ntraps) / (ntraps - 1) * 2 * np.pi
            base_phases = np.cumsum(phase_diff)

        # mod_freqs = 70 * np.ones(ntraps) * 1E3 # 67
        mod_freqs = np.array(mod_freq * np.ones(ntraps), dtype=int)
        # mod_freqs = np.array(71.9E3 * np.ones(ntraps), dtype=int)

        # mod_amps = 50 * np.ones(ntraps) * 1E3
        mod_amps = mod_amp * np.ones(ntraps) # 1/8lambda
        # mod_amps = 500 * np.ones(ntraps) * 1E3 # 1/8lambda

        print(mod_freqs)

        mod_forms = np.empty(len(base_freqs), dtype='object')
        mod_forms[:] = "Sine"  # if you choose Toggle, it's very slow to compute the waveform.
        # for ii in range(19, 22):
        #     mod_forms[ii] = "Off"
        # for ii in np.arange(12, 28, 2):
        #     mod_forms[ii] = "Off"
        # for ii in range(20,40):
        #     mod_forms[ii] = "Off"
        # mod_forms[29] = "Off"
        # mod_forms[20] = "Off"
        # mod_forms[13] = "Off"



        # base_amps = (1 + 2.9E-3 * (base_freqs/1E6-103)**2)/(1 + 2.9E-3 * (120-103)**2)
        base_amps = np.ones(ntraps)
        # print(f"base_amps={base_amps}")

        A = SuperpositionJiggle(base_freqs=base_freqs, base_phases=base_phases, base_amps=base_amps,
                                mod_freqs=mod_freqs, mod_amps=mod_amps, mod_forms=mod_forms)
        # A = Superposition(freqs=base_freqs, phases=base_phases, mags=base_amps)
        print('there')
        A.compute_waveform(filename, 'A')
