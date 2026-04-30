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


class TestEventHandler(PatternMatchingEventHandler):

    i_counter=0

    def __init__(self, Cycle_num,  *args, **kwargs):
        super(TestEventHandler, self).__init__(*args, **kwargs)
        self.last_created = None
        self.Cycle_num = Cycle_num

    def on_created(self, event):
        tic = time.perf_counter()
        path = event.src_path
        if path != self.last_created:
            self.last_created = path
            # tic = time.perf_counter()
            print(f'{event.src_path} has been created!')
            time.sleep(0.05)
            try:
                hf = h5py.File(f'{event.src_path} ', 'r')
            except:
                time.sleep(0.05)
                hf = h5py.File(f'{event.src_path} ', 'r')
                print('exception')
            print('read file')
            im_array = np.array(hf['frame-00'])
            hf.close()
            atom_count, empty_list = analyze_image(im_array, tweezer_freq_list, num_tweezers)
            print(atom_count, empty_list)
            ##################################################################
            num_empty = len(empty_list)
            boundary = empty_list[int(num_empty/2)] #empty_list[int(num_empty/2)]
            empty_list = np.array(empty_list)
            if 0 < atom_count:
                segment_queue_L = []
                segment_queue_R = []
                # now divide into left and right sides of the boundary
                mask_L = empty_list < boundary
                mask_R = empty_list >= boundary
                empty_list_L = empty_list[mask_L]
                empty_list_R = empty_list[mask_R]
                for i in empty_list_L:
                    if i > 0:
                        segment_queue_L.append(segment_list[i - 1])
                for i in empty_list_R:
                    if i < num_tweezers-1:
                        segment_queue_R.append(segment_list[2*(num_tweezers-1)-i-1])
                segment_queue_R = np.flip(segment_queue_R)
                # print(f'segment_queue_L = {segment_queue_L}')
                # print(f'segment_queue_R = {segment_queue_R}')

                if len(segment_queue_L) > 0:
                    print('left sorting')
                    for k in range(len(segment_queue_L) - 1):
                        # print(segment_queue_L[k])
                        lStep = k + 1  # current step is step k+1 (+1 because step0 is the static config)
                        llSegment = segment_queue_L[k]  # associated data memory segment
                        llLoop = 1  # pattern repeated once
                        llNext = k + 2  # next step is the next sweep
                        llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))


                    lStep = len(segment_queue_L)  # current step is the last one in segment_queue
                    llSegment = segment_queue_L[-1]  # associated data memory segment
                    llLoop = 1  # pattern repeated once
                    if len(segment_queue_R) > 0:
                        llNext = len(segment_queue_L) + 1 # next go to resorting on the right
                    else:
                        print('dropping')
                        llNext = 2*num_tweezers + 21
                        llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    if len(segment_queue_R) > 0:
                        print('right sorting 1')
                        for k in range(len(segment_queue_R) - 1):
                            lStep = len(segment_queue_L) + k + 1  # current step is step k+1 (+1 because step0 is the static config)
                            llSegment = segment_queue_R[k]  # associated data memory segment
                            llLoop = 1  # pattern repeated once
                            llNext = len(segment_queue_L) + k + 2  # next step is the next sweep
                            llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = len(segment_queue_L) + len(segment_queue_R)  # current step is the last one in segment_queue
                        llSegment = segment_queue_R[-1]  # associated data memory segment
                        llLoop = 1  # pattern repeated once
                        llNext = 2*num_tweezers + 21  # this is sort of random, just want a number that is not called before
                        llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    else:
                        lStep = 2 * num_tweezers + 100
                        llSegment = 2 * num_tweezers - 2  # the static waveform
                        llLoop = 1
                        # trigResult = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_WAITTRIGGER)
                        # if trigResult == ERR_TIMEOUT:
                        #     llNext = 0
                        #     print('missed trig')
                        # else:
                        #     llNext = 2 * num_tweezers + 22 + num_cicero_loops-1  # next step is 0
                        llNext = 0
                        llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        # print(f'{num_cicero_loops + 3}th trig')
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))


                elif len(segment_queue_R) > 0 and len(segment_queue_L) == 0:
                    print('right sorting 2')
                    for k in range(len(segment_queue_R) - 1):
                        # print(segment_queue_R[k])
                        lStep = k + 1  # current step is step k+1 (+1 because step0 is the static config)
                        llSegment = segment_queue_R[k]  # associated data memory segment
                        llLoop = 1  # pattern repeated once
                        llNext = k + 2  # next step is the next sweep
                        llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))


                    lStep = len(segment_queue_R)  # current step is the last one in segment_queue
                    llSegment = segment_queue_R[-1]  # associated data memory segment
                    llLoop = 1  # pattern repeated once
                    llNext = 2 * num_tweezers + 21  # this is sort of random, just want a number that is not called before
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                else:
                    lStep = 1  # current step is step 1
                    llLoop = 1  # pattern repeated once
                    llSegment = 2*num_tweezers-1 + self.i_counter # the drop waveform
                    llNext = 0
                    # if len(segment_queue_R) > 0:
                    #     llSegment = segment_queue_R[0]  # start resorting on the right
                    #     llNext = 2  # go to next resort on the right. potential problem here is that when we start the for loop
                    #                 # for resorting on the right, we'll overwrite step1.
                    #     print('potential issue')
                    # else:
                    #     llSegment = segment_list[-1]  #num_tweezers # static
                    #     llNext = 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                lStep = 2 * num_tweezers + 21
                llSegment = 2 * num_tweezers - 1 + self.i_counter  # the drop waveform
                llLoop = int(3 * 0.001 * SAMP_FREQ / wf_list[
                    2 * num_tweezers - 1 + self.i_counter].SampleLength)  # pattern repeated once
                llNext = 2 * num_tweezers + 100  # 0  # next step is 0
                llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                print('2nd trig')
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                if multi_trig == True and seq == 'ANA':
                    lStep = 2 * num_tweezers + 100
                    llSegment = 2 * num_tweezers - 2  # the static waveform
                    llLoop = 1
                    # trigResult = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_WAITTRIGGER)
                    # if trigResult == ERR_TIMEOUT:
                    #     llNext = 0
                    #     print('missed trig')
                    # else:
                    #     llNext = 2 * num_tweezers + 22 + loop_num  # next step is 0
                    llNext = 2 * num_tweezers + 22
                    llCondition = SPCSEQ_ENDLOOPONTRIG  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    # print(f'{loop_num + 3}th trig')
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 22
                    llSegment = int(len(wf_list) - 4)  # 2*num_tweezers # sweep LtoR
                    llLoop = 1
                    llNext = 2 * num_tweezers + 22 + 1  # 0 # 2 * num_tweezers + 100  # next step is 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 23
                    llSegment = int(len(wf_list) - 3)  # 2 * num_tweezers + 1  # shifted waveform
                    llLoop = 1  # irrelevant if ending on trig
                    llNext = 2 * num_tweezers + 24  # 0 # 2 * num_tweezers + 100  # next step is 0
                    llCondition = SPCSEQ_ENDLOOPONTRIG  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 24
                    llSegment = int(len(wf_list) - 2)  # 2 * num_tweezers + 2  # sweep RtoL
                    llLoop = 1
                    llNext = 2 * num_tweezers + 25  # 0 # 2 * num_tweezers + 100  # next step is 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 25
                    llSegment = int(len(wf_list) - 1)  # segment_list[-1]  # the last shifted waveform
                    llLoop = int(0.3 * SAMP_FREQ / wf_list[-1].SampleLength)
                    llNext = 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                elif multi_trig == True and seq == 'half-int':
                    lStep = 2 * num_tweezers + 100
                    llSegment = 2 * num_tweezers - 2  # the static waveform
                    llLoop = 1
                    llNext = 2 * num_tweezers + 22
                    llCondition = SPCSEQ_ENDLOOPONTRIG  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 22
                    llSegment = 2 * num_tweezers  # sweep to 5lambda
                    llLoop = 1
                    llNext = 2 * num_tweezers + 22 + 1  # 0 # 2 * num_tweezers + 100  # next step is 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 23
                    llSegment = 2 * num_tweezers + 1  # static 5lambda
                    llLoop = int(50 * 0.001 * SAMP_FREQ / wf_list[2 * num_tweezers + 1].SampleLength)
                    llNext = 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                elif multi_trig == True and seq == 'half-int_ANA':
                    lStep = 2 * num_tweezers + 100
                    llSegment = 2 * num_tweezers - 2  # the static waveform
                    llLoop = 1
                    llNext = 2 * num_tweezers + 22
                    llCondition = SPCSEQ_ENDLOOPONTRIG  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    # print(f'{loop_num + 3}th trig')
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 22
                    llSegment = int(len(wf_list) - 5)  # 2 * num_tweezers  # sweep to 5.5lambda shifted by Lo4
                    llLoop = 1
                    llNext = 2 * num_tweezers + 23
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 23
                    llSegment = int(len(wf_list) - 4)  # 2 * num_tweezers + 1  # 5.5lambda shifted by Lo4
                    llLoop = 1
                    llNext = 2 * num_tweezers + 24  # 0 # 2 * num_tweezers + 100  # next step is 0
                    llCondition = SPCSEQ_ENDLOOPONTRIG  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 24
                    llSegment = int(len(wf_list) - 3)  # 2 * num_tweezers + 2  # sweep back by Lo4
                    llLoop = 1
                    llNext = 2 * num_tweezers + 25  # 0 # 2 * num_tweezers + 100  # next step is 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 25
                    llSegment = int(len(wf_list) - 2)  # 2 * num_tweezers + 3  # static 5.5lambda (not shifted)
                    llLoop = 1
                    llNext = 2 * num_tweezers + 26
                    llCondition = SPCSEQ_ENDLOOPONTRIG  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 26
                    llSegment = int(len(wf_list) - 1)  # 2 * num_tweezers + 4  # sweep to 5lambda spacing
                    llLoop = 1
                    llNext = 2 * num_tweezers + 27
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 27
                    llSegment = 2 * num_tweezers - 2  # static
                    llLoop = 1
                    llNext = 0
                    llCondition = SPCSEQ_ENDLOOPONTRIG
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))


            else:
                lStep = 1  # current step is step 1
                llSegment = 2*num_tweezers-1 + self.i_counter #2*num_tweezers - 2   # static
                # llLoop = int(25*4003200/wf_list[-1].SampleLength)  # pattern repeated once
                llLoop = int(16*6400000/wf_list[-1].SampleLength)  # pattern repeated once
                llNext = 0  # go back to step 0
                llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

            # toc = time.perf_counter()
            print(f'Cycle {self.i_counter:0.0f} of {self.Cycle_num:0.0f}')
            self.i_counter = (self.i_counter + 1) % self.Cycle_num
            toc = time.perf_counter()
            print(f'analysis took {toc - tic:0.6f} seconds')



