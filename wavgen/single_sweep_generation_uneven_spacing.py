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
        sweep_time=0.24 # in units of ms
        sweep_mode="cosine"
        bias=0
        ntraps = 25
        ntraps_temp=65
        shift_Lambda = 0 #+ 1 / 16
        Lambda = 0.16E6
        shift = shift_Lambda*Lambda
        CenterFreq = 101.44E6
        spacing_A = 6*Lambda
        spacing_B = 4*Lambda
        com_shift = 0
        startfreq_A = 89.92E6 #CenterFreq - ntraps//2 * spacing_A  # 86.4E6 + 0.04E6 #88.04E6
        startfreq_B = 80E6 #  CenterFreq - ntraps/2 * spacing_B  # 86.4E6 + 0.04E6 #88.04E6

        # freq_A = [startfreq + j*spacing + stagger*(-1)**(j+1) for j in range(ntraps)]
        # freq_A = [startfreq + com_shift + j * spacing for j in range(ntraps)]
        # freq_A = np.array([startfreq +shift +  j * spacing for j in range(ntraps)])


        # #### For uneven spacing 4and12lambda #####
        # freq_temp = np.array([startfreq_B + shift + j * spacing_B for j in range(ntraps_temp)])
        # mask_freqs = np.ones(len(freq_temp))
        # mask_freqs[11:29] = 0
        # mask_freqs[30:32] = 0
        # mask_freqs[33:35] = 0
        # mask_freqs[36:54] = 0

        # #### For uneven spacing 4and12lambda 2centered 12lambda #####
        # freq_temp = np.array([startfreq_B + shift + j * spacing_B for j in range(ntraps_temp)])
        # mask_freqs = np.ones(len(freq_temp))
        # mask_freqs[11:32] = 0
        # mask_freqs[33:35] = 0
        # mask_freqs[36:54] = 0

        #### For uneven spacing 4lambda 2centered 4lambda #####
        freq_temp = np.array([startfreq_B + shift + j * spacing_B for j in range(ntraps_temp)])
        mask_freqs = np.ones(len(freq_temp))
        mask_freqs[12:32] = 0
        mask_freqs[34:54] = 0

        mask_freqs_bool = mask_freqs > 0.1
        freq_B = freq_temp[mask_freqs_bool]
        ntraps = len(freq_B)  # num tweezers we want


        # freq_B = [69.44E6 + spacing_B*j for j in range(ntraps)]
        # freq_B = [85.44E6 + spacing_B*j for j in range(ntraps)]

        # freq_B = [startfreq_B + com_shift + spacing_B*j for j in range(ntraps)] #+ -1/128 * 0.16E6*(-1)**(j+1)
        freq_A = [startfreq_A + com_shift + spacing_A*j for j in range(ntraps)] #+ -1/128 * 0.16E6*(-1)**(j+1)
        # freq_A =[91.44E6 + spacing_A*j for j in range(ntraps)]
        # freq_A =[startfreq_A + spacing_A*j for j in range(ntraps)]
        # print(len(freq_A), len(freq_B))

        # center_freq = freq_B[20]
        # print(center_freq)
        # twz_list = [center_freq]
        # for i in range(1, 20):
        #     twz_list.append(center_freq + 0.8E6 * i)
        # for i in range(1, 21):
        #     twz_list.append(center_freq - 0.8E6 * i)
        # freq_A = np.sort(twz_list)
        # freq_B = [88E6 + 0.8E6*j for j in range(ntraps)]



        # freq_B = [9.54720e+07 ,1.00000e+08 ,1.04000e+08, 1.08000e+08, 1.11472e+08]
        # for i in range(ntraps):
        #     freq_B.append(startfreq + i * spacing)
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
        # folder_name = 'Centered_Uneven_16and4lambda-TwentyFourTweezers'
        folder_name = 'Centered_uneven_4lambda_spacing_2centered_4lambda'
        # create a new folder for waveforms to be saved to, if it doesn't already exist


        new_path = Path(folder_name)
        isdir = os.path.isdir(new_path)
        if not isdir:
            os.mkdir(f'{folder_name}')
            print(f'directory created')

        name_temp = f'sweep_6lambda_to_uneven_240us.h5'
        filename = Path(folder_name, name_temp)
        # If we have already computed the Waveforms...
        # if os.access(filename + '.h5', os.F_OK):  # ...retrieve the Waveforms from file.
        if os.access(filename, os.F_OK):  # ...retrieve the Waveforms from file.

            print('file exists')
            AB = utilities.from_file(filename, 'AB')

        else:
            ## Define Waveform parameters ##
            print('computing new file')
            # ntraps_temp=ntraps
            # phase_diff = np.arange(ntraps_temp) / (ntraps_temp - 1) * 2 * np.pi
            phase_diff = np.arange(ntraps) / (ntraps - 1) * 2 * np.pi
            phasesA = np.cumsum(phase_diff)
            phasesB = np.cumsum(phase_diff)
            # phase_diff_1 = np.arange(int(ntraps / 2)) / (int(ntraps / 2) - 1) * 2 * np.pi
            # phases1 = np.cumsum(phase_diff_1)
            # phasesB = np.concatenate([phases1, phases1 + 2 * np.pi / (ntraps - 2)])

            print(freq_A)
            print(freq_B)

            ## Superpositions defined with lists of frequencies ##
            A = Superposition(freq_A, phases=phasesA) #, mags=magsA)
            print(freq_B)
            B = Superposition(freq_B, phases=phasesB) #, mags=magsB)

            # ## A Sweep between the 2 previously defined stationary waves ##
            # AB = Sweep1(A, B, hold_time_a=0.5, hold_time_b= 0.5, sweep_time=0.2, ramp='cosine')
            # AB = Sweep_sequence(A, B, sweep_time=sweep_time, ramp='cosine', segment = False)
            AB = Sweep_sequence(A, B, sweep_time=sweep_time, ramp=sweep_mode, segment=False)

            AB.compute_waveform(filename, 'A')