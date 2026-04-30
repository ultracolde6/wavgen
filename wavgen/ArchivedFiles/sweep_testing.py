from wavgen.waveform import Superposition, Sweep1, Sweep_sequence, Sweep_loop
from time import time
import wavgen.constants
from wavgen import utilities
import os
import numpy as np
from pathlib import Path


if __name__ == '__main__':
    folder_name = 'waveforms_320us_16Twz_4lambda_v1'
    # create a new folder for waveforms to be saved to, if it doesn't already exist
    new_path = Path(folder_name)
    isdir = os.path.isdir(new_path)
    if not isdir:
        os.mkdir(f'{folder_name}')
        print(f'directory created')

    filename = Path(folder_name, 'sweep_15.h5')
    sweep_num = 15
    # If we have already computed the Waveforms...
    # if os.access(filename + '.h5', os.F_OK):  # ...retrieve the Waveforms from file.
    if os.access(filename, os.F_OK):  # ...retrieve the Waveforms from file.

        print('file exists')
        AB = utilities.from_file(filename, 'AB')

    else:
        ## Define Waveform parameters ##
        print('computing new file')
        ntraps = 17 # this is the num of tweezers we want, plus 1
        keep_num = 8
        # center_freq = 100.3E6
        # center_freq = 101.26E6
        # spacing = 0.617E6
        spacing = 0.632E6
        # if keep_num % 2 == 0:
        #     startfreq = center_freq - round(spacing/2*10**(-6), 3)*10**6 - (keep_num/2 - 1 + ntraps - keep_num)*spacing
        # else:
        #     startfreq = center_freq - (int(keep_num/2) + ntraps - keep_num)*spacing
        startfreq = 96.208E6 - spacing # the first tweezer in the wanted array minus 1 tweezer spacing for the extra moving tweezer
        # startfreq = 92E6
        # f_list = [startfreq+j * 1E6 for j in range(ntraps)]
        f_list = [startfreq + j * spacing for j in range(ntraps)]
        print(f_list)
        # freq_A = [f_list[0], f_list[1], f_list[2], f_list[3], f_list[4], f_list[5]]
        freq_A = []
        for i in range(ntraps):
            if i <= sweep_num:
                freq_A.append(f_list[i])
            if i > sweep_num+1:
                freq_A.append(f_list[i])
        # freq_B = [f_list[1], f_list[2], f_list[3], f_list[4], f_list[5], f_list[6]]
        freq_B = f_list[1:]
        # freq_A = [98E6, 99E6]
        # freq_B = [99E6, 100E6]
        phasesB = utilities.rp[:len(freq_B)]
        # phasesA = [phasesB[0], phasesB[0], phasesB[1], phasesB[2], phasesB[3], phasesB[4]]
        phasesA = []
        for i in range(len(phasesB)):
            if i == 0:
                # phasesA.append(phasesB[0])
                phasesA.append(phasesB[sweep_num])
            elif 0 < i <= sweep_num:
                phasesA.append(phasesB[i-1])
            else:
                phasesA.append(phasesB[i])
        # magsA = [1, 1]
        # magsB = [1, 1]
        # phasesB = utilities.rp[1:len(freq_A)+1]
        print(freq_A)
        print(freq_B)

        ## Superpositions defined with lists of frequencies ##
        # max_list = []
        A = Superposition(freq_A, phases=phasesA) #, mags=magsA)

        B = Superposition(freq_B, phases=phasesB) #, mags=magsB)

        # ## A Sweep between the 2 previously defined stationary waves ##
        # AB = Sweep1(A, B, hold_time_a=0.5, hold_time_b= 0.5, sweep_time=0.2, ramp='cosine')
        AB = Sweep_sequence(A, B, sweep_time=0.32, ramp='cosine', segment = False)
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
    print(AB.SampleLength)
    AB.plot()
    # A.plot()
    # B.plot()
    import matplotlib.pyplot as plt
    plt.show()
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

