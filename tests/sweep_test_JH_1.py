from wavgen.waveform import Superposition, Sweep1
from time import time
import wavgen.constants
from wavgen import utilities
import os

if __name__ == '__main__':
    filename = 'sweep_92-94_100-3-100'
    # If we have already computed the Waveforms...
    if os.access(filename + '.h5', os.F_OK):  # ...retrieve the Waveforms from file.
        AB = utilities.from_file(filename, 'AB')
        A = utilities.from_file(filename, 'A')
        B = utilities.from_file(filename, 'B')


    else:
        ## Define Waveform parameters ##

        freq_A = [100E6 + j*2.5E6 for j in range(1)]
        freq_B = [102E6 + j*5E6 for j in range(1)]
        phasesA = utilities.rp[:len(freq_A)]
        phasesB = phasesA #utilities.rp[1:len(freq_A)+1]

        ## Superpositions defined with lists of frequencies ##
        A = Superposition(freq_A, phases=phasesA)

        B = Superposition(freq_B, phases=phasesB)

        # ## A Sweep between the 2 previously defined stationary waves ##
        AB = Sweep1(A, B, hold_time_a=50.0, hold_time_b= 50.0, sweep_time=3.0) # previously tried 100 ms sweep time but ran into fatal python error 85% through
        # AB = Sweep(A, B, sweep_time=100.0)

        # times = [time()]
        # A.compute_waveform(filename, 'A')
        # A.compute_waveform()

        # times.append(time())

        # times.append(time())
        # B.compute_waveform(filename, 'B')
        # B.compute_waveform()
        # times.append(time())

        # times.append(time())
        AB.compute_waveform(filename, 'AB')
        # AB.compute_waveform()
        # times.append(time())

        # ## Performance Metrics ##
        # # print("DATA_MAX: ", DATA_MAX)
        # print(32E4 / (times[1] - times[0]), " bytes/second")
        # print((times[2] - times[1])*1000, " ms")
        # print(32E5 / (times[3] - times[2]), " bytes/second")
        # print((times[4] - times[3])*1000, " ms")
        # print(32E6 / (times[5] - times[4]), " bytes/second")
        # print("Total time: ", times[-1] - times[0], " seconds")

    ## Plotting of our Waveforms for Validation ##
    AB.plot()
    # A.plot()
    # B.plot()
    import matplotlib.pyplot as plt
    plt.show()
    #
    # print('now open the card')
    # dwCard = wavgen.Card()
    # dwCard.setup_channels(300)
    # # dwCard.load_waveforms(A)
    # # dwCard.wiggle_output(duration=10000.0)
    # dwCard.load_waveforms(AB)
    # dwCard.wiggle_output()
    # # dwCard.load_waveforms(B)
    # # dwCard.wiggle_output(10000.0)
    print('done!')

