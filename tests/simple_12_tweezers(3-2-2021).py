import wavgen
import numpy as np

r = [2.094510589860613, 5.172224588379723, 2.713365750754814, 2.7268654021553975, 1.   /
     9455621726067513, 2.132845902763719, 5.775685169342227, 4.178303582622483, 1.971  /
     4912917733933, 1.218844007759545, 4.207174369712666, 2.6609861484752124, 3.41140  /
     54221128125, 1.0904071328591276, 1.0874359520279866, 1.538248528697041, 0.501676  /
     9726252504, 2.058427862897829, 6.234202186024447, 5.665480185178818]

if __name__=='__main__':
    ntraps = 21
    ntraps = 5
    # ntraps = 1
    startfreq = 90E6
    freq_A = [startfreq + j * 4E6 for j in range(ntraps)]
    # freq_A = [startfreq + j * 8E6 for j in range(ntraps)]
    # freq_A = [93E6,95E6,97E6]
    # mag_A = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    # mag_A = [1,1,1,1,1,1,1,1,1,1,1]
    mag_A = [1,1,1,1,1]
    freq_B = [startfreq + j * 2E6 for j in range(ntraps)]
    mag_B = [1,1,1,1,1,1,1,1,1,1,1]


    # freq_A = [111e6, 112e6, 113e6, 114e6]
    #freq_A = [int(110e6)]
    A = wavgen.waveform.Superposition(freq_A, mags = mag_A)  # One via the default constructor...
    A.set_phases(r[:len(freq_A)])
    # B = wavgen.waveform.Superposition(freq_B, mags=mag_B)  # One via the default constructor...
    # B.set_phases(r[:len(freq_B)])
    # filename = 'card_single'  # Location for our HDF5 file
    # A.compute_waveform(filename, 'A')


    print(freq_A)
    print(freq_B)
    # sweep=np.array(wavgen.waveform.Sweep(A, B, sweep_time=.032))
    # print(sweep[0])
    dwCard = wavgen.Card()
    dwCard.load_waveforms(A)
    # dwCard.load_sequence([A,B], 1)
    #
    dwCard.setup_channels(amplitude = 350      , use_filter=False)
    #
    #
    dwCard.wiggle_output()
    # # dwCard.load_waveforms(B)

