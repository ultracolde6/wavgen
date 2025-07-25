import wavgen.constants
from wavgen import utilities
import os

if __name__ == '__main__':
    filename = 'sweep_loop_92-102_100-2ms_x1-100_quad'
    # filename = 'sweep_92-102_100-1-100_cubic'
    # If we have already computed the Waveforms...
    if os.access(filename + '.h5', os.F_OK):  # ...retrieve the Waveforms from file.
        AB = utilities.from_file(filename, 'AB')
        A = utilities.from_file(filename, 'A')
        B = utilities.from_file(filename, 'B')

        # AB.plot()
        # import matplotlib.pyplot as plt
        # plt.show()
        print('now open the card')
        dwCard = wavgen.Card()
        dwCard.setup_channels(amplitude = 350, use_filter=False)
        dwCard.load_waveforms(AB, mode='replay')
        dwCard.wiggle_output(duration=0)
        print('done!')