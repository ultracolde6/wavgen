from wavgen.waveform import Superposition, Sweep1, Sweep_sequence, Sweep_loop
from time import time
import wavgen.constants
from wavgen import utilities
import os
import numpy as np
from pathlib import Path
import ipyparallel as ipp

def gen_waveform_LtoR(folder_name, ntraps, sweep_num):
    from wavgen.waveform import Superposition, Sweep1, Sweep_sequence, Sweep_loop
    from time import time
    import wavgen.constants
    from wavgen import utilities
    import os
    import numpy as np
    from pathlib import Path
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

        freq_A = []
        phasesA = []
        ####################for L to R:########################

        spacing = 0.800E6
        startfreq = 88E6 - spacing  # need to -spacing for L waveforms, don't for R waveforms

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

        A = Superposition(freq_A, phases=phasesA) #, mags=magsA)

        B = Superposition(freq_B, phases=phasesB) #, mags=magsB)
        AB = Sweep_sequence(A, B, sweep_time=0.1, ramp='cosine', segment = False)

        AB.compute_waveform(filename, 'AB')
    return

def gen_waveform_RtoL(folder_name, ntraps, sweep_num):
    from wavgen.waveform import Superposition, Sweep1, Sweep_sequence, Sweep_loop
    from time import time
    import wavgen.constants
    from wavgen import utilities
    import os
    import numpy as np
    from pathlib import Path
    name_temp = 'sweep_{}R.h5'.format(sweep_num)
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

        spacing = 0.800E6
        startfreq = 88E6 # need to -spacing for L waveforms, don't for R waveforms
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

        A = Superposition(freq_A, phases=phasesA) #, mags=magsA)

        B = Superposition(freq_B, phases=phasesB) #, mags=magsB)
        AB = Sweep_sequence(A, B, sweep_time=0.1, ramp='cosine', segment = False)

        AB.compute_waveform(filename, 'AB')
    return


def para_print(folder_name,x):
    import os
    writepath = folder_name+f'/file_{x}.txt'
    mode = 'a' if os.path.exists(writepath) else 'w'
    with open(writepath, mode) as f:
        f.write(f'Hello, world!\n  {x}')
    return x

if __name__ == '__main__':

    rc = ipp.Cluster(n=42).start_and_connect_sync()
    rc.wait_for_engines(n=42)
    # view=rc.load_balanced_view()
    view=rc[:]

    ntraps = 41  # this is the num of tweezers we want, plus 1
    folder_name = "waveforms_160_40Twz_5lambda_vpara_cos100"

    # create a new folder for waveforms to be saved to, if it doesn't already exist

    new_path = Path(folder_name)
    isdir = os.path.isdir(new_path)

    if not isdir:
        os.mkdir(f'{folder_name}')
        print(f'directory created')

    done_results = []
    for sweep_num in np.arange(ntraps-2)+1:
        ar = view.apply_async(gen_waveform_RtoL, folder_name, ntraps, sweep_num)
        done_results.append(sweep_num)


    # for sweep_num in np.arange(1):
    #     ar = gen_waveform_RtoL(folder_name, ntraps, sweep_num)
    #     done_results.append(sweep_num)

    print(done_results)
