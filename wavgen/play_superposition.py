import sys
import os
from pathlib import Path

# Add the parent directory to Python path so wavgen can be imported
import os, sys 
sys.path.append('./')

import wavgen
from wavgen import utilities
from wavgen.utilities import *
from wavgen.spectrum import *
from wavgen.constants import *
import numpy as np
import matplotlib.pyplot as plt



if __name__=='__main__':
    # folder_name = 'EightLambda' ##thirty tweezers
    folder_name = 'four lambda spacing - 70 tweezers'
    # folder_name = '3andhalf lambda spacing'
    # folder_name = 'three lambda spacing'
    # folder_name = 'waveforms_80_40Twz_5lambda_susc-meas' ## 2025 0723
    # folder_name = 'jiggle_waveforms'
    # filename = Path(folder_name, 'jiggle_amp=400.0kHz_freq=64.0kHz.h5')
    # filename = Path(folder_name, 'drop_2_twz15,25_NPM_Power_Adjusted.h5')
    # filename = Path(folder_name, '9tweezer_25lambda_static.h5')
    # filename = Path(folder_name, 'static_5,5lambda_antinode.h5')
    # filename = Path(folder_name, 'drop_2_twz16,24.h5')
    # filename = Path(folder_name, 'drop_5_twz21,22,23,24,25_NPM.h5')

    # filename = Path(folder_name, 'drop_2_twz15,25_not_phase_match.h5') ## 2025 0723
    # filename = Path(folder_name, 'drop_1_twz15.h5')
    # filename = Path(folder_name, '4tweezers.h5')

    # filename = Path(folder_name, '46tweezers_101.44center_3.5L_antinode.h5')
    # filename = Path(folder_name, 'static.h5')
    filename = Path(folder_name, '40tweezers_101.44center_4L.h5')
    # filename = Path(folder_name, 'drop_1_twz22.h5')
    # filename = Path(folder_name, '70tweezers_nonlinear.h5')
    # filename = Path(folder_name, '40tweezers_101.44center_4L_PG3.h5')
    # filename = Path(folder_name, '50tweezers.h5')
    # filename = Path(folder_name, 'static_20_center.h5')
    # filename = Path(folder_name, 'static_4_side.h5')
    # filename = Path(folder_name, 'static_5lambda_twogroup_node_Delta=0l.h5')
    # filename = Path(folder_name, 'static_104_single.h5')
    if os.access(filename, os.F_OK):  # ...retrieve the Waveforms from file.
        print('Read file!')
        A = utilities.from_file_simple(filename, 'A')
    dwCard = wavgen.Card()

    # dwCard.setup_channels(amplitude = 480, use_filter=False)
    dwCard.setup_channels(amplitude = 85, use_filter=False)
    #
    dwCard.load_waveforms(A)
    print('outputting')
    dwCard.wiggle_output(duration=0)