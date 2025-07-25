from wavgen import *
import easygui
import os
from wavgen.constants import MEM_SIZE
from wavgen.waveform import Superposition, even_spacing


if __name__ == '__main__':

    filename = 'card_sequential'  # Location for our HDF5 file
    step_time = 100.0  # Milliseconds

    # If we have already computed the Waveforms...
    if os.access(filename + '.h5', os.F_OK):  # ...retrieve the Waveforms from file.
        A = utilities.from_file(filename, 'A')
        # AB = utilities.from_file(filename, 'AB')
        B = utilities.from_file(filename, 'B')
        # BA = utilities.from_file(filename, 'BA')
    else:
        ntraps= 7
        freq_A = [97E6 + j * 1E6 for j in range(ntraps)]
        phases = rp[:ntraps]

        ## Define 2 Superposition objects ##
        A = Superposition(freq_A, phases=phases)  # One via the default constructor...
        B = even_spacing(ntraps, int(100E6), int(2E6), phases=phases)  # ...the other with a useful constructor wrapper helper

        ## 2 Sweep objects. One in each direction between the 2 previously defined waves ##
        # AB = Sweep(A, B, sample_length=MEM_SIZE//8)
        # BA = Sweep(B, A, sample_length=MEM_SIZE//8)

        # BA.compute_waveform(filename, 'BA')
        B.compute_waveform(filename, 'B')
        A.compute_waveform(filename, 'A')
        # AB.compute_waveform(filename, 'AB')

    # segments = [A, AB, B, BA]
    segments = [A, B]
    segs = len(segments)
    loops = int(MEM_SIZE//8 / A.SampleLength)
    steps = [utilities.Step(i, i, (i+1)%2*(loops - 1) + 1, (i+1)%segs) for i in range(segs)]

    dwCard = Card()
    dwCard.load_sequence(segments, steps)
    print('here')
    dwCard.wiggle_output()
    easygui.msgbox('Looping!')
    dwCard.stop_card()
