import wavgen
from wavgen import utilities
from wavgen.utilities import *
from wavgen.spectrum import *
from wavgen.constants import *
import numpy as np
import matplotlib.pyplot as plt

# r = [2.094510589860613, 5.172224588379723, 2.713365750754814, 2.7268654021553975, 1.9455621726067513,
#      2.132845902763719, 5.775685169342227, 4.178303582622483, 1.9714912917733933, 1.218844007759545,
#      4.207174369712666, 2.6609861484752124, 3.4114054221128125, 1.0904071328591276, 1.0874359520279866,
#      1.538248528697041, 0.5016769726252504, 2.058427862897829, 6.234202186024447, 5.665480185178818]

# r = [2.094510589860613+0.13123, 5.172224588379723, 2.713365750754814, 2.7268654021553975, 1.9455621726067513,
#      2.132845902763719, 2.6609861484752124-1.1234435, 4.178303582622483, 1.9714912917733933, 1.218844007759545,
#      4.207174369712666, 5.775685169342227, 3.4114054221128125, 1.0904071328591276, 1.0874359520279866,
#      1.538248528697041, 0.5016769726252504, 2.058427862897829, 6.234202186024447, 5.665480185178818]



if __name__=='__main__':
    # rp_local = np.random.rand(20)*2*np.pi

    # good random phases for 9 tweezers:
    # rp_local = np.array([4.00627675, 0.60909873, 0.55476328, 0.7467712,  2.6828748,  5.23432021, 1.43827396, 1.41563259, 0.45170676])
    # good random phases for 12 tweezers:
    # rp_local = np.array([3.49527485, 2.14652334, 3.78792428, 1.72387983, 0.15172922, 3.04570919,
    #                      5.5748488,  5.48343138, 4.55164846, 0.98316509, 5.60186994, 6.09350862])
    # good random phases for 14 tweezers:
    # rp_local = np.concatenate([np.array([3.49527485, 2.14652334, 3.78792428, 1.72387983, 0.15172922, 3.04570919,
    #                      5.5748488, 5.48343138, 4.55164846, 0.98316509, 5.60186994, 6.09350862, 2.5848552,  3.83450406]),
    #                            np.random.rand(2)*2*np.pi])

    # good random phases for 16 tweezers
    # rp_local = np.array([3.67339265, 2.4002002,  4.12547201, 1.45319259, 0.47256693, 2.83582555,6.03931703, 5.0194085,
    #                       5.3237773,  1.27536582, 5.91854789, 0.5338513, 2.52641684, 3.83084642, 1.5365708,  0.7507924 ])
    # rp_local = np.array([3.67339265, 2.4002002,  4.12547201, 1.45319259, 0.47256693, 2.83582555,6.03931703, 5.0194085,
    #                       5.3237773,  1.27536582, 5.91854789, 0.5338513, 2.52641684, 3.83084642, 1.5365708,  0.7507924, 5.501468942 ])
    # rp_local = np.hstack((rp_local, rp_local+1.32))
    # rp_local = np.concatenate([np.array([3.67339265, 2.4002002, 4.12547201, 1.45319259, 0.47256693, 2.83582555, 6.03931703, 5.0194085,
    #                      5.3237773, 1.27536582, 5.91854789, 0.5338513, 2.52641684, 3.83084642, 1.5365708, 0.7507924]),
    #                            (np.random.rand(2)-0.0)*2*np.pi])

    # good random phases for 18 tweezers
    # rp_local = np.array([ 3.21934938,  3.29967958,  4.89668318,  1.31849451,  0.39715318,
    #     3.38747516,  6.0630842 ,  4.6774261 ,  5.70960476,  1.90851341,
    #     5.47353832,  1.4248118 ,  3.44331092,  3.46030831,  1.41408589,
    #    -0.12564098,  5.02968942,  5.28050938])

    # good random phases for 20 tweezers
    # rp_local = np.array([3.21934938, 3.29967958, 4.89668318, 1.31849451, 0.39715318,
    #        3.38747516, 6.0630842, 4.6774261, 5.70960476, 1.90851341,
    #        5.47353832, 1.4248118, 3.44331092, 3.46030831, 1.41408589,
    #        -0.12564098, 5.02968942, 5.28050938, 1.32268456, 0.79252788]) + (np.random.rand(20)-0.5)*0.25*np.pi


    #  random phases for 100 tweezers
    # rp_local = np.tile(np.array([3.21934938, 3.29967958, 4.89668318, 1.31849451, 0.39715318,
    #        3.38747516, 6.0630842, 4.6774261, 5.70960476, 1.90851341,
    #        5.47353832, 1.4248118, 3.44331092, 3.46030831, 1.41408589,
    #        -0.12564098, 5.02968942, 5.28050938, 1.32268456, 0.79252788]),5) + (np.random.rand(100)-0.5)*0.25*np.pi
    # fixed zero phases for 100 twzs
    # rp_local = np.zeros(100)


    # np.random.seed(3)
    # rp_local = np.random.random(30)*2*np.pi

    # # test 1
    # nmax=50
    # phase_diff = np.arange(nmax)/(nmax-1) * 2*np.pi
    # rp_local = np.cumsum(phase_diff)


    # rp_local = np.array([ 3.33693737,  3.01887244,  5.05166402,  0.56100865, -0.03723229,
    #     4.06481713,  6.04528897,  3.84503722,  5.344957  ,  2.00331624,
    #     5.3906892 ,  1.93557071,  4.25199956,  3.85269421,  1.35456466,
    #     0.70893823,  6.32981103,  5.8684677 ,  1.31245983,  0.76849116])

    # good random phases for 21 tweezers
    # rp_local = np.array([3.33693737, 3.01887244, 5.05166402, 0.56100865, -0.03723229,
    #                      4.06481713, 6.04528897, 3.84503722, 5.344957, 2.00331624,
    #                      5.3906892, 1.93557071, 4.25199956, 3.85269421, 1.35456466,
    #                      0.70893823, 6.32981103, 5.8684677, 1.31245983, 0.76849116,4.75602244])
    # rp_local = np.array([3.32983055, 3.05416525, 5.07573984, 1.39829744, 0.05796052,
    #    4.29349013, 6.01175922, 4.13660929, 6.37415617, 1.29724253,
    #    5.74395328, 2.12948259, 3.85008974, 4.37986072, 2.14500993,
    #    0.70400991, 5.68516281, 5.93011376, 1.37374986, 0.47448655,
    #    4.75602244])
    # np.random.shuffle(rp_local)

    # print('Generate random phase:')
    # print(rp_local)

    ntraps = 1
