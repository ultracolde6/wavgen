from wavgen.waveform import Superposition, even_spacing, Sweep
from time import time
import wavgen.constants
from wavgen import utilities
import os


rp = [1.934454997984215 , 2.8421067958595616 , 2.677047569335915 , 1.1721824508892977 , 6.158065366794917 ,
    3.2691669970332335 , 2.636275384021578 , 1.6254638780707589 , 4.919003540925028 , 1.6084971058993613 ,
    5.2499387038268575 , 2.3688357219496265 , 4.713893357925578 , 5.223088585470364 , 0.3257672775855246 ,
    2.9571038289407126 , 2.4258010454280505 , 4.084691833872798 , 6.1867748426923335 , 5.200604534623386 ,
    3.3056812953203925 , 4.189137888598024 , 1.7650458297661427 , 4.080234513102615 , 0.6054340441874929 ,
    1.6794564559420377 , 2.385531129338364 , 5.400612735688388 , 4.978163766484847 , 5.335873096123345 ,
    0.9273414057111622 , 2.4193737371833834 , 2.8777346889035185 , 6.214778264445415 , 3.758998982400149 ,
    3.7838618270241438 , 0.60809445869596 , 0.1507635470741596 , 4.371624180280478 , 4.539661740808455 ,
    0.3847626491973457 , 6.145153550108536 , 1.008385520345513 , 5.852133555294753 , 0.016620198470431467 ,
    2.0158660597106937 , 1.7261705033296812 , 5.223710321703292 , 2.2220833343473436 , 2.9180968688523863 ,
    2.122206092376529 , 5.402785161537129 , 5.478771156577643 , 2.291512850266888 , 1.5715835663916051 ,
    2.255249593007268 , 1.571931477334538 , 1.3993650740616836 , 0.6011622182733365 , 3.1927489491586014 ,
    4.381746015200942 , 1.974081456041723 , 1.393542167751563 , 5.521906837731298 , 5.612290110455913 ,
    2.31118503089683 , 4.829965025115874 , 0.3421538142269762 , 4.555158230853398 , 1.6134448025783288 ,
    6.157248240200644 , 5.027656526405459 , 0.295901526406544 , 5.502983369799478 , 4.472320872860696 ,
    1.7618458333352276 , 4.41379605495804 , 4.6652622669145725 , 3.379174996566024 , 2.9970834472120313 ,
    4.886226685869682 , 4.340847582571988 , 0.3684494418446467 , 3.3447731714626525 , 0.3569784383241427 ,
    0.2362652137260263 , 4.420022732699935 , 6.263528358483921 , 6.2277672316776505 , 6.0305138883226554 ,
    2.5228306972997183 , 0.29710864827838496 , 0.5164352609138518 , 3.079335706611155 , 0.7796787693888715 ,
    2.9068441712875255 , 3.3802818513629718 , 0.16738916961106443 , 1.7466706296839072 , 0.7532941316251239]
""" 100 Pre-calculated Random Phases in range [0, 2pi] """
if __name__ == '__main__':
    filename = 'waveform_sweep'
    # If we have already computed the Waveforms...
    if os.access(filename + '.h5', os.F_OK):  # ...retrieve the Waveforms from file.
        A = utilities.from_file(filename, 'A')
        B = utilities.from_file(filename, 'B')
        AB = utilities.from_file(filename, 'AB')
    else:
        ## Define Waveform parameters ##

        freq_A = [90E6 + j*2.5E6 for j in range(2)]
        phasesA = rp[:len(freq_A)]
        phasesB = rp[1:len(freq_A)+1]

        sweep_size = wavgen.constants.MEM_SIZE // 8

        ## First Superposition defined with a list of frequencies ##
        A = Superposition(freq_A, phases=phasesA) #, resolution=int(1E6))

        ## Another Superposition made with Wrapper Function ##
        B = even_spacing(2, int(100E6), int(5E6), phases=phasesB)

        # ## A Sweep between the 2 previously defined stationary waves ##
        AB = Sweep(A, B, sweep_time=100.0)

        # times = [time()]
        A.compute_waveform(filename, 'B')
        # A.compute_waveform()

        # times.append(time())

        # times.append(time())
        B.compute_waveform(filename, 'A')
        # B.compute_waveform()
        # times.append(time())

        # times.append(time())
        AB.compute_waveform(filename, 'AB')
        # times.append(time())

        # ## Performance Metrics ##
        # # print("DATA_MAX: ", DATA_MAX)
        # print(32E4 / (times[1] - times[0]), " bytes/second")
        # print((times[2] - times[1])*1000, " ms")
        # print(32E5 / (times[3] - times[2]), " bytes/second")
        # print((times[4] - times[3])*1000, " ms")
        # print(32E6 / (times[5] - times[4]), " bytes/second")
        # print("Total time: ", times[-1] - times[0], " seconds")


    print('now open the card')
    dwCard = wavgen.Card()
    dwCard.setup_channels(300)
    dwCard.load_waveforms(A)
    dwCard.wiggle_output(duration=10000.5)
    dwCard.load_waveforms(AB)
    dwCard.wiggle_output(100.0)
    dwCard.load_waveforms(B)
    dwCard.wiggle_output(duration=3000.5)

    # Plotting of our Waveforms for Validation ##
    AB.plot()
    A.plot()
    B.plot()
    import matplotlib.pyplot as plt
    plt.show()