from wavgen.waveform import Superposition, Sweep1, Sweep_sequence, Sweep_loop
from time import time
import wavgen.constants
from wavgen import utilities
import os
import numpy as np
import ipyparallel as ipp


if __name__ == '__main__':

    rc=ipp.Cluster(n=8).start_and_connect_sync()
    rc.wait_for_engines(n=8)
    ntraps = 41
    def func_loop(sweep_num):
        from wavgen.waveform import Superposition, Sweep1, Sweep_sequence, Sweep_loop
        import wavgen.constants
        import numpy as np

        ntraps = 41  # this is the num of tweezers we want, plus 1
        max_list = []

        phase_diff = np.arange(ntraps - 1) / (ntraps - 2) * 2 * np.pi
        phasesB = np.cumsum(phase_diff)
        ## Define Waveform parameters ##
        # keep_num = 4
        # center_freq = 101.26E6
        # center_freq = 100E6
        # spacing = 0.639E6 #4*lambda new
        # spacing = 0.875E6 #5.5*lambda, new
        # spacing = 0.798E6 #5lambda new
        # spacing = 0.799E6 # 5lambda_v1
        spacing = 0.8E6
        # spacing = 0.75E6
        # spacing = 0.882E6 #5.5lambda_v3
        # if keep_num % 2 == 0:
        #     startfreq = center_freq - round(spacing/2*10**(-6), 3)*10**6 - (keep_num / 2 - 1 + ntraps - keep_num) * spacing
        # else:
        #     startfreq = center_freq - (int(keep_num / 2) + ntraps - keep_num) * spacing
        # startfreq = 92.941E6
        # startfreq = 96.208E6 - spacing
        startfreq = 88E6 - spacing  # need to -spacing for L waveforms, don't for R waveforms
        # startfreq = 80.248E6 - spacing
        # f_list = [startfreq+j * 1E6 for j in range(ntraps)]
        f_list = [startfreq + j * spacing for j in range(ntraps)]
        # print(f_list)
        freq_A=[]
        phasesA = []
       ############################# for L to R:
        for i in range(ntraps):
            if i <= sweep_num:
                freq_A.append(f_list[i])
            if i > sweep_num+1:
                freq_A.append(f_list[i])

        for i in range(len(phasesB)):
            if i == 0:
                phasesA.append(phasesB[sweep_num])
            elif 0 < i <= sweep_num:
                phasesA.append(phasesB[i-1])
            else:
                phasesA.append(phasesB[i])

        freq_B = f_list[1:]
######################################################### R to L below ###################
        # for i in range(ntraps):
        #     if i < ntraps - 2 - sweep_num:
        #         freq_A.append(f_list[i])
        #     if i >= ntraps - 1 - sweep_num:
        #         freq_A.append(f_list[i])
        #
        # for i in range(len(phasesB)):
        #     if i < len(phasesB) - sweep_num - 1:
        #         phasesA.append(phasesB[i])
        #     elif i >= len(phasesB) - sweep_num:
        #         phasesA.append(phasesB[i])
        # phasesA.append(phasesB[len(phasesB) - sweep_num - 1])
        #
        # freq_B = f_list[:-1]  # for R sweeps

        ## Superpositions defined with lists of frequencies ##
        A = Superposition(freq_A, phases=phasesA)  # , mags=magsA)

        B = Superposition(freq_B, phases=phasesB)  # , mags=magsB)

        # ## A Sweep between the 2 previously defined stationary waves ##
        AB = Sweep_sequence(A, B, sweep_time=0.16, ramp='cosine', segment = False)

        return(AB.compute_waveform())

    max_list = np.array(rc[:].map_sync(func_loop,np.arange(1, ntraps-1)))
    print(max_list)
    print(f'optimal norm is {np.min(wavgen.constants.SAMP_VAL_MAX / np.array(max_list))}')


