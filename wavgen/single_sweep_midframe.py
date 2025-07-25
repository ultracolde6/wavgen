from wavgen.waveform import Superposition, Sweep1, Sweep_sequence, Sweep_loop
from time import time
import wavgen.constants
from wavgen import utilities
import os
import numpy as np
from pathlib import Path


if __name__ == '__main__':
    for fraction in [0]:
        # bias=1/fraction
        sweep_time=0.16
        sweep_mode="shiftedlinear"
        bias=0
        ntraps = 40
        shift_Lambda = 0 # 2 + 1 / 2 #+ 1 / 16
        Lambda = 0.16E6
        shift = shift_Lambda*Lambda
        CenterFreq = 104E6
        spacing = 5*Lambda
        com_shift = 0* Lambda/4
        startfreq = CenterFreq - 20*spacing  # 86.4E6 + 0.04E6 #88.04E6

        # freq_B = [88E6 +0.04E6+ 0.8E6*j for j in range(ntraps)]
        freq_B = [startfreq + com_shift + spacing*j for j in range(ntraps)] #+ -1/128 * 0.16E6*(-1)**(j+1)

        ##################################################
        # uniform stretch
        # CenterFreq = 104E6
        # spacingB = 5 *Lambda
        # com_shift = 1 * Lambda/4
        # startfreqB = CenterFreq - 20*spacingB  # 86.4E6 + 0.04E6 #88.04E6
        #
        # # freq_B = [88E6 +0.04E6+ 0.8E6*j for j in range(ntraps)]
        # freq_A = [startfreqB + com_shift + spacingB*j for j in range(ntraps)] #+ -1/128 * 0.16E6*(-1)**(j+1)

        ####################################################
        # two group
        sym_shift = 0 * Lambda
        left_shift = -0.25 * Lambda - sym_shift
        right_shift = 0.25 * Lambda + sym_shift

        freq_init = np.array([startfreq + com_shift + j * spacing for j in range(ntraps)])
        freq_A = freq_init * 1.0

        freq_A[:int(ntraps / 2)] = freq_init[:int(ntraps / 2)] + left_shift
        freq_A[int(ntraps / 2):] = freq_init[:int(ntraps / 2)] + right_shift



        # center_freq = freq_B[20]
        # print(center_freq)
        # twz_list = [center_freq]
        # for i in range(1, 20):
        #     twz_list.append(center_freq + 0.8E6 * i)
        # for i in range(1, 21):
        #     twz_list.append(center_freq - 0.8E6 * i)
        # freq_A = np.sort(twz_list)
        # freq_B = [88E6 + 0.8E6*j for j in range(ntraps)]
        # freq_B = []
        # for i in range(int(ntraps / 2)):
        #     freq_B.append(startfreq + i * spacing)
        # for j in range(int(ntraps / 2), ntraps):
        #     freq_B.append(startfreq + j * spacing + shift)
        # shift_list = np.zeros(ntraps)
        # for i in range(ntraps):
        #     if i % 2:
        #         shift_list[i] = -0.04E6
        #     else:
        #         shift_list[i] = 0.04E6
        # print(shift_list)
        # freq_A = shift_list + freq_A
        # folder_name = 'waveforms_100_40Twz_5lambda_hysteresis'
        folder_name = 'waveforms_80_40Twz_5lambda_susc-meas'
        # create a new folder for waveforms to be saved to, if it doesn't already exist


        new_path = Path(folder_name)
        isdir = os.path.isdir(new_path)
        if not isdir:
            os.mkdir(f'{folder_name}')
            print(f'directory created')

        name_temp = f'sweep_5lambda_twogroup_Delta=0l_back.h5'
        # name_temp = f'sweep_4,5to5lambda_fromleft.h5'
        filename = Path(folder_name, name_temp)
        # If we have already computed the Waveforms...
        # if os.access(filename + '.h5', os.F_OK):  # ...retrieve the Waveforms from file.
        if os.access(filename, os.F_OK):  # ...retrieve the Waveforms from file.

            print('file exists')
            AB = utilities.from_file(filename, 'AB')

        else:
            ## Define Waveform parameters ##
            print('computing new file')
            phase_diff = np.arange(ntraps) / (ntraps - 1) * 2 * np.pi
            phasesA = np.cumsum(phase_diff)
            phasesB = phasesA
            # phase_diff_1 = np.arange(int(ntraps / 2)) / (int(ntraps / 2) - 1) * 2 * np.pi
            # phases1 = np.cumsum(phase_diff_1)
            # phasesB = np.concatenate([phases1, phases1 + 2 * np.pi / (ntraps - 2)])

            print(freq_A)
            print(freq_B)

            ## Superpositions defined with lists of frequencies ##
            A = Superposition(freq_A, phases=phasesA) #, mags=magsA)

            B = Superposition(freq_B, phases=phasesB) #, mags=magsB)

            # ## A Sweep between the 2 previously defined stationary waves ##
            # AB = Sweep1(A, B, hold_time_a=0.5, hold_time_b= 0.5, sweep_time=0.2, ramp='cosine')
            # AB = Sweep_sequence(A, B, sweep_time=sweep_time, ramp='cosine', segment = False)
            AB = Sweep_sequence(A, B, sweep_time=sweep_time, ramp=sweep_mode, segment=False)

            AB.compute_waveform(filename, 'A')