##########################################################
    # phase_diff = np.arange(ntraps)/(ntraps-1) * 2*np.pi
    # phasesA = np.cumsum(phase_diff)
###########################################################

    # phasesA = np.array([-np.pi/2,0,-np.pi/2])

    startfreq = 88E6

    # startfreq = 99.9E6 #80.248E6 + 0.798E6*10 # 99E6
    # centerfreq= 100E6
    spacing = 0.8E6
    end_freq = 88E6 + spacing * 40
    freq_list_all=[startfreq + 0.8E6*j for j in range(40)]
    # spacing = 1E6
    # startfreq = 80E6
    # freq_A = [centerfreq-spacing, centerfreq+spacing]
    # freq_A = [92.2E6, 108.8E6]
    # freq_A = [startfreq + spacing*j for j in range(ntraps)]
    # freq_A = [end_freq - spacing * (ntraps - j) for j in range(ntraps)]
    # 4 right most tweezers
    # freq_B = [end_freq - spacing * (ntraps - j) for j in range(ntraps)]
    # freq_A = [startfreq - 8*0.798E6*j for j in range(ntraps)]
    # freq_A = [101.786E6, 108.178E6]
    # startfreq = 105.688E6 # 99E6
    # freq_A = [startfreq + j * 1E6 for j in range(ntraps)]
    # # # startfreq = 92.831E6
    # # startfreq = 95.982E6
    # # startfreq = 100.3E6
    # startfreq = 100E6
    freq_A = [freq_list_all[18]]
    # freq_A = [100E6]
    # freq_A = [100E6,110E6,115E6]
    # freq_A = [startfreq + j * 0.7E6 for j in range(ntraps)]
    # freq_A = [88,93,98]
    # freq_A = [startfreq + j * 1.119E6 for j in range(ntraps)]
    # freq_A = [startfreq + j * 1E6 for j in range(ntraps)]
    # freq_A = [108.458E6, 109.333E6]
    # freq_A = [92.806E6, 98.366E6]
    # freq_A = [94E6, 94.769E6]
    # freq_A = [92E6,96E6,100E6]
    # freq_A = [102.528E6]
    # freq_A = [100E6,105.747E6]
    # freq_A = [105.6E6]
    # print(freq_A)
    # freq_A = [80E6, 90E6, 100E6, 110E6, 120E6]
    # freq_A = [90E6, 92.5E6, 95E6, 97.5E6, 100E6, 102.5E6, 105E6, 107.5E6, 110E6]

    # freq_A = [101.89E6]
    # freq_A = [99.992E6] #10lamdba
    # freq_A = [97.795E6, 98.425E6, 99.055E6, 99.685E6, 100.315E6, 100.945E6, 101.575E6, 102.205E6]
    # freq_A = [99.992E6, 100.608E6] # 4*lambda
    # mag_A = [1]
    # freq_A = [98.760E6,99.376E6, 99.992E6, 100.608E6,101.224E6,101.840E6]  # 4*lambda
    # mag_A = [1]
    # freq_A = [102E6]
    # max_calibration
    # mag_A = [0.978,1,0.900,0.952,0.977]
    # amp_calibration
