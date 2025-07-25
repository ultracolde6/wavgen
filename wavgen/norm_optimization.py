from wavgen.waveform import Superposition, Sweep1, Sweep_sequence, Sweep_loop
from time import time
import wavgen.constants
from wavgen import utilities
import os
import numpy as np


if __name__ == '__main__':
    ntraps = 41  # this is the num of tweezers we want, plus 1
    max_list = []

    phase_diff = np.arange(ntraps-1) / (ntraps - 2) * 2 * np.pi
    phasesB = np.cumsum(phase_diff)

    sweep_mode = "shiftedlinear"
    sweep_time = 0.08
    spacing = 0.8E6
    # ind = 14 # the index of the tweezer we want to displace. Need to -1 for R to L

    startfreq = 88.04E6  # need to -spacing for L waveforms, don't for R waveforms

    f_list = [startfreq + j * spacing for j in range(ntraps)]
    # f_list[ind] += 0.04E6
    print(f_list)
    freq_A = []
    phasesA = []
    for sweep_num in range(1, ntraps-1):

       ############################# for L to R:
        for i in range(ntraps):
            if i <= sweep_num:
                freq_A.append(f_list[i])
            if i > sweep_num+1:
                freq_A.append(f_list[i])

        for i in range(len(phasesB)):
            if i == 0:
                # phasesA.append(phasesB[sweep_num])
                phasesA.append(phasesB[0])
            elif 0 < i <= sweep_num:
                phasesA.append(phasesB[i-1])
            else:
                phasesA.append(phasesB[i])

        freq_B = f_list[1:]
        ## Superpositions defined with lists of frequencies ##
        A = Superposition(freq_A, phases=phasesA)  # , mags=magsA)

        B = Superposition(freq_B, phases=phasesB)  # , mags=magsB)

        # ## A Sweep between the 2 previously defined stationary waves ##
        AB = Sweep_sequence(A, B, sweep_time=sweep_time, ramp=sweep_mode, segment = False)

        max_list.append(AB.compute_waveform())
######################################################### R to L below ###################
    spacing = 0.8E6
    startfreq = 88.04E6 - spacing  # need to -spacing for L waveforms, don't for R waveforms

    f_list = [startfreq + j * spacing for j in range(ntraps)]
    freq_A = []
    phasesA = []
    for sweep_num in range(1, ntraps-1):

        for i in range(ntraps):
            if i < ntraps - 2 - sweep_num:
                freq_A.append(f_list[i])
            if i >= ntraps - 1 - sweep_num:
                freq_A.append(f_list[i])

        for i in range(len(phasesB)):
            if i < len(phasesB) - sweep_num - 1:
                phasesA.append(phasesB[i])
            elif i >= len(phasesB) - sweep_num:
                phasesA.append(phasesB[i])
        # phasesA.append(phasesB[len(phasesB) - sweep_num - 1])
        phasesA.append(phasesB[-1])

        freq_B = f_list[:-1]  # for R sweeps

        ## Superpositions defined with lists of frequencies ##
        A = Superposition(freq_A, phases=phasesA)  # , mags=magsA)

        B = Superposition(freq_B, phases=phasesB)  # , mags=magsB)

        # ## A Sweep between the 2 previously defined stationary waves ##
        AB = Sweep_sequence(A, B, sweep_time=sweep_time, ramp=sweep_mode, segment = False)

        max_list.append(AB.compute_waveform())

    print(freq_B)
    print(f"max_list={max_list}")
    print(f'optimal norm is {np.min(wavgen.constants.SAMP_VAL_MAX / np.array(max_list))}')