if __name__ == '__main__':
    ntraps = 40 # this is the num of tweezers we want
    multi_trig = True
    # seq = 'ANA'
    # seq = 'half-int'
    seq = 'half-int_ANA'

    if multi_trig:
        if seq == 'ANA':
            path_folder = 'waveforms_160_40Twz_5lambda_v2'
            spacing = 0.8
            startfreq = 88
            multi_trig_list = ['sweep_LtoR_quarter_lambda.h5', 'shift_quarter_lambda.h5', 'sweep_RtoL_quarter_lambda.h5', 'static.h5'] #integer ANA
        elif seq == 'half-int_ANA':
            # path_folder = 'waveforms_160_40Twz_5lambda_v2'
            path_folder = 'waveforms_160_40Twz_5lambda_susc-meas'
            spacing = 0.8
            startfreq = 88
            # multi_trig_list = ['sweep_5to5,5lambda_shifted_Lo4.h5', 'static_5,5lambda_shifted_Lo4.h5', 'sweep_5,5to5lambda_back_Lo4.h5', 'static.h5', 'static.h5'] # for regular ANA
            # multi_trig_list = ['sweep_forward_5Lo16.h5', 'static_shifted_5Lo16.h5', 'sweep_back_5Lo16.h5', 'static.h5', 'static.h5']
            # multi_trig_list = ['sweep_to_half_shifted_Lo2_node.h5', 'static_half_shifted_Lo2_node.h5', 'sweep_from_half_shifted_Lo2_node.h5', 'static.h5',
            #                    'static.h5']
            multi_trig_list = ['sweep_to_half_shifted_Lo2_node_dualbias_Lo-64.h5', 'static_half-shifted_Lo2_dualbias_Lo-64.h5',
                               'sweep_from_half_shifted_Lo2_node_dualbias_Lo-64.h5', 'static.h5',
                               'static.h5']
        elif seq == 'half-int':
            path_folder = 'waveforms_160_40Twz_5,5lambda_v3'
            spacing = 0.88
            startfreq = 88
            multi_trig_list = ['sweep_5,5to5lambda.h5', 'static_5lambda_v1.h5'] # half-integer node only
    else:
        path_folder = 'waveforms_160_40Twz_5lambda_v2'
        spacing = 0.8
        startfreq = 88
        multi_trig_list = []
    cycle_list = ['drop_20.h5'] #, 'drop_middle_10_v2.h5']
    # cycle_list = ['drop_16_v1.h5', 'drop_8_new.h5', 'static.h5']
    # cycle_list = ['drop_1_twz14.h5', 'drop_1_twz26.h5', 'drop_2_twz14,26.h5']
    # cycle_list = ['static.h5'] #, 'drop_16_v1.h5', 'static.h5', 'drop_12.h5', 'static.h5', 'drop_8_new.h5', 'static.h5', 'drop_6.h5', 'drop_4.h5']


    # startfreq = spacing * 125
    # startfreq = 87.89 #5lambda_v1
    # startfreq = 88  # 5lambda_v2


    tweezer_freq_list = [startfreq + j * spacing for j in range(ntraps)]
    print(tweezer_freq_list)

    num_tweezers = len(tweezer_freq_list)
    date_dir = datetime.datetime.now().strftime("%Y\%m\%d")
    # DIR_DATA = Path('Y:/', 'expdata-e6', 'data', 'fluo_images_delete_1')
    DIR_DATA = Path('C:/', 'Users', 'CavityQED', 'Desktop', 'fluo_images_delete_1')

    filename_list_L = [f'sweep_{num}.h5' for num in range(1, ntraps)]
    filename_list_R = [f'sweep_{num}R.h5' for num in range(1, ntraps)]
    filename_list = np.concatenate((filename_list_L, filename_list_R))
    # print(filename_list)
    wf_list = []

    for filename in filename_list:
        if os.access(Path(path_folder, filename), os.F_OK):  # ...retrieve the Waveforms from file.
            wf_list.append(utilities.from_file(Path(path_folder, filename), 'AB'))

    # include static waveform
    wf_list.append(utilities.from_file(Path(path_folder, 'static.h5'), 'A'))

    # include drop waveform
    N_cycle = len(cycle_list)
    for filename in cycle_list:
        wf_list.append(utilities.from_file_simple(Path(path_folder, filename), 'A'))
    # include multi trig waveforms
    for filename in multi_trig_list:
        wf_list.append(utilities.from_file_simple(Path(path_folder, filename), 'A'))
    # include shifted waveform
    # wf_list.append(utilities.from_file_simple(Path(path_folder, 'static_shifted_-23970.h5'), 'A'))
    # segment_list = range(num_tweezers+1)
    print(f"wf_list_len={len(wf_list)}")
    segment_list = range(len(wf_list))

  ################################################

    # Now open the card
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

        assert 80 <= amplitude <= (1000 if use_filter else 480), "Amplitude must within interval: [80 - 2000]"
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
    setup_channels(amplitude=80, use_filter=False)
    _setup_clock()
    start_step = 0
    # step tells us which segment to loop for how many times, and what the next step is
    max_segments = len(wf_list) # num_tweezers + N_cycle
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
    llSegment = 2*num_tweezers-2  # associated data memory segment is static waveform
    llLoop = 1  # pattern repeated once
    llNext = 1 # next step is step 1
    llCondition = SPCSEQ_ENDLOOPONTRIG  # repeat current step until trig has occurred
    print('first trigger')
    # combine all parameters into one int64 bit value
    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

    lStep = 1
    llSegment = 2*num_tweezers-2
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
    my_event_handler = TestEventHandler(N_cycle, patterns, ignore_patterns, ignore_directories, case_sensitive)

    print('here')


    path = DIR_DATA
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)



#########################################################################
    WAIT = M2CMD_CARD_WAITTRIGGER

    ## Start card, try again if clock-not-locked ##
    spcm_dwSetParam_i32(hCard, SPC_TIMEOUT, int(1))
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



    _error_check()


    ################################
    my_observer.start()
    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()




