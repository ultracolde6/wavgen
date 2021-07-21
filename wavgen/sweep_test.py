from wavgen import *
from wavgen import waveform_JH

if __name__ == '__main__':
    startfreq = 97E6
    ntraps = 5
    freq_A = [startfreq + j * 1E6 for j in range(ntraps)]
    freq_B = [startfreq + j * 2E6 for j in range(ntraps)]
    A = waveform.Superposition(freq_A)
    A.set_phases(utilities.rp[:len(freq_A)])
    B = waveform.Superposition(freq_B)
    B.set_phases(utilities.rp[:len(freq_B)])
    AB = waveform.Sweep(A, B, sweep_time=100.1)
    AB.plot()

    # ## Set up the Card ##
    # dwCard = Card()
    # dwCard.setup_channels(300)
    # dwCard.load_waveforms(AB)
    # dwCard.wiggle_output()