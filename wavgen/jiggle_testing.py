from wavgen.waveform import Superposition, Sweep1, Sweep_sequence, Sweep_loop
from wavgen.waveform_jiggle import SingleJiggle, SuperpositionJiggle
from time import time
import wavgen.constants
from wavgen import utilities
import os
import numpy as np
from pathlib import Path



if __name__=='__main__':

    # base_freq = 90E6
    # mod_freq = 55E3
    # mod_amp = 3E3
    #
    # A = SingleJiggle(base_freq=base_freq, mod_freq=mod_freq, mod_amp=mod_amp, mod_form = "Sine")


    startfreq = 88.228E6 #80.248E6 # 99E6
    ntraps = 40
    base_freqs = [startfreq + 0.798 * 1E6*j for j in range(ntraps)]

    if ntraps == 1:
        base_phases = [0]
    else:
        phase_diff = np.arange(ntraps) / (ntraps - 1) * 2 * np.pi
        base_phases = np.cumsum(phase_diff)

    mod_freqs = 57*np.ones(ntraps)*1E3
    mod_amps = 3* np.ones(ntraps)*1E3

    mod_forms = np.empty(len(base_freqs) , dtype='object')
    mod_forms[:] = "Sine" #if you choose Toggle, it's very slow to compute the waveform.
    # for ii in range(10,20):
    #     mod_forms[ii] = "Off"
    # for ii in range(20,40):
    #     mod_forms[ii] = "Off"

    print(mod_forms)

    A = SuperpositionJiggle(base_freqs=base_freqs, base_phases=base_phases, mod_freqs=mod_freqs, mod_amps=mod_amps, mod_forms=mod_forms)
    # A = Superposition(freqs=base_freqqs, phases=base_phases)

    dwCard = wavgen.Card()
    dwCard.setup_channels(amplitude = 80, use_filter=False)

    # dwCard.stabilize_intensity(A,which_cam=0)

    dwCard.load_waveforms(A)
    dwCard.wiggle_output(duration=0)