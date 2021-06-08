import wavgen

r = [2.094510589860613, 5.172224588379723, 2.713365750754814, 2.7268654021553975, 1.   /
     9455621726067513, 2.132845902763719, 5.775685169342227, 4.178303582622483, 1.971  /
     4912917733933, 1.218844007759545, 4.207174369712666, 2.6609861484752124, 3.41140  /
     54221128125, 1.0904071328591276, 1.0874359520279866, 1.538248528697041, 0.501676  /
     9726252504, 2.058427862897829, 6.234202186024447, 5.665480185178818]

if __name__=='__main__':
    ntraps = 5
    startfreq = 110E6
    freq_A = [startfreq + j * 2E6 for j in range(ntraps)]
    # max_calibration
    # mag_A = [0.978,1,0.900,0.952,0.977]
    # amp_calibration
    mag_A = [0.959,1,0.912,0.958,0.981]
    mag_A = [0.958,1,0.920,0.979,0.997]
    mag_A = [0.955,1,0.923,0.983,1]
    mag_A = [0.954,0.999,0.923,0.983,1]
    mag_A = [0.953,0.999,0.923,0.983,1]
# RUN5
    mag_A = [0.952,0.996,0.923,0.983,1]
# RUN6
    mag_A = [0.952,0.998,0.923,0.983,1]
# RUN7
    mag_A = [0.950,0.996,0.923,0.982,1]
# RUN8
    mag_A = [0.9495,0.997,0.9225,0.983,1]
    mag_A = [1,1,1,1,1]

    # freq_A = [111e6, 112e6, 113e6, 114e6]
    #freq_A = [int(110e6)]
    A = wavgen.waveform.Superposition(freq_A, mags = mag_A)  # One via the default constructor...
    A.set_phases(r[:len(freq_A)])
    # A.stabilize_intensity()
    # self, wav, cam = None, which_cam = None
    # filename = 'card_single'  # Location for our HDF5 file
    # A.compute_waveform(filename, 'A')

    print(freq_A)
    dwCard = wavgen.Card()
    dwCard.setup_channels(amplitude = 350, use_filter=False)
    # dwCard.stabilize_intensity(A,which_cam=0)

    dwCard.load_waveforms(A)
    dwCard.wiggle_output()