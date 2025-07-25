from wavgen.waveform import Superposition, Sweep_sequence, Sweep_crop
from time import time
import wavgen.constants
from wavgen import utilities
import os
from wavgen import *
import easygui
import os
from wavgen.utilities import *
from wavgen.spectrum import *
from wavgen.constants import *
from wavgen.waveform import Superposition
import numpy as np
from time import time, sleep
from pathlib import Path


if __name__ == '__main__':
    # filename = 'sweep_94-100_4ms'
    # filename = 'sweep_(92,2_100)-(100_106)_1ms'
    # filename = 'sweep_(94_100)-(100-106)_1ms_diff_depth'
    # filename = 'sweep_(94_100)-(100_106)_100us_diff_depth_cos'
    # filename = 'sweep_(94_100)-(100_106)_200us_(0,92_1)-(1_1)_cos'
    # filename = 'sweep_(98_100)-(100_106)_200us_(1_1)-(1_1)_cos'
    # filename = 'sweep_(96_100)-(100_106)_200us_(0,95_1)-(1_1)_cos'
    # filename = 'sweep_(88_100)-(100_106)_200us_(0,90_1)-(1_1)_cos'
    # filename = 'sweep_(92_100)-(100_106)_200us_(0,90_1)-(1_1)_cos'
    # filename = 'sweep_sequence_(100_106)-(94_100)_200us'
    # filename = 'sweep_sequence_(98_99)-(99_100)_160us'
    path_folder = 'waveforms_160us_5lambda'
    filename = 'sweep_3.h5'
    # filename = 'sweep_(90_100)-(100_106)_200us_(0,90_1)-(1_1)_cos'
    # If we have already computed the Waveforms...

    if os.access(Path(path_folder, filename), os.F_OK):  # ...retrieve the Waveforms from file.
        print('Read file!')
        A = utilities.from_file(Path(path_folder, filename), 'A')
        AB = utilities.from_file(Path(path_folder, filename), 'AB')
        B = utilities.from_file(Path(path_folder, filename), 'B')
    # if os.access(filename + '.h5', os.F_OK):  # ...retrieve the Waveforms from file.
    #     print('Read file!')
    #     A = utilities.from_file(filename, 'A')
    #     AB = utilities.from_file(filename, 'AB')
    #     B = utilities.from_file(filename, 'B')


    # else:
    #     ## use the sweep crop ##
    #     print('sweep crop!')
    #     old_filename = 'sweep_(94_100)-(100_106)_1-1-1_diff_depth.h5'
    #     hf = h5py.File(old_filename, 'r')
    #     wave = np.array(hf["AB"][:])
    #     config_a = from_file(old_filename, 'A')
    #     config_b = from_file(old_filename, 'B')
    #     A = Sweep_crop(wave, config_a, config_b, sweep_time =1.0, hold_time_a = 1.0, section = 'A')
    #     print('A done')
    #     AB = Sweep_crop(wave, config_a, config_b,  sweep_time =1.0, hold_time_a = 1.0, section = 'AB')
    #     print('AB done')
    #     B = Sweep_crop(wave, config_a, config_b,  sweep_time =1.0, hold_time_a = 1.0, section = 'B')
    #     print('B done')

        # ## Define Waveform parameters ##
        #
        # freq_A = [94E6, 100E6]
        # # freq_B = freq_A
        # freq_B = [100E6, 106E6]
        # phasesA = utilities.rp[:len(freq_A)]
        # phasesB = phasesA
        # # phasesA = [0]
        # # phasesB = [0]
        #
        # ## Superpositions defined with lists of frequencies ##
        # A = Superposition(freq_A, phases=phasesA)
        #
        # B = Superposition(freq_B, phases=phasesB)
        #
        # # ## A Sweep between the 2 previously defined stationary waves ##
        # AB = Sweep_sequence(A, B, sweep_time=1.0)

        # print('compute A')
        # A.compute_waveform(filename, 'A')
        # print('compute B')
        # B.compute_waveform(filename, 'B')
        # print('compute AB')
        # AB.compute_waveform(filename, 'AB')
    # include static waveform
    # C = utilities.from_file('static_(98_99_100_101_102)', 'A')
    ## Plotting of our Waveforms for Validation ##
    AB.plot()
    A.plot()
    B.plot()
    # C.plot()

    import matplotlib.pyplot as plt
    plt.show()
    ## Now open the card
    hCard = spcm_hOpen(create_string_buffer(b'/dev/spcm0'))
    ChanReady = False
    BufReady = False
    Sequence = False
    Wave = None
    offset = 0

    def _error_check(halt=True, print_err=True):
        """ Checks the Error Register.

        Parameters
        ----------
        halt : bool, optional
            Will halt program on discovery of error code.
        print_err : bool, optional
            Will print the error code.
        """
        ErrBuf = create_string_buffer(ERRORTEXTLEN)  # Buffer for returned Error messages
        if spcm_dwGetErrorInfo_i32(hCard, None, None, ErrBuf) != ERR_OK:
            if print_err:
                sys.stdout.write("Warning: {0}".format(ErrBuf.value))
            if halt:
                spcm_vClose(hCard)
                exit(1)
            return False
        return True


    ## Sets channels to default mode if no user setting ##
    def setup_channels(amplitude=DEF_AMP, ch0=True, ch1=False, use_filter=False):
        """ Performs a Standard Initialization for designated Channels & Trigger.

        Parameters
        ----------
        amplitude : float, optional
            Sets the Output Amplitude **RANGE**: [80 - 2000](mV) inclusive
        ch0 : bool, optional
            To Activate Channel0
        ch1 : bool, optional
            To Activate Channel1
        use_filter : bool, optional
            To Activate Output Filter

        Notes
        -----
        .. todo:: Complete ability to configure triggers.
        .. todo:: Add support for simultaneous use of both channels.
        """
        ## Input Validation ##
        if ch0 and ch1:
            print('Multi-Channel Support Not Yet Supported!')
            print('Defaulting to Ch1 only.')
            ch0 = False

        assert 80 <= amplitude <= (1000 if use_filter else 400), "Amplitude must within interval: [80 - 2000]"
        if amplitude != int(amplitude):
            amplitude = int(amplitude)
            print("Rounding amplitude to required integer value: ", amplitude)

        ## Channel Activation ##
        CHAN = 0x00000000
        amp = int32(amplitude)
        if ch0:
            spcm_dwSetParam_i32(hCard, SPC_ENABLEOUT0, 1)
            CHAN = CHAN ^ CHANNEL0
            spcm_dwSetParam_i32(hCard, SPC_AMP0, amp)
            spcm_dwSetParam_i64(hCard, SPC_FILTER0, int64(use_filter))
        if ch1:
            spcm_dwSetParam_i32(hCard, SPC_ENABLEOUT1, 1)
            CHAN = CHAN ^ CHANNEL1
            spcm_dwSetParam_i32(hCard, SPC_AMP1, amp)
            spcm_dwSetParam_i64(hCard, SPC_FILTER1, int64(use_filter))
        spcm_dwSetParam_i32(hCard, SPC_CHENABLE, CHAN)


    def _write_segment(wavs, pv_buf, pn_buf, offset=0):
        """ Writes set of waveforms consecutively into a single segment of board memory.
        Breaks down the transfer into manageable chunks.

        Parameters
        ----------
        wavs : list of :class:`~wavgen.waveform.Waveform`
            Waveforms to be written to the current segment.
        pv_buf : :obj:`ctypes.Array`
            Local contiguous PC buffer for transferring to Board.
        pn_buf : :obj:`ctypes.Pointer(int16)`
            Usable pointer to buffer, cast as correct data type.
        offset : int, optional
            Passed from :meth:`load_waveforms`, see description there.
        """
        total_so_far = offset
        start = time()
        for wav in wavs:
            size = min(wav.SampleLength, NUMPY_MAX)  # ALERT: changed to 2e9 just to be big.. should set another limit
            so_far = 0
            spcm_dwInvalidateBuf(hCard, SPCM_BUF_DATA)
            wav.load(pn_buf, 0, size)
            spcm_dwDefTransfer_i64(hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, int32(0), pv_buf, uint64(0),
                                   uint64(size * 2))
            dwError = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)


    def _setup_clock():
        """ Tries to achieve requested sampling frequency (see global parameter :data:`~wavgen.config.SAMP_FREQ`)
        """
        # spcm_dwSetParam_i32(self.hCard, SPC_CLOCKMODE, SPC_CM_INTPLL)# Sets out internal Quarts Clock For Sampling
        spcm_dwSetParam_i32(hCard, SPC_CLOCKMODE, SPC_CM_EXTREFCLOCK)
        spcm_dwSetParam_i32(hCard, SPC_REFERENCECLOCK, 10000000)
        spcm_dwSetParam_i64(hCard, SPC_SAMPLERATE, int64(int(SAMP_FREQ)))  # Sets Sampling Rate
        spcm_dwSetParam_i32(hCard, SPC_CLOCKOUT, 0)  # Disables Clock Output
        check_clock = int64(0)
        spcm_dwGetParam_i64(hCard, SPC_SAMPLERATE, byref(check_clock))  # Checks Sampling Rate
        verboseprint("Achieved Sampling Rate: ", check_clock.value)


    def stop_card():
        # assert Sequence, "Function only for debugging Sequential mode (for now)"
        status = int32(0)
        spcm_dwGetParam_i64(hCard, SPC_M2STATUS, byref(status))
        if status.value ^ M2STAT_CARD_READY:
            print("Card wasn't running in the first place")
        else:
            print("Stopping card.")
            spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_STOP)


    ##################################################################################################################
    setup_channels(amplitude=120, use_filter=False)
    print(A.SampleLength, B.SampleLength, AB.SampleLength)
    seg_size = A.SampleLength + B.SampleLength  # 1024
    start_step = 0
    print('here')
    pv_buf0 = pvAllocMemPageAligned(A.SampleLength * 2)  # times 2 because 2 bytes/sample I think?
    pn_buf0 = cast(pv_buf0, ptr16)  # Casts pointer into something usable
    print('here')
    pv_buf1 = pvAllocMemPageAligned(AB.SampleLength * 2)  # times 2 because 2 bytes/sample I think?
    pn_buf1 = cast(pv_buf1, ptr16)  # Casts pointer into something usable
    pv_buf2 = pvAllocMemPageAligned(B.SampleLength * 2)
    pn_buf2 = cast(pv_buf2, ptr16)  # Casts pointer into something usable
    print('here')
    # pv_buf3 = pvAllocMemPageAligned(C.SampleLength * 2)
    # pn_buf3 = cast(pv_buf3, ptr16)  # Casts pointer into something usable
    # print('here')

    _setup_clock()
    ##############################################
    # step tells us which segment to loop for how many times, and what the next step is
    max_segments = 4  # the caltech people use 8192
    # readout used bytes per sample
    lBytesPerSample = int32(0)
    spcm_dwGetParam_i32(hCard, SPC_MIINST_BYTESPERSAMPLE, byref(lBytesPerSample))
    # print(lBytesPerSample)
    # Setting up card mode
    spcm_dwSetParam_i32(hCard, SPC_CARDMODE, SPC_REP_STD_SEQUENCE)
    spcm_dwSetParam_i32(hCard, SPC_TRIG_ORMASK, SPC_TM_NONE)
    spcm_dwSetParam_i32(hCard, SPC_TRIG_ORMASK, SPC_TMASK_EXT0)
    spcm_dwSetParam_i32(hCard, SPC_TRIG_EXT0_LEVEL0, 1500)
    spcm_dwSetParam_i32(hCard, SPC_TRIG_EXT0_MODE, SPC_TM_POS)
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_MAXSEGMENTS, max_segments)
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_STARTSTEP, start_step)

    # # Set up data memory and transfer data


    # load waveform A to the buffer and transfer it to the card
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_WRITESEGMENT, 0)  # set current config switch to segment 0
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_SEGMENTSIZE, A.SampleLength)  # caltech people make all their segments multiples of 20us
    _write_segment([A], pv_buf0, pn_buf0, offset=0)
    # (SAMP_FREQ = 1GS/s)*(20us) = 20e3 samples
    # according to manual: min segment size is 384 samples for 1 active channel (192 samples for 2 active channels)
    # max segment size is 2 GS/active channels/number of sequence segments = 122e3 samples for 2 channels an 8192 segments


    # load waveform AB to the buffer and transfer it to the card
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_WRITESEGMENT, 1)  # set current config switch to segment 1
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_SEGMENTSIZE, AB.SampleLength)  # define size of current segment 1
    _write_segment([AB], pv_buf1, pn_buf1, offset=0)


    # load waveform B to the buffer and transfer it to the card
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_WRITESEGMENT, 2)  # set current config switch to segment 1
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_SEGMENTSIZE, B.SampleLength)  # define size of current segment 1
    _write_segment([B], pv_buf2, pn_buf2, offset=0)

    # # load waveform C to the buffer and transfer it to the card
    # spcm_dwSetParam_i32(hCard, SPC_SEQMODE_WRITESEGMENT, 3)  # set current config switch to segment 1
    # spcm_dwSetParam_i32(hCard, SPC_SEQMODE_SEGMENTSIZE, C.SampleLength)  # define size of current segment 1
    # _write_segment([C], pv_buf3, pn_buf3, offset=0)

    # setting up sequence memory
    # Step 0
    lStep = 0  # current step is step 0
    llSegment = 0  # associated data memory segment is the static waveform
    llLoop = 1  # pattern repeated
    llNext = 1  # next step is step 1
    llCondition = SPCSEQ_ENDLOOPONTRIG  # repeat current step until trig has occurred
    # combine all parameters into one int64 bit value
    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
    # # print(llValue)
    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

    # Step 1
    lStep = 1  # current step is step 1
    llSegment = 1  # sweep
    llLoop = 1  # pattern repeated
    llNext = 2  # next step is step 1
    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
    # combine all parameters into one int64 bit value
    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
    # # print(llValue)
    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

    # Step 2
    lStep = 2  # current step is step 2, static
    llSegment = 2  # associated data memory segment is 1
    llLoop = 10  # pattern repeated once
    llNext = 0  # next step is step 0
    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

    # Step 3
    # lStep = 3  # current step is step 3
    # llSegment = 3  # associated data memory segment is 3
    # llLoop = 10 #int(3E8//B.SampleLength)  # ~320 ms: 10000 for 32000 samples, 500000 for 640 samples
    # llNext = 0  # next step is step 0
    # llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
    # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
    # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

    ################################
    print('here1')

    WAIT = M2CMD_CARD_WAITTRIGGER

    ## Start card, try again if clock-not-locked ##
    spcm_dwSetParam_i32(hCard, SPC_TIMEOUT, int(15000))
    dwError = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_START)  # | M2CMD_CARD_ENABLETRIGGER | WAIT)
    count = 0
    while dwError == ERR_CLOCKNOTLOCKED:
        verboseprint("Clock not Locked, giving it a moment to adjust...")
        count += 1
        sleep(0.1)
        _error_check(halt=False, print_err=False)
        dwError = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_START)  # | M2CMD_CARD_ENABLETRIGGER | WAIT)
        if count == 10:
            verboseprint('count 10')
            break
    verboseprint('Clock Locked')
    spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_ENABLETRIGGER)
    spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_FORCETRIGGER)

    verboseprint('TriggerEnabled')

    # trigResult = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_WAITTRIGGER)
    # if trigResult == ERR_TIMEOUT:
    #     verboseprint("no trigger detected, force trigger now!")
    #     spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_FORCETRIGGER)

    _error_check()

    easygui.msgbox('Stop Card?', 'Infinite Looping!')
    spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_STOP)


