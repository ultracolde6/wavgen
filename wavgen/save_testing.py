import wavgen
from wavgen import utilities
from wavgen.utilities import *
from wavgen.spectrum import *
from wavgen.constants import *
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


r = [2.094510589860613, 5.172224588379723, 2.713365750754814, 2.7268654021553975, 1.   /
     9455621726067513, 2.132845902763719, 5.775685169342227, 4.178303582622483, 1.971  /
     4912917733933, 1.218844007759545, 4.207174369712666, 2.6609861484752124, 3.41140  /
     54221128125, 1.0904071328591276, 1.0874359520279866, 1.538248528697041, 0.501676  /
     9726252504, 2.058427862897829, 6.234202186024447, 5.665480185178818]
if __name__=='__main__':
    folder_name = 'waveforms_160us_5lambda_v1'
    # create a new folder for waveforms to be saved to, if it doesn't already exist
    new_path = Path(folder_name)
    isdir = os.path.isdir(new_path)
    if not isdir:
        os.mkdir(f'{folder_name}')
        print(f'directory created')

    filename = Path(folder_name, 'static.h5')

    if os.access(filename, os.F_OK):  # ...retrieve the Waveforms from file.
        print('Read file!')
        A = utilities.from_file(filename, 'A')
    else:
        startfreq = 92E6
        ntraps = 8
        spacing = 1E6

        freq_A = [startfreq + j * spacing for j in range(ntraps)]

        phasesA = utilities.rp[:len(freq_A)]
        mag_A = np.ones(ntraps)

        A = wavgen.waveform.Superposition(freq_A, phases=phasesA, mags = mag_A)

        A.compute_waveform(filename, 'A')

    dwCard = wavgen.Card()
    dwCard.setup_channels(amplitude = 120, use_filter=False)

    dwCard.load_waveforms(A)
    dwCard.wiggle_output(duration=0)