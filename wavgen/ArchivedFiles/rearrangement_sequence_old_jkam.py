import wavgen.constants
from wavgen import *
import easygui
from wavgen.utilities import *
from wavgen.spectrum import *
from wavgen.constants import *
import time
# from time import time, sleep
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from pathlib import Path
import datetime
import h5py
import numpy as np
from image_analysis import analyze_image
import shutil
import os.path

if __name__ == '__main__':
    run_name = 'run10'
    tweezer_freq_list = [98, 99, 100, 101, 102]
    num_tweezers = len(tweezer_freq_list)
    path_folder = 'waveforms_160us_5_twz'
    date_dir = datetime.datetime.now().strftime("%Y\%m\%d")
    # DIR_DATA = Path('Y:/', 'expdata-e6', 'data', str(date_dir), 'data', run_name, 'High NA Imaging')  # path where the data is saved
    DIR_DATA = Path('Y:/', 'expdata-e6', 'data', 'fluo_images_delete', str(date_dir), 'data', run_name, 'High NA Imaging')
    # date_dir1 = datetime.datetime.now().strftime("%Y/%m/%d")
    # year = datetime.datetime.now().strftime("%Y")
    # month = datetime.datetime.now().strftime("%m")
    # day = datetime.datetime.now().strftime("%d")

    # create a new directory for fluorescence images to be deleted, if it doesn't already exist
    # new_dir = 'Y:/expdata-e6/data/fluo_images_delete'
    # new_path_name = f'{new_dir}/{date_dir1}'
    # print(new_path_name)
    # new_path = Path(new_path_name)
    # isdir = os.path.isdir(new_path)
    # if not isdir:
    #     os.mkdir(f'{new_dir}/{year}')
    #     os.mkdir(f'{new_dir}/{year}/{month}')
    #     os.mkdir(f'{new_dir}/{year}/{month}/{day}')
    #     print(f'directory created')

    # filename_list = ['sweep_sequence_(97_98_100_101_102)-(98_99_100_101_102)_160us_phase_match',
    #                  'sweep_sequence_(97_98_99_101_102)-(98_99_100_101_102)_160us_phase_match',
    #                  'sweep_sequence_(97_98_99_100_102)-(98_99_100_101_102)_160us_phase_match',
    #                  'sweep_sequence_(97_98_99_100_101)-(98_99_100_101_102)_160us_phase_match']

    filename_list = ['sweep_1.h5',
                     'sweep_2.h5',
                     'sweep_3.h5',
                     'sweep_4.h5']
    wf_list = []
    # If we have already computed the Waveforms...
    # for filename in filename_list:
    #     if os.access(filename + '.h5', os.F_OK):  # ...retrieve the Waveforms from file.
    #         wf_list.append(utilities.from_file(filename, 'AB'))
    for filename in filename_list:
        if os.access(Path(path_folder, filename), os.F_OK):  # ...retrieve the Waveforms from file.
            wf_list.append(utilities.from_file(Path(path_folder, filename), 'AB'))

    # include static waveform
    wf_list.append(utilities.from_file(Path(path_folder, 'static.h5'), 'A'))
    # include static waveform
    # wf_list.append(utilities.from_file('static', 'A'))
    # include drop waveform. Want 3 tweezers deterministically loaded
    wf_list.append(utilities.from_file(Path(path_folder, 'static.h5'), 'A'))
    # wf_list.append(utilities.from_file('static', 'A'))
    # segment_list = [0, 1, 2, 3, 4, 5]
    segment_list = range(num_tweezers + 1)
    # Now open the card
    hCard = spcm_hOpen(create_string_buffer(b'/dev/spcm0'))
    ChanReady = False
    BufReady = False
    Sequence = False
    Wave = None
    offset = 0
    print(len(wf_list))
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
        start = time.time()
        # start = time()
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
    setup_channels(amplitude=120, use_filter=False) # amplitude previously at 350
    _setup_clock()
    start_step = 0
    # step tells us which segment to loop for how many times, and what the next step is
    max_segments = 10
    # readout used bytes per sample
    lBytesPerSample = int32(0)
    spcm_dwGetParam_i32(hCard, SPC_MIINST_BYTESPERSAMPLE, byref(lBytesPerSample))
    # Setting up card mode
    spcm_dwSetParam_i32(hCard, SPC_CARDMODE, SPC_REP_STD_SEQUENCE)
    spcm_dwSetParam_i32(hCard, SPC_TRIG_ORMASK, SPC_TM_NONE)
    spcm_dwSetParam_i32(hCard, SPC_TRIG_ORMASK, SPC_TMASK_EXT0)
    spcm_dwSetParam_i32(hCard, SPC_TRIG_EXT0_LEVEL0, 1500)
    spcm_dwSetParam_i32(hCard, SPC_TRIG_EXT0_MODE, SPC_TM_POS)
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_MAXSEGMENTS, max_segments)
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_STARTSTEP, start_step)

    ###############################################
    # create buffers and write segments to memory
    pv_buf_list = []
    pn_buf_list = []
    for j in range(len(segment_list)):
        pv_buf = pvAllocMemPageAligned(wf_list[j].SampleLength * 2)
        pv_buf_list.append(pv_buf)
        pn_buf_list.append(cast(pv_buf, ptr16))
    for j in range(len(segment_list)):
        spcm_dwSetParam_i32(hCard, SPC_SEQMODE_WRITESEGMENT, segment_list[j])  # set current config switch to segment j
        spcm_dwSetParam_i32(hCard, SPC_SEQMODE_SEGMENTSIZE, wf_list[j].SampleLength)
        _write_segment([wf_list[j]], pv_buf_list[j], pn_buf_list[j], offset=0)
