from wavgen.waveform import Superposition, Sweep_sequence, Sweep_crop
from time import time
import wavgen.constants
from wavgen import utilities
import os
from wavgen import *
import easygui
import os
from wavgen.utilities import *
from wavgen.spectrum import *
from wavgen.constants import *
from wavgen.waveform import Superposition
import numpy as np
from time import time, sleep

if __name__ == '__main__':
    filename = 'sweep_(88_100)-(100_106)_200us_(0,90_1)-(1_1)_cos'
    # If we have already computed the Waveforms...
    if os.access(filename + '.h5', os.F_OK):  # ...retrieve the Waveforms from file.
        A = utilities.from_file(filename, 'A')
        AB = utilities.from_file(filename, 'AB')
        B = utilities.from_file(filename, 'B')


    else:
        ## use the sweep crop ##
        old_filename = 'sweep_(88_100)-(100_106)_0,5-0,2-0,5_(0,90_1)-(1_1)_cos.h5'
        hf = h5py.File(old_filename, 'r')
        wave = np.array(hf["AB"][:])
        config_a = from_file(old_filename, 'A')
        config_b = from_file(old_filename, 'B')
        A = Sweep_crop(wave, config_a, config_b, sweep_time =0.2, hold_time_a = 0.50, section = 'A')
        print('A done')
        AB = Sweep_crop(wave, config_a, config_b,  sweep_time =0.2, hold_time_a = 0.50, section = 'AB')
        print('AB done')
        B = Sweep_crop(wave, config_a, config_b,  sweep_time =0.2, hold_time_a = 0.50, section = 'B')
        print('B done')

        print('compute A')
        A.compute_waveform(filename, 'A')
        print('compute B')
        B.compute_waveform(filename, 'B')
        print('compute AB')
        AB.compute_waveform(filename, 'AB')

    ## Plotting of our Waveforms for Validation ##
    AB.plot()
    A.plot()
    B.plot()

    import matplotlib.pyplot as plt
    plt.show()
