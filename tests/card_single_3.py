from wavgen import *
import os
import numpy as np

if __name__ == '__main__':

    filename = 'card_single_6'  # Location for our HDF5 file
    sweep_length = 5
    sweep = []

    # If we have already computed the Waveforms...
    if os.access(filename + '.h5', os.F_OK):  # ...retrieve the Waveforms from file.
        for i in range(sweep_length+1):
            sweep.append(utilities.from_file(filename, 'sweep'+str([i])))
    else:
        ## Define Waveform parameters ##
        ntraps = 2
        freq_A = np.array([100E6 + j * 10E6 for j in range(ntraps)])
        freq_B = np.array([110E6 + j * 5E6 for j in range(ntraps)])
        phases = utilities.rp[:ntraps]

        ## Construct list of sweeps ##
        sweep_list=[]
        delta_f = (np.array(freq_B) - np.array(freq_A))/sweep_length
        freq_array = np.zeros(sweep_length+1)
        for i in range(sweep_length+1):
            f = np.ndarray.tolist(freq_A + delta_f*i)
            sweep_list.append(waveform.Superposition(f, phases=phases[:len(freq_A)]))

        ## Compute all the Sample Points ##
        for i in range(len(sweep_list)):
            sweep_list[i].compute_waveform(filename, 'sweep'+str([i]))

    ## Set up the Card ##
    dwCard = Card()
    dwCard.setup_channels(300)

    ## Consecutively play each Waveform ##
    for i in range(sweep_length+1):
        dwCard.load_waveforms(sweep[i])
        print('sweep'+str(i))
        dwCard.wiggle_output(duration=300.5)
    dwCard.load_waveforms(sweep[sweep_length])
    dwCard.wiggle_output()

    print("Done!")
