from wavgen.waveform import Superposition, Sweep1, Sweep_sequence, Sweep_loop
from time import time
import wavgen.constants
from wavgen import utilities
import os
import numpy as np
from pathlib import Path
import ipyparallel as ipp

if __name__ == '__main__':
    max_list = []

    ntraps = 41  # this is the num of tweezers we want, plus 1

    spacing = 0.800E6

    for sweep_mode in ["shiftedlinear"]:
        for sweep_time in [0.08]:

            for sweep_num in np.arange(ntraps-2)+1:

                phase_diff = np.arange(ntraps - 1) / (ntraps - 2) * 2 * np.pi
                phasesB = np.cumsum(phase_diff)

                # f_list[ind] += 0.04E6
                freq_A = []
                phasesA = []

                ############## for R to L:#########################
                #
                startfreq = 88.04E6 # need to -spacing for L waveforms, don't for R waveforms
                f_list = [startfreq + j * spacing for j in range(ntraps)]

                for i in range(ntraps):
                    if i < ntraps - 2 - sweep_num:
                        freq_A.append(f_list[i])
                    if i >= ntraps - 1 - sweep_num:
                        freq_A.append(f_list[i])

                freq_B = f_list[:-1] # for R sweeps
                #
                for i in range(len(phasesB)):
                    if i < len(phasesB) - sweep_num - 1:
                        phasesA.append(phasesB[i])
                    elif i >= len(phasesB) - sweep_num:
                        phasesA.append(phasesB[i])
                # phasesA.append(phasesB[len(phasesB) - sweep_num - 1])
                phasesA.append(phasesB[-1])
                # phasesA = phasesB

               ##############################################################
                print(freq_A)
                print(freq_B)

                ## Superpositions defined with lists of frequencies ##
                # max_list = []
                A = Superposition(freq_A, phases=phasesA) #, mags=magsA)

                B = Superposition(freq_B, phases=phasesB) #, mags=magsB)

                # ## A Sweep between the 2 previously defined stationary waves ##
                # AB = Sweep1(A, B, hold_time_a=0.5, hold_time_b= 0.5, sweep_time=0.2, ramp='cosine')
                AB = Sweep_sequence(A, B, sweep_time=sweep_time, ramp=sweep_mode, segment = False)

                max_list.append(AB.compute_waveform())
                print("######################")

            for sweep_num in np.arange(ntraps - 2) + 1:

                phase_diff = np.arange(ntraps - 1) / (ntraps - 2) * 2 * np.pi
                phasesB = np.cumsum(phase_diff)

                freq_A = []
                phasesA = []

                ####################for L to R:########################

                startfreq = 88.04E6 - spacing  # need to -spacing for L waveforms, don't for R waveforms
                f_list = [startfreq + j * spacing for j in range(ntraps)]
                for i in range(ntraps):
                    if i <= sweep_num:
                        freq_A.append(f_list[i])
                    if i > sweep_num+1:
                        freq_A.append(f_list[i])
                #
                for i in range(len(phasesB)):
                    if i == 0:
                        # phasesA.append(phasesB[sweep_num])
                        phasesA.append(phasesB[0])
                    elif 0 < i <= sweep_num:
                        phasesA.append(phasesB[i-1])
                    else:
                        phasesA.append(phasesB[i])

                freq_B = f_list[1:]

                ##############################################################
                print(freq_A)
                print(freq_B)

                ## Superpositions defined with lists of frequencies ##
                # max_list = []
                A = Superposition(freq_A, phases=phasesA)  # , mags=magsA)

                B = Superposition(freq_B, phases=phasesB)  # , mags=magsB)

                # ## A Sweep between the 2 previously defined stationary waves ##
                # AB = Sweep1(A, B, hold_time_a=0.5, hold_time_b= 0.5, sweep_time=0.2, ramp='cosine')
                AB = Sweep_sequence(A, B, sweep_time=sweep_time, ramp=sweep_mode, segment=False)
                max_list.append(AB.compute_waveform())
                # print(AB.sample_length)
                print("######################")
    print(f"max_list={max_list}")
    print(f'optimal norm is {np.min(wavgen.constants.SAMP_VAL_MAX / np.array(max_list))}')