########################################################################################################################
    # set up the static configuration
    lStep = 0  # current step is step 0
    llSegment = num_tweezers-1  # associated data memory segment is 4
    llLoop = 1  # pattern repeated once
    llNext = 1 # next step is step 1
    llCondition = SPCSEQ_ENDLOOPONTRIG  # repeat current step until trig has occurred
    # combine all parameters into one int64 bit value
    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

    lStep = 1
    llSegment = num_tweezers-1  # {0,1,2,3,4} config to reinitialize for next arrangement
    llLoop = 1
    llNext = 0  # next step is the next sweep
    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

    print('here1')

#######################################################################################################################
    # set up watchdog
    print('watchdog')
    patterns = ["*"]
    ignore_patterns = None
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    print('here')

    def on_created(event):
        tic = time.perf_counter()
        print(f'{event.src_path} has been created!')
        time.sleep(0.1)
        try:
            hf = h5py.File(f'{event.src_path} ', 'r')
        except:
            time.sleep(0.05)
            hf = h5py.File(f'{event.src_path} ', 'r')
        file_name = f'{event.src_path}'
        print('read file')
        im_array = np.array(hf['frame-00'])
        hf.close()
        atom_count, empty_list = analyze_image(im_array, tweezer_freq_list, num_tweezers)
        print(atom_count, empty_list)
        # shot_num = file_name[-8:-3]
        # if int(file_name[-4]) % 2 == 0:
        #     shutil.move(file_name, f'{new_dir}/{date_dir1}/{run_name}_{shot_num}.h5')
        #     print(f'moved file {shot_num}')


        if 0 < atom_count:
            segment_queue = []
            for i in range(len(empty_list)):
                if empty_list[i] > 0:
                    segment_queue.append(segment_list[empty_list[i] - 1])
            if len(segment_queue) > 0:
                for k in range(len(segment_queue) - 1):
                    lStep = k + 1  # current step is step k+1 (+1 because step0 is the static config)
                    llSegment = segment_queue[k]  # associated data memory segment
                    llLoop = 1  # pattern repeated once
                    llNext = 10 + k  # next step is {0,1,2,3,4} config (10 chosen randomly)
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                    # print(f'step {k} configured')

                    lStep = 10 + k
                    llSegment = num_tweezers-1  # {0,1,2,3,4} config to reinitialize for next arrangement
                    llLoop = 1
                    llNext = k + 2  # next step is the next sweep
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                lStep = len(segment_queue)  # current step is the last one in segment_queue
                llSegment = segment_queue[-1]  # associated data memory segment
                llLoop = 1  # pattern repeated once
                llNext = 20  # next step is 20
                llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                lStep = 20  # 20 chosen randomly
                llSegment = num_tweezers  # the drop waveform
                llLoop = 5  # pattern repeated
                llNext = 0  # next step is 0
                llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

            else:
                lStep = 1  # current step is step 1
                llSegment = num_tweezers-1  # associated data memory segment
                llLoop = 1  # pattern repeated once
                llNext = 20  # go back to step 0
                llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                lStep = 20  # 20 chosen randomly
                llSegment = num_tweezers  # the drop waveform
                llLoop = 5  # pattern repeated once
                llNext = 0  # next step is 0
                llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

        else:
            lStep = 1  # current step is step 1
            llSegment = num_tweezers-1  # associated data memory segment
            llLoop = 1  # pattern repeated once
            llNext = 0  # go back to step 0
            llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))


        toc = time.perf_counter()
        print(f'analysis took {toc-tic:0.6f} seconds')

    my_event_handler.on_created = on_created
    path = DIR_DATA
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)



#########################################################################
    WAIT = M2CMD_CARD_WAITTRIGGER

    ## Start card, try again if clock-not-locked ##
    spcm_dwSetParam_i32(hCard, SPC_TIMEOUT, int(15000))
    dwError = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_START)  # | M2CMD_CARD_ENABLETRIGGER | WAIT)
    count = 0
    while dwError == ERR_CLOCKNOTLOCKED:
        verboseprint("Clock not Locked, giving it a moment to adjust...")
        count += 1
        time.sleep(0.1)
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


    ################################
    my_observer.start()
    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()

    easygui.msgbox('Stop Card?', 'Infinite Looping!')
    spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_STOP)