#     mag_A = [0.959,1,0.912,0.958,0.981]
#     mag_A = [0.958,1,0.920,0.979,0.997]
#     mag_A = [0.955,1,0.923,0.983,1]
#     mag_A = [0.954,0.999,0.923,0.983,1]
#     mag_A = [0.953,0.999,0.923,0.983,1]
# # RUN5
#     mag_A = [0.952,0.996,0.923,0.983,1]
# # RUN6
#     mag_A = [0.952,0.998,0.923,0.983,1]
# # RUN7
#     mag_A = [0.950,0.996,0.923,0.982,1]
# # RUN8
#     mag_A = [0.9495,0.997,0.9225,0.983,1]                                                                                                                                                                                                                                                                                                                                                                                                              [1,1,1,1]

    # freq_A = [111e6, 112e6, 113e6, 114e6]
    # freq_A = [99.693E6, 100.307E6]
    # freq_A = [98.792E6, 101.812E6]
    # mag_A = [0.95, 1, 1]
    # mag_A = [0.67, 0.75, 1, 0.9, 0.8, 0.9, 1]
    # mag_A = [1,0.95]
    # mag_A = np.ones(ntraps)
    # mag_A = [0.55, 0.8, 1, 1, 1]
    # phasesA = utilities.rp[:len(freq_A)]
    # print('used random phase here:')
    # print(repr(phasesA))
    ntraps=len(freq_A)
    phase_diff = np.arange(ntraps) / (ntraps - 1) * 2 * np.pi
    all_40_diff = np.arange(40) / (40 - 1)*2*np.pi
    all_phases = np.cumsum(all_40_diff)
    phasesB = all_phases[:6]
    phasesA = np.cumsum(phase_diff)
    phasesA=[0]
    print('Twz frequencies:')
    print(np.array(freq_A)/1E6)
    mag_A = np.ones(ntraps)
    # mag_A = np.array([0.25,1,0.25])
    # mag_A = np.array([1, 0.92])
    # phasesA = [1.094510589860613, 5.172224588379723]
    # A = wavgen.waveform.Superposition(freq_A, phases=phasesA)
    # ntraps2 = len(freq_B)
    # phase_diff_B = np.arange(ntraps2) / (ntraps2 - 1) * 2 * np.pi
    # phasesB = np.cumsum(phase_diff_B)
    # print('Right Twz frequencies:')
    # print(np.array(freq_B)/1E6)
    # mag_B = np.ones(ntraps2)

    # A = wavgen.waveform.Superposition(freq_A + freq_B,
    #                                   phases=np.concatenate((phasesA, phasesB)),
    #                                     mags=np.concatenate((mag_A, mag_B)))  # One via the default constructor...

    A = wavgen.waveform.Superposition(freq_A, phases=phasesA, mags=mag_A)  # One via the default constructor...
    # A = wavgen.waveform.Superposition(freq_A)  # One via the default constructor...

    # A.stabilize_intensity()
    # self, wav, cam = None, which_cam = None

    # A.plot()
    # plt.show()
    dwCard = wavgen.Card()
    dwCard.setup_channels(amplitude = 150, use_filter=False)

    # dwCard.stabilize_intensity(A,which_cam=0)

    dwCard.load_waveforms(A)
    dwCard.wiggle_output(duration=0)