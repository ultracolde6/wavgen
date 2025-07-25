import wavgen
from wavgen import utilities
from wavgen.utilities import *
from wavgen.spectrum import *
from wavgen.constants import *
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# r = [2.094510589860613, 5.172224588379723, 2.713365750754814, 2.7268654021553975, 1.   /
#      9455621726067513, 2.132845902763719, 5.775685169342227, 4.178303582622483, 1.971  /
#      4912917733933, 1.218844007759545, 4.207174369712666, 2.6609861484752124, 3.41140  /
#      54221128125, 1.0904071328591276, 1.0874359520279866, 1.538248528697041, 0.501676  /
#      9726252504, 2.058427862897829, 6.234202186024447, 5.665480185178818]


if __name__=='__main__':
    folder_name = 'temp_waveforms_80_40Twz_5lambda_susc-meas'
    # create a new folder for waveforms to be saved to, if it doesn't already exist
    new_path = Path(folder_name)
    isdir = os.path.isdir(new_path)
    if not isdir:
        os.mkdir(new_path)
        print(f'directory created')

    ntraps = 2  # this is the num of tweezers we want
    Lambda = 0.16E6
    CenterFreq = 104E6
    spacing_Lambda = 5
    stagger_Lambda = 0*1/32
    shift_Lambda = 0

    for stagger_Lambda in np.arange(-1/8,1/8+0.000001,1/32):

        spacing = spacing_Lambda * Lambda #0.8E6
        shift = shift_Lambda * Lambda #0.8E6
        stagger = stagger_Lambda * Lambda #0.8E6

        startfreq = CenterFreq - 20*spacing + shift # 86.4E6 + 0.04E6 #88.04E6
        filename = Path(folder_name, f'(sp={spacing_Lambda:.5f}L'
                                     f'_sh={shift_Lambda:.5f}L'
                                     f'_st={stagger_Lambda:.5f}L).h5')

        if os.access(filename, os.F_OK):  # ...retrieve the Waveforms from file.
            print('Read file!')
            A = utilities.from_file(filename, 'A')
        else:
            freq_A = [startfreq + j*spacing + stagger*(-1)**(j+1) for j in range(ntraps)]
            print(freq_A)
            magsA = np.ones(ntraps)
            phase_diff = np.arange(ntraps) / (ntraps - 1) * 2 * np.pi
            phasesA = np.cumsum(phase_diff)
            A = wavgen.waveform.Superposition(freq_A, phases=phasesA, mags=magsA)  # One via the default constructor...
            A.compute_waveform(filename, 'A')
    # A.plot()
    # plt.show()
    # dwCard = wavgen.Card()
    # dwCard.setup_channels(amplitude = 120, use_filter=False)
    # # dwCard.stabilize_intensity(A,which_cam=0)
    #
    # dwCard.load_waveforms(A)
    # dwCard.wiggle_output(duration=0)