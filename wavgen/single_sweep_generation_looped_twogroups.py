from wavgen.waveform import Superposition, Sweep1, Sweep_sequence, Sweep_loop
from time import time
import wavgen.constants
from wavgen import utilities
import os
import numpy as np
from pathlib import Path



if __name__ == '__main__':
    folder_name = 'waveforms_80_40Twz_5lambda_susc-meas-TEST'
    # create a new folder for waveforms to be saved to, if it doesn't already exist
    # new_path = Path(folder_name,"SWEEP")
    # isdir = os.path.isdir(new_path)
    # if not isdir:
    #     os.mkdir(new_path)
    #     print(f'directory created')



    ntraps = 40
    Lambda = 0.16E6
    CenterFreq =104E6
    sweeptime_ms = 0.16


    spacing_Lambda_A = 5
    stagger_Lambda_A = 0
    shift_Lambda_A = 0
    twogroup_shift_Lambda_A = 0


    spacing_Lambda_B = 5
    stagger_Lambda_B = 0
    shift_Lambda_B = 0
    # twogroup_shift_Lambda_B = 1/4


    for fraction in [-3/80,-5/128]:
        twogroup_shift_Lambda_B = 1.25

        spacing_A = spacing_Lambda_A * Lambda  # 0.8E6
        shift_A = shift_Lambda_A * Lambda  # 0.8E6
        stagger_A = stagger_Lambda_A * Lambda  # 0.8E6
        startfreq_A = CenterFreq - 20 * spacing_A + shift_A
        twogroup_shift_A = twogroup_shift_Lambda_A * Lambda
        freq_A = np.array([startfreq_A + j * spacing_A + stagger_A * (-1) ** (j + 1) for j in range(ntraps)])
        freq_A[:int(ntraps / 2)] = freq_A[:int(ntraps / 2)] - twogroup_shift_A
        freq_A[int(ntraps / 2):] = freq_A[int(ntraps / 2):] + twogroup_shift_A

        spacing_B = spacing_Lambda_B * Lambda  # 0.8E6
        shift_B = shift_Lambda_B * Lambda  # 0.8E6

        stagger_B = stagger_Lambda_B * Lambda  # 0.8E6
        startfreq_B = CenterFreq - 20 * spacing_B + shift_B
        twogroup_shift_Lambda_B += fraction
        twogroup_shift_B = twogroup_shift_Lambda_B * Lambda
        freq_B = np.array([startfreq_B + j * spacing_B + stagger_B * (-1) ** (j + 1) for j in range(ntraps)])
        freq_B[:int(ntraps / 2)] = freq_B[:int(ntraps / 2)] - twogroup_shift_B
        freq_B[int(ntraps / 2):] = freq_B[int(ntraps / 2):] + twogroup_shift_B

        # filename = Path(folder_name, f'SWEEP/from_(sp={spacing_Lambda_A:.5f}L'
        #                              f'_sh={shift_Lambda_A:.5f}L'
        #                              f'_st={stagger_Lambda_A:.5f}L)_'
        #                              f'to_(sp={spacing_Lambda_B:.5f}L'
        #                              f'_sh={shift_Lambda_B:.5f}L'
        #                              f'_st={stagger_Lambda_B:.5f}L)_'
        #                              f'in_{sweeptime_ms:.3f}ms.h5')
        filename = Path(folder_name, f'sweep_to_5lambda_twogroup_node_Delta={fraction}l.h5')

        if os.access(filename, os.F_OK):  # ...retrieve the Waveforms from file.
            print('Read file!')
            AB = utilities.from_file(filename, 'A')
        else:
            ## Define Waveform parameters ##
            print('computing new file')
            phase_diff = np.arange(ntraps) / (ntraps - 1) * 2 * np.pi
            phasesA = np.cumsum(phase_diff)
            phasesB = phasesA

            print(freq_A)
            print(freq_B)

            ## Superpositions defined with lists of frequencies ##
            A = Superposition(freq_A, phases=phasesA) #, mags=magsA)
            B = Superposition(freq_B, phases=phasesB) #, mags=magsB)

            # ## A Sweep between the 2 previously defined stationary waves ##
            AB = Sweep_sequence(A, B, sweep_time=sweeptime_ms, ramp="shiftedlinear", segment = False)
            AB.compute_waveform(filename, 'A')