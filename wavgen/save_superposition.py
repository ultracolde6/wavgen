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
    for drop_num in [5]:
        # bias=0
        # folder_name = 'EightLambda'
        # folder_name = 'TwelveLambda-TwentyfiveTweezers'
        # folder_name = 'four lambda spacing - 70 tweezers'
        # folder_name = 'Centered_uneven_4lambda_spacing_2centered_4lambda'
        # folder_name = '3andhalf lambda spacing'
        folder_name = 'FourPtFiveLambda-25Tweezers'
        # folder_name = 'waveforms_80_40Twz_5lambda_susc-meas'
        # filename = Path(folder_name, 'static.h5')
        # filename = Path(folder_name, f'static_half-shifted_Lo2_dualbias_Lo{fraction}.h5')
        # filename = Path(folder_name, f'static_half-shifted_Lo2_dualbias_Lo{fraction}.h5')
        # filename = Path(folder_name,'60tweezers.h5')
        # filename = Path(folder_name,'drop5_twz18,19,20,21,22.h5')
        # filename = Path(folder_name,'40tweezers_102.72center_two_groups.h5')
        # filename = Path(folder_name,f'{drop_num}tweezers_102.72center_4L_antinode.h5')
        # filename = Path(folder_name,'70tweezers_101.44center_5L_gapped.h5')
        # filename = Path(folder_name,'26tweezers_101.44center_4L.h5')
        # filename = Path(folder_name,'40dropto24.h5')
        # filename = Path(folder_name,'70tweezers_nonlinear.h5')
        # filename = Path(folder_name, f'drop1_{drop_idx}.h5')
        # filename = Path(folder_name, f'40tweezers_101.44center_4L_antinode_rydberg.h5')
        # filename = Path(folder_name, f'40tweezers_101.44center_blockade_4L_wide_v2.h5')
        # filename = Path(folder_name, 'static_5,5lambda_shifted_Lo4_short.h5')
        # filename = Path(folder_name, 'drop2_twz12,13_short.h5')
        filename = Path(folder_name, 'static.h5')
        # filename = Path(folder_name, 'drop_2.h5')

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
            # ntraps = drop_num  # this is the num of tweezers we want
            ntraps = 25  # this is the num of tweezers we want
            # startfreq = 88E6
            # CenterFreq = 104.0E6
            CenterFreq = 101.44E6
            # CenterFreq = 102.72E6
            # CenterFreq = 102.72E6

            spacing_Lambda = 4.5
            shift_Lambda = 0# 0.25 #+ 1 / 16
            # stagger_Lambda = -1 / 128
            spacing = spacing_Lambda * Lambda  # 0.8E6
            shift = shift_Lambda * Lambda  # 0.8E6
            # stagger = stagger_Lambda * Lambda  # 0.8E6
            # startfreq = CenterFreq - 20 * spacing
            # startfreq = 87.04E6 #CenterFreq - (ntraps//2) * spacing
            # startfreq= CenterFreq - int(ntraps/2)*spacing #80E6
            # startfreq = CenterFreq - int( ntraps-1 )/2 * spacing
            startfreq = CenterFreq - ntraps * spacing / 2  # 86.4E6 + 0.04E6 #88.04E6

            com_shift = 0*Lambda/4
            center_bias = 0*Lambda/16

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
            # startfreq = CenterFreq - ntraps*spacing/2 # 86.4E6 + 0.04E6 #88.04E6

            # freq_A = [startfreq + j*spacing + stagger*(-1)**(j+1) for j in range(ntraps)]
            freq_A = [startfreq + com_shift + j * spacing for j in range(ntraps)]
            # freq_A = [101.44E6, 102.16E6]
            # freq_A = np.array([startfreq +shift +  j * spacing for j in range(ntraps)])
            # freq_A = np.array([99520000,10048000,101.44E6,102.4E6])
            ### FOR UNEVEN SPACING ### 4 and 16 lambda, 23 tweezers, ntraps=43
            # freq_temp = np.array([startfreq +shift +  j * spacing for j in range(ntraps)])
            # mask_freqs = np.ones(len(freq_temp))
            # mask_freqs[10:17] = 0
            # mask_freqs[18:21] = 0
            # mask_freqs[22:25] = 0
            # mask_freqs[26:33] = 0

            ### FOR UNEVEN SPACING ### 4 and 12 lambda, 25 tweezers, ntraps=65
            # freq_temp = np.array([startfreq +shift +  j * spacing for j in range(ntraps)]) # set ntraps=65 for the uneven spacing version
            # mask_freqs = np.ones(len(freq_temp))
            # mask_freqs[11:29] = 0
            # mask_freqs[30:32] = 0
            # mask_freqs[33:35] = 0
            # mask_freqs[36:54] = 0
            # #
            # mask_freqs_bool = mask_freqs > 0.1
            # freq_A = freq_temp[mask_freqs_bool]
            # ntraps = len(freq_A)  # num tweezers we want

            ### FOR UNEVEN SPACING ### 4 and 12 lambda, 24 tweezers, ntraps=65, 2 centered 12lambda
            # freq_temp = np.array([startfreq +shift +  j * spacing for j in range(ntraps)]) # set ntraps=65 for the uneven spacing version
            # mask_freqs = np.ones(len(freq_temp))
            # mask_freqs[11:32] = 0
            # mask_freqs[33:35] = 0
            # mask_freqs[36:54] = 0
            # #
            # mask_freqs_bool = mask_freqs > 0.1
            # freq_A = freq_temp[mask_freqs_bool]
            # ntraps = len(freq_A)  # num tweezers we want

            ### FOR UNEVEN SPACING ### 4 and 12 lambda, 24 tweezers, ntraps=65, 2 centered 4lambda
            # freq_temp = np.array([startfreq + shift + j * spacing for j in
            #                       range(ntraps)])  # set ntraps=65 for the uneven spacing version
            # mask_freqs = np.ones(len(freq_temp))
            # mask_freqs[12:32] = 0
            # mask_freqs[34:54] = 0
            # #
            # mask_freqs_bool = mask_freqs > 0.1
            # freq_A = freq_temp[mask_freqs_bool]
            # ntraps = len(freq_A)  # num tweezers we want


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
            magsA = np.ones(ntraps)
            # magsA[10:17]=0
            # magsA[18:21]=0
            # magsA[22:25]=0
            # magsA[26:33] = 0

            # magsA[16] = 1
            # magsA[::3] = 0
            # for i in range(30,40):
            #     magsA[i] = 0
            # magsA = np.zeros(ntraps)
            # magsA[14] = 1
            # magsA[15] = 1
            # magsA[2] = (0.89719+1+0.015)/2
            # magsA[3] = (0.86915+1)/2
            # magsA[4] = (0.96261+1+0.02)/2
            # for i in [42,50]:
            #     magsA[i] = 1
            # for i in range(19,20):
            #     magsA[i]=1
            # magsA[14] = 1
            # magsA[14] = 1
            # for ii in range(10, 30):
            #     if ii%2 ==0:
            #         magsA[ii] = 1
            # for ii in range(16, 24):
            #     magsA[ii] = 1

            phase_diff = np.arange(ntraps) / (ntraps - 1) * 2 * np.pi
            phasesA = np.cumsum(phase_diff)
            # rng=np.random.default_rng(seed=2)
            # phasesA = rng.random(ntraps)*2*np.pi
            # phasesA=[14.2996,19.7162,25.99939,33.1492,41.1657]
            # phase_diff_temp_5 = np.arange(5) / (5 - 1) * 2 * np.pi
            # phases_temp_5 = np.cumsum(phase_diff_temp_5)
            # phasesA= phases_temp_5

            ################## the following minimizes cost function 3 ##########################
            # phasesA = np.array([ -1.14254421e-01, -1.91730193e-01, 8.48065418e-02, 2.04235594e-01,
            #                      7.27589378e-01, 1.64693962e+00, 2.23424824e+00, 3.89016556e+00,
            #                      4.36346004e+00, 5.91085170e+00, 7.40510848e+00, 8.89809238e+00,
            #                      1.05167619e+01, 1.25341858e+01, 1.47477671e+01, 1.72211853e+01,
            #                      1.95716544e+01, 2.18883146e+01, 2.45402847e+01, 2.75826692e+01,
            #                      3.06437088e+01, 3.37234011e+01, 3.71935083e+01, 4.09989265e+01,
            #                      4.47705366e+01, 4.84191976e+01, 5.23276925e+01, 5.64323475e+01,
            #                      6.09357548e+01, 6.55648507e+01, 7.01926692e+01, 7.47673572e+01,
            #                      8.04161415e+01, 8.48823005e+01, 9.04170711e+01, 9.56197995e+01,
            #                      1.01218521e+02, 1.07221170e+02, 1.13066712e+02, 1.19266267e+02 ])
            #######################################################################################

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
