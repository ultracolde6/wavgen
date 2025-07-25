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


if __name__ == '__main__':
    Lambda = 0.16E6
    CenterFreq = 104E6
    for fraction in [-3/80,-5/128]:
    # for fraction in [1/64]:
        # bias=Lambda/fraction

        # bias=0
        folder_name = 'waveforms_80_40Twz_5lambda_susc-meas'
        # filename = Path(folder_name, f'static_half-shifted_Lo2_dualbias_Lo{fraction}.h5')
        # filename = Path(folder_name, f'static_half-shifted_Lo2_dualbias_Lo{fraction}.h5')
        # filename = Path(folder_name, 'drop_9.h5')
        # filename = Path(folder_name, 'static_5,5lambda_antinode.h5')
        filename = Path(folder_name, f'static_5lambda_twogroup_node_Delta={fraction}l.h5')

        # create a new folder for waveforms to be saved to, if it doesn't already exist
        new_path = Path(folder_name)
        isdir = os.path.isdir(new_path)
        if not isdir:
            os.mkdir(f'{folder_name}')
            print(f'directory created')

        # filename = Path(folder_name, 'static_neg.h5')
        # filename = Path(folder_name, 'drop_8.h5')

        if os.access(filename, os.F_OK):  # ...retrieve the Waveforms from file.
            print('Read file!')
            A = utilities.from_file(filename, 'A')
        else:
            ntraps = 40  # this is the num of tweezers we want
            # ntraps = 1
            # startfreq = 88E6
            CenterFreq = 104E6

            spacing_Lambda = 5
            # shift_Lambda =  0*(2 + 1/2) #+ 1 / 16
            # shift = shift_Lambda * Lambda  # 0.8E6

            # stagger_Lambda = -1 / 128
            spacing = spacing_Lambda * Lambda  # 0.8E6
            # stagger = stagger_Lambda * Lambda  # 0.8E6
            startfreq = CenterFreq - 20 * spacing
            # startfreq = CenterFreq
            com_shift = 0*Lambda/4
            center_bias = 0*Lambda/16

            # two group generation
            sym_shift=fraction*Lambda
            left_shift=-1.25*Lambda-sym_shift
            right_shift=1.25*Lambda+sym_shift

            freq_init = np.array([startfreq + com_shift + j * spacing for j in range(ntraps)])
            freq_A = freq_init*1.0

            freq_A[:int(ntraps/2)]=freq_init[:int(ntraps/2)] +left_shift
            freq_A[int(ntraps/2):]=freq_init[int(ntraps/2):] +right_shift
            # ind = 14
            # spacing = (0.8-0.03/32)*1E6
            # spacing = 0.882E6
            # if keep_num % 2 == 0:
            #     startfreq = center_freq - round(spacing/2*10**(-6), 3)*10**6 - (keep_num / 2 - 1 + ntraps - keep_num) * spacing
            # else:
            #     startfreq = center_freq - (int(keep_num / 2) + ntraps - keep_num) * spacing
            # startfreq = 110*spacing -39950 # lambda/4 shifted
            # startfreq = 87.89E6
            # startfreq = 80.248E6
            # startfreq = CenterFreq - 20*spacing + shift # 86.4E6 + 0.04E6 #88.04E6

            # freq_A = [startfreq + j*spacing + stagger*(-1)**(j+1) for j in range(ntraps)]
            # freq_A = [startfreq + com_shift + j * spacing for j in range(ntraps)]
            # freq_A = []
            # for i in range(int(ntraps/2)):
            #     freq_A.append(startfreq + i*spacing - center_bias/2)
            # for j in range(int(ntraps/2), ntraps):
            #     freq_A.append(startfreq + j*spacing + shift + center_bias/2)
            # bias_ind = [20]
            # for i in bias_ind:
            #     freq_A[i] += bias
            print(freq_A, len(freq_A))
            # center_freq = freq_A[20]
            # print(center_freq)
            # twz_list = [center_freq]
            # for i in range(1, 20):
            #     twz_list.append(center_freq + 0.8E6 * i)
            # for i in range(1, 21):
            #     twz_list.append(center_freq - 0.8E6 * i)
            # freq_A = np.sort(twz_list)
            # freq_A[ind] += 0.04E6
            # print(freq_A)
            # f_list = [startfreq + j * spacing for j in range(ntraps)]
            # print(freq_A)

            # for the drop waveform
            # freq_A = []
            # shift = f_list[ntraps-keep_num]-f_list[0]
            # for i in range(ntraps):
            #     if i < ntraps-keep_num:
            #         freq_A.append(f_list[i]-shift)
            #     else:
            #         freq_A.append(f_list[i])

            # num_below = 2  # number to keep with freq below the "center" tweezer (not necessarily the center_freq)
            # num_above = 1  # number to keep with freq above the "center" tweezer (not necessarily the center_freq)
            # shift = f_list[ntraps - int(keep_num / 2) - num_below] - f_list[0]
            # shift_1 = f_list[-1] - f_list[ntraps - int(keep_num / 2) + num_above]
            # print(shift,shift_1)
            # for i in range(ntraps):
            #     if i < ntraps - int(keep_num / 2) - num_below:
            #         freq_A.append(f_list[i] - shift)
            #     elif ntraps - int(keep_num / 2) - num_below <= i <= ntraps - int(keep_num / 2) + num_above:
            #         freq_A.append(f_list[i])
            #     else:
            #         freq_A.append(f_list[i] + shift_1)
            # print('Drop waveform frequencies:')
            # print(freq_A)
            # magsA = np.zeros(ntraps)  # np.ones(ntraps)
            magsA = np.ones(ntraps)
            # for i in range(20, 30):
            #     magsA[i] = 1
            # for i in range(16,24):
            #     magsA[i]=1
            # magsA[30] = 1
            # magsA[10] = 1
            # for ii in range(10, 30):
            #     if ii%2 ==0:
            #         magsA[ii] = 1
            # for ii in range(16, 24):
            #     magsA[ii] = 1
            phase_diff = np.arange(ntraps) / (ntraps - 1) * 2 * np.pi
            phasesA = np.cumsum(phase_diff)
            # phase_diff_1 = np.arange(int(ntraps/2))/(int(ntraps/2)-1)*2*np.pi
            # phases1 = np.cumsum(phase_diff_1)
            # phasesA = np.concatenate([phases1, phases1+2*np.pi/(ntraps-2)])
            # phasesA = utilities.rp[:len(freq_A)]
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
