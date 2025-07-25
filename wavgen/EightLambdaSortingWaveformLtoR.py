from wavgen.waveform import Superposition, Sweep1, Sweep_sequence, Sweep_loop
from time import time
import wavgen.constants
from wavgen import utilities
import os
import numpy as np
from pathlib import Path


if __name__ == '__main__':

    ntraps = 31  # this is the num of tweezers we want, plus 1
    # keep_num = 30
    # center_freq = 100.3E6
    # center_freq = 101.26E6
    # spacing = 0.639E6 # 4lambda
    # spacing = 0.882E6 # 5.5lambda
    # spacing = 0.799E6
    # spacing = 0.719E6
    twz_lambda = 0.16e6
    spacing = 8 * twz_lambda
    # spacing = 0.800E6
    # if keep_num % 2 == 0:
    #     startfreq = center_freq - round(spacing/2*10**(-6), 3)*10**6 - (keep_num/2 - 1 + ntraps - keep_num)*spacing
    # else:
    #     startfreq = center_freq - (int(keep_num/2) + ntraps - keep_num)*spacing
    # startfreq = 87.89E6 #-spacing  #96.208E6 - spacing # the first tweezer in the wanted array minus 1 tweezer spacing for the extra moving tweezer
    # startfreq = 80.248E6 - spacing # the first tweezer in the wanted array minus 1 tweezer spacing for the extra moving tweezer
    # startfreq = 88E6 - spacing # need to -spacing for L waveforms, don't for R waveforms

    # ind = 14
    folder_name = 'EightLambda'
    # create a new folder for waveforms to be saved to, if it doesn't already exist


    new_path = Path(folder_name)
    isdir = os.path.isdir(new_path)
    if not isdir:
        os.mkdir(f'{folder_name}')
        print(f'directory created')
    for sweep_num in np.arange(ntraps-2)+1:
        name_temp = 'sweep_{}.h5'.format(sweep_num)
        filename = Path(folder_name, name_temp)
        # If we have already computed the Waveforms...
        # if os.access(filename + '.h5', os.F_OK):  # ...retrieve the Waveforms from file.
        if os.access(filename, os.F_OK):  # ...retrieve the Waveforms from file.

            print('file exists')
            AB = utilities.from_file(filename, 'AB')

        else:
            ## Define Waveform parameters ##
            print('computing new file')
            phase_diff = np.arange(ntraps - 1) / (ntraps - 2) * 2 * np.pi
            phasesB = np.cumsum(phase_diff)

            # f_list[ind] += 0.04E6
            freq_A = []
            phasesA = []
            ####################for L to R:########################

            startfreq = 84.8E6 - spacing  # need to -spacing for L waveforms, don't for R waveforms
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

            # phasesA = phasesB
            freq_B = f_list[1:]
            print("L to R sweep generation end.")
            # ############## for R to L:#########################
            #
            # startfreq = 88E6 # need to -spacing for L waveforms, don't for R waveforms
            # f_list = [startfreq + j * spacing for j in range(ntraps)]
            #
            # for i in range(ntraps):
            #     if i < ntraps - 2 - sweep_num:
            #         freq_A.append(f_list[i])
            #     if i >= ntraps - 1 - sweep_num:
            #         freq_A.append(f_list[i])
            #
            # freq_B = f_list[:-1] # for R sweeps
            # print("R to L sweep generation end.")
            ####################################################
            # for i in range(len(phasesB)):
            #     if i < len(phasesB) - sweep_num - 1:
            #         phasesA.append(phasesB[i])
            #     elif i >= len(phasesB) - sweep_num:
            #         phasesA.append(phasesB[i])
            # # phasesA.append(phasesB[len(phasesB) - sweep_num - 1])
            # phasesA.append(phasesB[-1])
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
            AB = Sweep_sequence(A, B, sweep_time=0.16, ramp='cosine', segment = False)
            # AB = Sweep_loop(A, B, hold_time_1=0.5, hold_time_2= 0.5, sweep_time=1.0, ramp='cosine')

            # AB = Sweep_sequence(A, B, sweep_time=1.0)

            # times = [time()]
            # A.compute_waveform(filename, 'A')
            # max_list.append(A.compute_waveform())

            # times.append(time())

            # times.append(time())
            # B.compute_waveform(filename, 'B')
            # max_list.append(B.compute_waveform())
            # times.append(time())

            # times.append(time())
            AB.compute_waveform(filename, 'AB')
            # B.compute_waveform(filename, 'B')

            # max_list.append(AB.compute_waveform())
            # times.append(time())

            # ## Performance Metrics ##
            # # print("DATA_MAX: ", DATA_MAX)
            # print(32E4 / (times[1] - times[0]), " bytes/second")
            # print((times[2] - times[1])*1000, " ms")
            # print(32E5 / (times[3] - times[2]), " bytes/second")
            # print((times[4] - times[3])*1000, " ms")
            # print(32E6 / (times[5] - times[4]), " bytes/second")
            # print("Total time: ", times[-1] - times[0], " seconds")
    # print(max_list)
    # print(f'optimal norm is {np.min(wavgen.constants.SAMP_VAL_MAX/np.array(max_list))}')

    ## Plotting of our Waveforms for Validation ##
    # print(AB.SampleLength)
    # AB.plot()
    # A.plot()
    # B.plot()
    # import matplotlib.pyplot as plt
    # plt.show()
    # #
    # print('now open the card')
    # dwCard = wavgen.Card()
    # dwCard.setup_channels(300)
    # # dwCard.load_waveforms(A)
    # # dwCard.wiggle_output(duration=10000.0)
    # dwCard.load_waveforms(AB, mode='replay')
    # dwCard.wiggle_output()
    # dwCard.load_waveforms(B)
    # dwCard.wiggle_output()
    # print('done!')

