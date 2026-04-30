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
        sweep_time = 0.16
        sweep_mode = 'cosine'
        bias=0
        ntraps = 40
        shift_Lambda = 0 # 2 + 1 / 2 #+ 1 / 16
        Lambda = 0.16E6
        shift = shift_Lambda*Lambda
        # CenterFreq = 101.44E6
        CenterFreq = 102.72E6
        spacing = 4*Lambda
        com_shift = 0* Lambda/4
        startfreq = CenterFreq - ntraps/2 * spacing  # 86.4E6 + 0.04E6 #88.04E6

        # freq_B = [88E6 +0.04E6+ 0.8E6*j for j in range(ntraps)]
        freq_A = [startfreq + com_shift + spacing*j for j in range(ntraps)] #+ -1/128 * 0.16E6*(-1)**(j+1)
        # freq_B = [startfreq + com_shift + spacing*j for j in range(ntraps)] #+ -1/128 * 0.16E6*(-1)**(j+1)
        phase_diff = np.arange(ntraps) / (ntraps - 1) * 2 * np.pi
        phasesA = np.cumsum(phase_diff)

        ##################################################
        # # uniform stretch
        # # CenterFreq = 101.44E6
        # CenterFreq = 102.72E6
        # spacingB = 4.5 * Lambda
        # com_shift =  0*Lambda/4
        # startfreqB = CenterFreq - ntraps/2 * spacingB  # 86.4E6 + 0.04E6 #88.04E6
        # freq_B = [startfreqB + com_shift + spacingB*j for j in range(ntraps)] #+ -1/128 * 0.16E6*(-1)**(j+1)
        # phasesB = phasesA

        ####################################################
        # two group
        sym_shift = 0 * Lambda
        left_shift = -1.25 * Lambda - sym_shift
        right_shift = 1.25 * Lambda + sym_shift

        freq_init = np.array([startfreq + com_shift + j * spacing for j in range(ntraps)])
        freq_B = freq_init * 1.0

        freq_B[:int(ntraps / 2)] = freq_init[:int(ntraps / 2)] + left_shift
        freq_B[int(ntraps / 2):] = freq_init[int(ntraps / 2):] + right_shift




        phase_diff_1 = np.arange(int(ntraps / 2)) / (int(ntraps / 2) - 1) * 2 * np.pi
        phase_diff_2 = np.arange(1, int(ntraps / 2)+1) / (int(ntraps / 2) - 1) * 2 * np.pi
        phases1 = np.cumsum(phase_diff_1)
        phases2 = np.cumsum(phase_diff_2)
        phasesB = np.concatenate([phases1, phases2])
        # phasesB = np.concatenate([phases1, -phases1])

        # phasesB = phasesA

        ####################################################

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
        # folder_name = 'waveforms_80_40Twz_5lambda_susc-meas'
        folder_name = 'four lambda spacing - 70 tweezers'
        # create a new folder for waveforms to be saved to, if it doesn't already exist


        new_path = Path(folder_name)
        isdir = os.path.isdir(new_path)
        if not isdir:
            os.mkdir(f'{folder_name}')
            print(f'directory created')

        # name_temp = f'70tweezers_sweep_to_halfint_node.h5'
        # name_temp = f'40tweezers_102.72center_sweep_to_4.5L_antinode.h5'
        name_temp = f'40tweezers_102.72center_sweep_from_two_groups_new.h5'
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


            ################## the following minimizes cost function 3 ##########################
            # phasesA = np.array([ -1.14254421e-01, -1.91730193e-01, 8.48065418e-02, 2.04235594e-01,
            #                      7.27589378e-01, 1.64693962e+00, 2.23424824e+00, 3.89016556e+00,
            #                      4.36346004e+00, 5.91085170e+00, 7.40510848e+00, 8.89809238e+00,
            #                      1.05167619e+01, 1.25341858e+01, 1.47477671e+01, 1.72211853e+01,
            #                      1.95716544e+01, 2.18883146e+01, 2.45402847e+01, 2.75826692e+01,
            #                      3.06437088e+01, 3.37234011e+01, 3.71935083e+01, 4.09989265e+01,
            #                      4.47705366e+01, 4.84191976e+01, 5.23276925e+01, 5.64323475e+01,
            #                      6.09357548e+01, 6.55648507e+01, 7.01926692e+01, 7.47673572e+01,
            #                      8.04161415e+01, 8.48823005e+01, 9.04170711e+01, 9.56197995e+01,
            #                      1.01218521e+02, 1.07221170e+02, 1.13066712e+02, 1.19266267e+02 ])
            #######################################################################################


            print(freq_A)
            print(freq_B)

            ## Superpositions defined with lists of frequencies ##
            B = Superposition(freq_A, phases=phasesA) #, mags=magsA)

            A = Superposition(freq_B, phases=phasesB) #, mags=magsB)

            # ## A Sweep between the 2 previously defined stationary waves ##
            # AB = Sweep1(A, B, hold_time_a=0.5, hold_time_b= 0.5, sweep_time=0.2, ramp='cosine')
            # AB = Sweep_sequence(A, B, sweep_time=sweep_time, ramp='cosine', segment = False)
            AB = Sweep_sequence(A, B, sweep_time=sweep_time, ramp=sweep_mode, segment=False)

            AB.compute_waveform(filename, 'A')