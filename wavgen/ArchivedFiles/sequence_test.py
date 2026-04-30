from wavgen import *
import easygui
import os
from wavgen.utilities import *
from wavgen.spectrum import *
from wavgen.constants import *
from wavgen.waveform import Superposition, even_spacing
import numpy as np
from time import time, sleep


if __name__ == '__main__':
    hCard = spcm_hOpen(create_string_buffer(b'/dev/spcm0'))
    ChanReady = False
    BufReady = False
    Sequence = False
    Wave = None
    offset = 0
    ntraps = 2
    freq_A = [94E6 + j * 6E6 for j in range(ntraps)]
    phases = utilities.rp[:ntraps]

    ## Define 2 Superposition objects ##
    A = Superposition(freq_A, phases=phases)  # One via the default constructor...
    B = even_spacing(ntraps, int(100E6), int(5E6),
                     phases=phases)  # ...the other with a useful constructor wrapper helper

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
            spcm_dwSetParam_i32(hCard, SPC_AMP0,       amp)
            spcm_dwSetParam_i64(hCard, SPC_FILTER0,    int64(use_filter))
        if ch1:
            spcm_dwSetParam_i32(hCard, SPC_ENABLEOUT1, 1)
            CHAN = CHAN ^ CHANNEL1
            spcm_dwSetParam_i32(hCard, SPC_AMP1,       amp)
            spcm_dwSetParam_i64(hCard, SPC_FILTER1,    int64(use_filter))
        spcm_dwSetParam_i32(hCard, SPC_CHENABLE,       CHAN)

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
            size = min(wav.SampleLength, NUMPY_MAX) #ALERT: changed to 2e9 just to be big.. should set another limit
            so_far = 0
            spcm_dwInvalidateBuf(hCard, SPCM_BUF_DATA)
            wav.load(pn_buf,0,size)
            spcm_dwDefTransfer_i64(hCard,SPCM_BUF_DATA,SPCM_DIR_PCTOCARD,int32(0),pv_buf,uint64(0),uint64(size*2))
            dwError = spcm_dwSetParam_i32(hCard, SPC_M2CMD,M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
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
    setup_channels(amplitude=350, use_filter=False)
    print(A.SampleLength, B.SampleLength)
    seg_size = A.SampleLength + B.SampleLength #1024
    start_step = 0
    print('here')
    pv_buf0 = pvAllocMemPageAligned(A.SampleLength*2) # times 2 because 2 bytes/sample I think?
    pn_buf0 = cast(pv_buf0, ptr16)  # Casts pointer into something usable
    print('here')
    #
    pv_buf1 = pvAllocMemPageAligned(B.SampleLength*2)
    pn_buf1 = cast(pv_buf1, ptr16)  # Casts pointer into something usable
    # _write_segment([A], pv_buf0, pn_buf0)
    print('here')

    _setup_clock()
##############################################
    # step tells us which segment to loop for how many times, and what the next step is
    max_segments = 4  # the caltech people use 8192
    # readout used bytes per sample
    lBytesPerSample = int32(0)
    spcm_dwGetParam_i32(hCard, SPC_MIINST_BYTESPERSAMPLE, byref(lBytesPerSample))
    print(lBytesPerSample)
    # Setting up card mode
    spcm_dwSetParam_i32(hCard, SPC_CARDMODE, SPC_REP_STD_SEQUENCE)
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_MAXSEGMENTS, max_segments)
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_STARTSTEP, start_step)


    # # Set up data memory and transfer data
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_WRITESEGMENT, 0)  # set current config switch to segment 0
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_SEGMENTSIZE,
                        A.SampleLength)  # caltech people make all their segments multiples of 20us
    # (SAMP_FREQ = 1GS/s)*(20us) = 20e3 samples
    # according to manual: min segment size is 384 samples for 1 active channel (192 samples for 2 active channels)
    # max segment size is 2 GS/active channels/number of sequence segments = 122e3 samples for 2 channels an 8192 segments

    # load waveform A to the buffer and transfer it to the card
    _write_segment([A], pv_buf0, pn_buf0, offset=0)


    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_WRITESEGMENT, 1)  # set current config switch to segment 1
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_SEGMENTSIZE, B.SampleLength)  # define size of current segment 1

    # load waveform B to the buffer and transfer it to the card
    _write_segment([B], pv_buf1, pn_buf1, offset=0)

    print('here')

    # setting up sequence memory (only 2 steps here as example)
    lStep = 0  # current step is step 0
    llSegment = 0  # associated data memory segment is 0
    llLoop = 10000  # pattern repeated 10 times
    llNext = 1  # next step is step 1
    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step

    # combine all parameters into one int64 bit value
    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
    # # print(llValue)
    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
    lStep = 1  # current step is step 1
    llSegment = 1  # associated data memory segment is 1
    llLoop = 10000  # pattern repeated once
    llNext = 0  # next step is step 0
    llCondition = SPCSEQ_ENDLOOPALWAYS  # repeat current step until trig has occurred
    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

################################
    print('here1')

    WAIT = M2CMD_CARD_WAITTRIGGER

    ## Start card, try again if clock-not-locked ##
    spcm_dwSetParam_i32(hCard, SPC_TIMEOUT, int(15000))
    dwError = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_START) # | M2CMD_CARD_ENABLETRIGGER | WAIT)
    count = 0
    while dwError == ERR_CLOCKNOTLOCKED:
        verboseprint("Clock not Locked, giving it a moment to adjust...")
        count += 1
        sleep(0.1)
        _error_check(halt=False, print_err=False)
        dwError = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_START) #| M2CMD_CARD_ENABLETRIGGER | WAIT)
        if count == 10:
            verboseprint('count 10')
            break
    verboseprint('Clock Locked')
    spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_ENABLETRIGGER)
    verboseprint('TriggerEnabled')

    trigResult = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_WAITTRIGGER)
    if trigResult == ERR_TIMEOUT:
        verboseprint("no trigger detected, force trigger now!")
        spcm_dwSetParam_i32(hCard,SPC_M2CMD,M2CMD_CARD_FORCETRIGGER)


    _error_check()

    easygui.msgbox('Stop Card?', 'Infinite Looping!')
    spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_STOP)
