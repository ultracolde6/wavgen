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
import datetime


class TestEventHandler(PatternMatchingEventHandler):

    # i_counter=0

    def __init__(self, Cycle_num, drop_num, AXA_num, *args, **kwargs):
        super(TestEventHandler, self).__init__(*args, **kwargs)
        self.last_created = None
        self.Cycle_num = Cycle_num
        self.AXA_num = AXA_num
        self.drop_num = drop_num
        self.drop_counter=0
        self.AXA_counter=0
        self.i_counter=0
        self.previous_time = time.time()
        self.current_time = time.time()
        self.shot_counter=0
        self.tic = time.perf_counter()
        self.bad_shot_list=[]


    def on_created(self, event):
        # global tic_1
        tic_1 = time.perf_counter()

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
            tic_2 = time.perf_counter()
            try:
                print('tic_2-tic_1', tic_2-tic_1)
                time_diff = tic_2-tic_1
            except:
                time_diff = 0
            if time_diff>0.8:
                print('skipping')
                self.bad_shot_list.append(self.shot_counter+1)
                lStep = 1
                llSegment = 2 * num_tweezers - 2
                llLoop = 1
                llNext = 0
                llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
            else:
            ##################################################################
                if 0 < atom_count:
                    segment_queue_L = []
                    segment_queue_R = []
                    # now divide into left and right sides of the boundary
                    mask_empty = np.diff(empty_list) > 1
                    for i in range(len(mask_empty)):
                        if mask_empty[i] and empty_list[0] == 0:
                            empty_list_reduced = empty_list[i+1:]
                            break
                        else:
                            empty_list_reduced = empty_list
                    for i in range(len(mask_empty)):
                        if mask_empty[-1-i] and empty_list[-1] == num_tweezers-1:
                            empty_list_reduced = empty_list_reduced[:-1-i]
                            break
                    # drop an extra atom if len(empty_list) is odd (this means the num of loaded tweezers is also odd, assuming num_tweezers is even)
                    # if len(empty_list)%2 and len(empty_list_reduced)>0:
                    #     if empty_list_reduced[0] != 0:
                    #         print('extra drop')
                    #         empty_list_reduced.append(empty_list_reduced[0]-1)
                    #     elif empty_list_reduced[-1] != num_tweezers-1:
                    #         print('extra drop')
                    #         empty_list_reduced.append(empty_list_reduced[-1]+1)
                    # elif len(empty_list)%2 and len(empty_list_reduced)==0:
                    #     for i in range(len(mask_empty)):
                    #         if mask_empty[i] and empty_list[0] == 0:
                    #             empty_list_reduced.append(empty_list[i]+1)
                    #             print('extra drop')
                    #             break
                    #         elif mask_empty[-1 - i] and empty_list[-1] == num_tweezers - 1:
                    #             empty_list_reduced.append(empty_list[-1 - i]-1)
                    #             print('extra drop')
                    #             break

                    # now divide into left and right sides of the boundary
                    empty_list_reduced=np.sort(empty_list_reduced)
                    print('empty_list_reduced:', empty_list_reduced)
                    num_empty = len(empty_list)
                    boundary = empty_list[int(num_empty / 2)]
                    print('boundary:', boundary)
                    mask_L = empty_list_reduced <= boundary
                    mask_R = empty_list_reduced > boundary
                    empty_list_L = empty_list_reduced[mask_L]
                    empty_list_R = empty_list_reduced[mask_R]
                    for i in empty_list_L:
                        if i > 0:
                            segment_queue_L.append(segment_list[i - 1])
                    for i in empty_list_R:
                        if i < num_tweezers-1:
                            segment_queue_R.append(segment_list[2*(num_tweezers-1)-i-1])
                    segment_queue_R = np.flip(segment_queue_R)
                    print(f'segment_queue_L = {segment_queue_L}')
                    print(f'segment_queue_R = {segment_queue_R}')

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
                        llSegment = 2*num_tweezers-1 + self.drop_counter # the drop waveform
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
                    print(f"####################{self.drop_counter}###################")
                    llSegment = 2 * num_tweezers - 1 + self.drop_counter  # the drop waveform
                    llLoop = int(10 * 0.001 * SAMP_FREQ / wf_list[llSegment].SampleLength)  # pattern repeated once
                    llNext = 2 * num_tweezers + 100  # 0  # next step is 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    tic1 = time.perf_counter()
                    # print('2nd trig')
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))


                    ##################### Start of AXA ############################
                    if multi_trig == True and hold_drop:
                        for counter_temp_AXA_loop in range(multi_trig_loops):
                            print(f"{counter_temp_AXA_loop}    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

                            if counter_temp_AXA_loop == 0:
                                lStep = 2 * num_tweezers + 100
                            else:
                                lStep = 2 * num_tweezers + 21 + counter_temp_AXA_loop*4
                            # llSegment = 2 * num_tweezers - 1 + self.drop_counter + 1 # the drop waveform
                            llSegment = 2 * num_tweezers - 1 + 0 # the first drop waveform
                            llLoop = 1
                            llNext = 2 * num_tweezers + 22 + counter_temp_AXA_loop*4
                            llCondition = SPCSEQ_ENDLOOPONTRIG  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                            # print(f'{loop_num + 3}th trig')
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                            lStep = 2 * num_tweezers + 22 + counter_temp_AXA_loop*4
                            llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter))  # sweep A to X
                            llLoop = 1
                            llNext = 2 * num_tweezers + 23 + counter_temp_AXA_loop*4
                            llCondition = SPCSEQ_ENDLOOPALWAYS  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                            lStep = 2 * num_tweezers + 23 + counter_temp_AXA_loop*4
                            llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter) + 1)  # hold X
                            llLoop = 1
                            llNext = 2 * num_tweezers + 24 + counter_temp_AXA_loop*4
                            llCondition = SPCSEQ_ENDLOOPONTRIG   # stay at X until triggered
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                            toc1 = time.perf_counter()
                            # print(toc1 - tic1)
                            lStep = 2 * num_tweezers + 24 + counter_temp_AXA_loop*4
                            llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter) + 2)  # sweep X to A
                            llLoop = 1
                            llNext = 2 * num_tweezers + 25 + counter_temp_AXA_loop*4
                            llCondition =  SPCSEQ_ENDLOOPALWAYS # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = 2 * num_tweezers + 25 + counter_temp_AXA_loop*4
                        # llSegment = 2 * num_tweezers - 1 + self.drop_counter + 1 # the drop waveform
                        llSegment = 2 * num_tweezers - 1 + 0 # the first drop waveform
                        llLoop = 1
                        if multi_loop:
                            llNext = 1 # the first sorting step <- this should be 0 if not for the next sort
                        else:
                            llNext = 0 # back to static waveform
                        llCondition = SPCSEQ_ENDLOOPONTRIG
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    elif multi_trig == True and not hold_drop:
                        lStep = 2 * num_tweezers + 100
                        llSegment = 2 * num_tweezers - 2  # the static waveform
                        llLoop = 1
                        llNext = 2 * num_tweezers + 22
                        llCondition = SPCSEQ_ENDLOOPONTRIG  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        # print(f'{loop_num + 3}th trig')
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = 2 * num_tweezers + 22
                        llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter))  # 2 * num_tweezers  # sweep to 5.5lambda shifted by Lo4
                        llLoop = 1
                        llNext = 2 * num_tweezers + 23
                        llCondition = SPCSEQ_ENDLOOPALWAYS  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = 2 * num_tweezers + 23
                        llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter) + 1)  # 2 * num_tweezers + 1  # 5.5lambda shifted by Lo4
                        llLoop = 1
                        llNext = 2 * num_tweezers + 24  # 0 # 2 * num_tweezers + 100  # next step is 0
                        llCondition = SPCSEQ_ENDLOOPONTRIG  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                        toc1 = time.perf_counter()
                        # print(toc1 - tic1)
                        lStep = 2 * num_tweezers + 24
                        llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter) + 2)  # 2 * num_tweezers + 2  # sweep back by Lo4
                        llLoop = 1
                        llNext = 2 * num_tweezers + 25  # 0 # 2 * num_tweezers + 100  # next step is 0
                        llCondition =  SPCSEQ_ENDLOOPALWAYS # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        # lStep = 2 * num_tweezers + 25
                        # llSegment = int(len(wf_list) - 2)  # 2 * num_tweezers + 3  # static 5.5lambda (not shifted)
                        # llLoop = 1
                        # llNext = 2 * num_tweezers + 26
                        # llCondition = SPCSEQ_ENDLOOPONTRIG  # unconditionally leave current step
                        # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                        #
                        # lStep = 2 * num_tweezers + 26
                        # llSegment = int(len(wf_list) - 1)  # 2 * num_tweezers + 4  # sweep to 5lambda spacing
                        # llLoop = 1
                        # llNext = 2 * num_tweezers + 27
                        # llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = 2 * num_tweezers + 25
                        llSegment = 2 * num_tweezers - 2  # static
                        llLoop = 1
                        llNext = 0
                        llCondition = SPCSEQ_ENDLOOPONTRIG
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    else:
                        lStep = 2 * num_tweezers + 100

                        if hold_drop:
                            # llSegment = 2 * num_tweezers - 1 + self.drop_counter # the drop waveform
                            llSegment = 2 * num_tweezers - 1 + 0 # the first drop waveform
                            llLoop = 1
                            llNext = 0
                            llCondition = SPCSEQ_ENDLOOPONTRIG  # unconditionally leave current step
                            # print(f'{loop_num + 3}th trig')
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                        else:
                            llSegment = 2 * num_tweezers - 2  # the static waveform
                            llLoop = 1
                            llNext = 0
                            llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                            # print(f'{loop_num + 3}th trig')
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))


                else:
                    lStep = 1  # current step is step 1

                    llSegment = 2*num_tweezers-1 + self.drop_counter #2*num_tweezers - 2   # drop
                    # llLoop = int(25*4003200/wf_list[-1].SampleLength)  # pattern repeated once
                    llLoop = int(5 * 0.001 * SAMP_FREQ / wf_list[llSegment].SampleLength)  # pattern repeated once
                    llNext = 0  # go back to step 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                # toc = time.perf_counter()
                # print(f'Cycle {self.i_counter:0.0f} of {self.Cycle_num:0.0f}')
                self.current_time = time.time()
                print("********************************")

                # date_dir_log = datetime.datetime.now().strftime("%Y\%m\%d")
                # DIR_DATA_log = Path('X:/', 'expdata-e6', 'data', date_dir_log, "run_test")
                # if not os.path.exists(DIR_DATA_log):
                #     os.makedirs(DIR_DATA_log)
                ################Write in logger file#######################
                # log_file_path = Path(DIR_DATA_log, "wavegen_log.txt")
                # current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # log_entry = f"{current_time}, Cycle {self.drop_counter:0.0f} of {self.drop_num:0.0f} in drop, " \
                #             f"Cycle {self.AXA_counter:0.0f} of {self.AXA_num:0.0f} in AXA \n"
                # with open(log_file_path, 'a') as log_file:
                #     log_file.write(log_entry)
                ##########################################################

                print(f'Cycle {self.drop_counter:0.0f} of {self.drop_num:0.0f} in drop waveforms')
                print(f'Cycle {self.AXA_counter:0.0f} of {self.AXA_num:0.0f} in AXA waveforms')
                print("*******************************")
                # if (self.current_time - self.previous_time > 13):
                #     print('missed trigger!')
                #     self.i_counter = (self.i_counter + 2) % self.Cycle_num
                #     self.drop_counter = (self.drop_counter + 2) % self.drop_num
                #     # self.drop_counter = 0
                #     self.AXA_counter = (self.AXA_counter + 2) % self.AXA_num  # currently Cycle_num = AXA_num, and drop_num=1.
                # elif (self.current_time - self.previous_time < 4):
                #     print('missed trigger!')
                #     self.i_counter = (self.i_counter + 0) % self.Cycle_num
                #     self.drop_counter = (self.drop_counter + 0) % self.drop_num
                #     # self.drop_counter = 0
                #     self.AXA_counter = (self.AXA_counter + 0) % self.AXA_num  # currently Cycle_num = AXA_num, and drop_num=1.
                # else:
                self.i_counter = (self.i_counter + 1) % self.Cycle_num
                self.drop_counter = (self.drop_counter + 1) % self.drop_num
                # self.drop_counter = 0
                self.AXA_counter = (self.AXA_counter + 1) % self.AXA_num #currently Cycle_num = AXA_num, and drop_num=1.

                self.previous_time = self.current_time
                self.shot_counter += 1
                print('shot', self.shot_counter)
                toc = time.perf_counter()
                print(f'analysis took {toc - self.tic:0.6f} seconds')
                print('bad_shot_list:', self.bad_shot_list)
                self.tic=toc


class TestEventHandler_3(PatternMatchingEventHandler): # for multi_loop

    def __init__(self, Cycle_num, drop_num, AXA_num, loop_num, *args, **kwargs):
        super(TestEventHandler_3, self).__init__(*args, **kwargs)
        self.last_created = None
        self.Cycle_num = Cycle_num
        self.AXA_num = AXA_num
        self.drop_num = drop_num
        self.loop_num = loop_num
        self.drop_counter=0
        self.AXA_counter=0
        self.loop_counter=0
        self.i_counter=0
        self.previous_time = time.time()
        self.current_time = time.time()
        self.shot_counter=0
        self.tic = time.perf_counter()
        self.bad_shot_list=[]


    def on_created(self, event):
        # global tic_1
        tic_1 = time.perf_counter()

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
            atom_count, empty_list = analyze_image(im_array, tweezer_freq_list_drop, num_tweezers_drop)
            print(atom_count, empty_list)
            tic_2 = time.perf_counter()
            try:
                print('tic_2-tic_1', tic_2-tic_1)
                time_diff = tic_2-tic_1
            except:
                time_diff = 0
            if time_diff>0.8:
                print('skipping')
                self.bad_shot_list.append(self.shot_counter+1)
                lStep = 2 * num_tweezers + 25
                llSegment = 2 * num_tweezers - 1 + 0  # the first drop waveform
                llLoop = 1
                llNext = 2 * num_tweezers + 25
                llCondition = SPCSEQ_ENDLOOPALWAYS
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
            else:
            ##################################################################
                if -1 < atom_count:
                    print('there are atoms!')
                    segment_queue_L = []
                    segment_queue_R = []
                    # now divide into left and right sides of the boundary
                    mask_empty = np.diff(empty_list) > 1
                    for i in range(len(mask_empty)):
                        if mask_empty[i] and empty_list[0] == 0:
                            empty_list_reduced = empty_list[i+1:]
                            break
                        else:
                            empty_list_reduced = empty_list
                    for i in range(len(mask_empty)):
                        if mask_empty[-1-i] and empty_list[-1] == num_tweezers_drop-1:
                            empty_list_reduced = empty_list_reduced[:-1-i]
                            break
                    # if len(empty_list)%2 and len(empty_list_reduced)>0:
                    #     if empty_list_reduced[0] != 0:
                    #         print('extra drop')
                    #         empty_list_reduced.append(empty_list_reduced[0]-1)
                    #     elif empty_list_reduced[-1] != num_tweezers-1:
                    #         print('extra drop')
                    #         empty_list_reduced.append(empty_list_reduced[-1]+1)
                    # elif len(empty_list)%2 and len(empty_list_reduced)==0:
                    #     for i in range(len(mask_empty)):
                    #         if mask_empty[i] and empty_list[0] == 0:
                    #             empty_list_reduced.append(empty_list[i]+1)
                    #             print('extra drop')
                    #             break
                    #         elif mask_empty[-1 - i] and empty_list[-1] == num_tweezers - 1:
                    #             empty_list_reduced.append(empty_list[-1 - i]-1)
                    #             print('extra drop')
                    #             break

                    # now divide into left and right sides of the boundary
                    if len(mask_empty) <= 0 or dont_sort_AXA:  # try to catch bug where empty_list_reduced is never defined
                        empty_list_reduced=[]
                    empty_list_reduced=np.sort(empty_list_reduced)
                    print('empty_list_reduced:', empty_list_reduced)
                    num_empty = len(empty_list)
                    boundary = empty_list[int(num_empty / 2)]
                    print('boundary:', boundary)
                    mask_L = empty_list_reduced <= boundary
                    mask_R = empty_list_reduced > boundary
                    empty_list_L = empty_list_reduced[mask_L]
                    empty_list_R = empty_list_reduced[mask_R]
                    for i in empty_list_L:
                        if i > 0:
                            segment_queue_L.append(segment_list_drop[i-1 + len(segment_list)])
                    for i in empty_list_R:
                        if i < num_tweezers_drop-1:
                            segment_queue_R.append(segment_list_drop[2*(num_tweezers_drop-1)-i-1 + len(segment_list)])
                    segment_queue_R = np.flip(segment_queue_R)
                    print(f'segment_queue_L = {segment_queue_L}')
                    print(f'segment_queue_R = {segment_queue_R}')

                    # Step 0: Static configuration (waits for trigger)
                    # Steps 1-20: Dynamic sorting sequence (left/right sweeps to fill empty sites)
                    # Step 21: Drop waveform execution (removes unwanted atoms)
                    # Step 121: Multi-loop decision point (checks if more loops needed)
                    # Steps 22-24: AXA sequence
                    # Step 25: Return to sorting for next cycle (if not final loop)
                    #
                    # Flow: Static(0) -> Sort(1-20) -> Drop(21) -> LoopCheck(121) -> AXA(22-24) -> Sort(1) -> ...
                    #       After final loop: LoopCheck(121) -> Static(0) [sequence ends]
                    
                    # SORTING SEQUENCE: Steps 1 through ~20 (dynamically set based on empty sites)
                    if len(segment_queue_L) > 0:
                        print('left sorting')
                        # STEPS 1 to (len(segment_queue_L)-1): Left-side sorting sweeps
                        # These steps perform sequential sorting sweeps from left to right
                        # Each sweep moves atoms to fill empty sites on the left side of the array
                        for k in range(len(segment_queue_L) - 1): # last step is left out
                            # print(segment_queue_L[k])
                            lStep = k + 1  # current step is step k+1 (+1 because step0 is the static config)
                            llSegment = segment_queue_L[k]  # associated data memory segment (sorting waveform)
                            llLoop = 1  # pattern repeated once
                            llNext = k + 2  # next step is the next sweep in sequence
                            llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step after completion
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))


                        # STEP (len(segment_queue_L)): Final left-side sorting sweep
                        # Last sorting sweep on the left side
                        # Transitions to right-side sorting if needed, or goes directly to drop step
                        lStep = len(segment_queue_L)  # current step is the last one in left segment_queue
                        llSegment = segment_queue_L[-1]  # associated data memory segment (final left sorting waveform)
                        llLoop = 1  # pattern repeated once
                        if len(segment_queue_R) > 0:
                            llNext = len(segment_queue_L) + 1 # next go to re-sorting on the right (start right sorting)
                        else: # right side is all fine
                            print('no right sorting, going straight to dropping')
                            llNext = 2*num_tweezers + 31  # skip right sorting, go directly to drop step
                        llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step after completion
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        if len(segment_queue_R) > 0:
                            print('right sorting 1')
                            # STEPS (len(segment_queue_L)+1) to (len(segment_queue_L)+len(segment_queue_R)-1): Right-side sorting sweeps
                            for k in range(len(segment_queue_R) - 1):
                                lStep = len(segment_queue_L) + k + 1  # current step continues after left sorting steps
                                llSegment = segment_queue_R[k]  # associated data memory segment (right sorting waveform)
                                llLoop = 1  # pattern repeated once
                                llNext = len(segment_queue_L) + k + 2  # next step is the next right sweep
                                llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step after completion
                                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                            # STEP (len(segment_queue_L) + len(segment_queue_R)): Final right-side sorting sweep
                            lStep = len(segment_queue_L) + len(segment_queue_R)  # current step is the last one in segment_queue
                            llSegment = segment_queue_R[-1]  # associated data memory segment (final right sorting waveform)
                            llLoop = 1  # pattern repeated once
                            llNext = 2*num_tweezers + 31  # next: step 21 (drop waveform execution)
                            llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step after completion
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        else:
                            print('is this ever reached?')
                            # lStep = 2 * num_tweezers + 100
                            # llSegment = 2 * num_tweezers - 1 + self.drop_counter + 1
                            # # llSegment = 2 * num_tweezers - 1 + 0
                            # llLoop = 1
                            # llNext = 2 * num_tweezers + 22
                            # llCondition = SPCSEQ_ENDLOOPONTRIG
                            # # print(f'{loop_num + 3}th trig')
                            # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))


                    elif len(segment_queue_R) > 0 and len(segment_queue_L) == 0:
                        # CASE: Right-side sorting only (no left-side empty sites)
                        # STEPS 1 to len(segment_queue_R): Right-side sorting sweeps only
                        print('right sorting 2 without left sorting')
                        # STEPS 1 to (len(segment_queue_R)-1): Right-side sorting sweeps
                        for k in range(len(segment_queue_R) - 1):
                            # print(segment_queue_R[k])
                            lStep = k + 1  # current step is step k+1 (+1 because step0 is the static config)
                            llSegment = segment_queue_R[k]  # associated data memory segment (right sorting waveform)
                            llLoop = 1  # pattern repeated once
                            llNext = k + 2  # next step is the next right sweep
                            llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step after completion
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))


                        # STEP len(segment_queue_R): Final right-side sorting sweep
                        # Last sorting sweep on the right side
                        # After this, all sorting is complete, proceed to drop step
                        lStep = len(segment_queue_R)  
                        llSegment = segment_queue_R[-1]  
                        llLoop = 1  
                        llNext = 2 * num_tweezers + 31
                        llCondition = SPCSEQ_ENDLOOPALWAYS 
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    else:
                        # CASE: No sorting needed (no empty sites to fill, or all atoms already in place)
                        # STEP 1: Skip directly to drop waveform
                        # If no sorting is required, go straight to drop step
                        print('no left or right sorting')
                        lStep = 1  # current step is step 1
                        llSegment = 2 * num_tweezers - 1 + self.drop_counter + 1  # the drop waveform
                        llLoop = 1
                        llNext = 2 * num_tweezers + 31  # next: step 21 (drop waveform execution)
                        llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step after completion
                        # print(f'{loop_num + 3}th trig')
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    # STEP 21: Drop waveform execution
                    # This step executes the drop waveform to remove unwanted atoms
                    # After completion, it transitions to step 121 for multi-loop check
                    lStep = 2 * num_tweezers + 31 # was 21
                    print(f"####################{self.drop_counter}###################")
                    llSegment = 2 * num_tweezers - 1 + self.drop_counter + 1  # the drop waveform
                    llLoop = int(10 * 0.001 * SAMP_FREQ / wf_list[llSegment].SampleLength)  # pattern repeated for 10 ms
                    llNext = 2 * num_tweezers + 121  # next step: 121 (multi-loop decision point)
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step after loop completes
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))


                    ##################### Start of AXA  sequence ############################
                    # Multi-loop mode: Allows multiple rearrangement cycles after initial drop
                    # This enables iterative improvement of atom positioning
                    if multi_trig == True and hold_drop and multi_loop:

                        # print('test test test')
                        # print(self.drop_counter)


                        for counter_temp_AXA_loop in range(multi_trig_loops):
                            print(f"{counter_temp_AXA_loop}   ????????????????????")

                            # STEP 121: Multi-loop decision point
                            # Holds the drop waveform and waits for trigger
                            # Checks if this is the final loop iteration
                            # - If final loop (loop_counter == loop_num-1): goes to step 0 (static, ends sequence)
                            # - If not final: goes to step 22 (starts AXA sequence for next rearrangement)
                            if counter_temp_AXA_loop == 0:
                                lStep = 2 * num_tweezers + 121
                            else:
                                lStep = 2 * num_tweezers + 21 + counter_temp_AXA_loop*4

                            llSegment = 2 * num_tweezers - 1 + self.drop_counter + 1  # the drop waveform (held during wait)
                            llLoop = 1
                            if self.loop_counter == (self.loop_num - 1):  # stop the loop
                                print('Final rearrangement')
                                llNext = 0  # go back to static waveform after final trigger (end of multi-loop)
                            else:
                                print('Continuing to next rearrangement')
                                llNext = 2 * num_tweezers + 22 + counter_temp_AXA_loop*4  # proceed to AXA sequence for next iteration
                            llCondition = SPCSEQ_ENDLOOPONTRIG  # wait for external trigger before proceeding
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                            # STEP 22: AXA - Sweep to target spacing
                            # First part of AXA sequence: sweep to target spacing (e.g., 3.5 lambda)
                            lStep = 2 * num_tweezers + 22 + counter_temp_AXA_loop*4
                            llSegment = int(len(wf_list) - 3 * (
                                        self.AXA_num - self.AXA_counter))  # sweep to target spacing waveform
                            llLoop = 1
                            llNext = 2 * num_tweezers + 23 + counter_temp_AXA_loop*4  # next: step 23 (hold at target spacing)
                            llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally proceed after waveform completes
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                            # STEP 23: AXA - Hold at target spacing
                            # Second part of AXA sequence: hold at target spacing and wait for trigger
                            lStep = 2 * num_tweezers + 23 + counter_temp_AXA_loop*4
                            llSegment = int(len(wf_list) - 3 * (
                                        self.AXA_num - self.AXA_counter) + 1)  # static at target spacing waveform
                            llLoop = 1
                            llNext = 2 * num_tweezers + 24 + counter_temp_AXA_loop*4
                            llCondition = SPCSEQ_ENDLOOPONTRIG
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                            toc1 = time.perf_counter()
                            # print(toc1 - tic1)

                            # STEP 24: AXA - Sweep back to original spacing
                            # Third part of AXA sequence: sweep back from target spacing to original
                            # Returns the tweezer array to its normal operating configuration
                            lStep = 2 * num_tweezers + 24 + counter_temp_AXA_loop*4
                            llSegment = int(
                                len(wf_list) - 3 * (self.AXA_num - self.AXA_counter) + 2)  # sweep back waveform
                            llLoop = 1
                            llNext = 2 * num_tweezers + 25 + counter_temp_AXA_loop*4  # next: step 25 (return to sorting or end)
                            llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally proceed after waveform completes
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))



                            #
                            # if counter_temp_AXA_loop == 0:
                            #     lStep = 2 * num_tweezers + 121
                            # else:
                            #     lStep = 2 * num_tweezers + 21 + counter_temp_AXA_loop*4
                            # # llSegment = 2 * num_tweezers - 1 + self.drop_counter + 1 # the drop waveform
                            # llSegment = 2 * num_tweezers - 1 + self.drop_counter + 1  # the drop waveform (held during wait)
                            # llLoop = 1
                            # llNext = 2 * num_tweezers + 22 + counter_temp_AXA_loop*4
                            # llCondition = SPCSEQ_ENDLOOPONTRIG  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                            # # print(f'{loop_num + 3}th trig')
                            # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                            #
                            # lStep = 2 * num_tweezers + 22 + counter_temp_AXA_loop*4
                            # llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter))  # sweep A to X
                            # llLoop = 1
                            # llNext = 2 * num_tweezers + 23 + counter_temp_AXA_loop*4
                            # llCondition = SPCSEQ_ENDLOOPALWAYS  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                            # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                            #
                            # lStep = 2 * num_tweezers + 23 + counter_temp_AXA_loop*4
                            # llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter) + 1)  # hold X
                            # llLoop = 1
                            # llNext = 2 * num_tweezers + 24 + counter_temp_AXA_loop*4
                            # llCondition = SPCSEQ_ENDLOOPONTRIG   # stay at X until triggered
                            # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                            # toc1 = time.perf_counter()
                            # # print(toc1 - tic1)
                            # lStep = 2 * num_tweezers + 24 + counter_temp_AXA_loop*4
                            # llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter) + 2)  # sweep X to A
                            # llLoop = 1
                            # llNext = 2 * num_tweezers + 25 + counter_temp_AXA_loop*4
                            # llCondition =  SPCSEQ_ENDLOOPALWAYS # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                            # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                            #



                        # STEP 25: Return to sorting for next rearrangement cycle
                        # After AXA sequence completes, this step holds the drop waveform and waits for trigger
                        # Then transitions to step 1 (first sorting step) to begin another rearrangement cycle
                        # This creates the loop: sort -> drop -> AXA -> sort -> drop -> AXA -> ... (until final loop)
                        lStep = 2 * num_tweezers + 25 + counter_temp_AXA_loop*4
                        llSegment = 2 * num_tweezers - 1 + self.drop_counter + 1  # the drop waveform (held during wait)
                        llLoop = 1
                        llNext = 1  # go to the first sorting step (step 1) to start next rearrangement cycle
                        llCondition = SPCSEQ_ENDLOOPONTRIG  # wait for external trigger before starting next cycle
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        # if self.loop_counter==(self.loop_num): # stop the loop
                        #     print('Final rearrangement')
                        #     lStep = 2 * num_tweezers + 25
                        #     llSegment = 2 * num_tweezers - 1 + self.drop_counter + 1  # the drop waveform
                        #     llLoop = 1
                        #     llNext = 0 # go back to static on trigger
                        #     llCondition = SPCSEQ_ENDLOOPONTRIG
                        #     llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        #     spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                        # else:
                        #     print('Continuing to next rearrangement')
                        #     lStep = 2 * num_tweezers + 25
                        #     llSegment = 2 * num_tweezers - 1 + self.drop_counter + 1 # the drop waveform
                        #     llLoop = 1
                        #     llNext = 1 # go to the first sorting step
                        #     # llNext = 2 * num_tweezers + 22  # go to AXA
                        #     llCondition = SPCSEQ_ENDLOOPONTRIG
                        #     llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        #     spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    if multi_trig == True and hold_drop and not multi_loop:
                        lStep = 2 * num_tweezers + 100
                        # llSegment = 2 * num_tweezers - 1 + self.drop_counter + 1 # the drop waveform
                        llSegment = 2 * num_tweezers - 1 + 0 # the first drop waveform
                        llLoop = 1
                        llNext = 2 * num_tweezers + 22
                        llCondition = SPCSEQ_ENDLOOPONTRIG  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        # print(f'{loop_num + 3}th trig')
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = 2 * num_tweezers + 22
                        llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter))  # 2 * num_tweezers  # sweep to 5.5lambda shifted by Lo4
                        llLoop = 1
                        llNext = 2 * num_tweezers + 23
                        llCondition = SPCSEQ_ENDLOOPALWAYS  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = 2 * num_tweezers + 23
                        llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter) + 1)  # 2 * num_tweezers + 1  # 5.5lambda shifted by Lo4
                        llLoop = 1
                        llNext = 2 * num_tweezers + 24  # 0 # 2 * num_tweezers + 100  # next step is 0
                        llCondition = SPCSEQ_ENDLOOPONTRIG  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                        toc1 = time.perf_counter()
                        # print(toc1 - tic1)
                        lStep = 2 * num_tweezers + 24
                        llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter) + 2)  # 2 * num_tweezers + 2  # sweep back by Lo4
                        llLoop = 1
                        llNext = 2 * num_tweezers + 25  # 0 # 2 * num_tweezers + 100  # next step is 0
                        llCondition =  SPCSEQ_ENDLOOPALWAYS # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = 2 * num_tweezers + 25
                        # llSegment = 2 * num_tweezers - 1 + self.drop_counter # the drop waveform
                        llSegment = 2 * num_tweezers - 1 + 0 # the first drop waveform
                        llLoop = 1
                        llNext = 0
                        llCondition = SPCSEQ_ENDLOOPONTRIG
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                        print("does this get reached?")

                    elif multi_trig == True and not hold_drop and not multi_loop:
                        lStep = 2 * num_tweezers + 100
                        llSegment = 2 * num_tweezers - 2  # the static waveform
                        llLoop = 1
                        llNext = 2 * num_tweezers + 22
                        llCondition = SPCSEQ_ENDLOOPONTRIG  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        # print(f'{loop_num + 3}th trig')
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = 2 * num_tweezers + 22
                        llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter))  # 2 * num_tweezers  # sweep to 5.5lambda shifted by Lo4
                        llLoop = 1
                        llNext = 2 * num_tweezers + 23
                        llCondition = SPCSEQ_ENDLOOPALWAYS  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = 2 * num_tweezers + 23
                        llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter) + 1)  # 2 * num_tweezers + 1  # 5.5lambda shifted by Lo4
                        llLoop = 1
                        llNext = 2 * num_tweezers + 24  # 0 # 2 * num_tweezers + 100  # next step is 0
                        llCondition = SPCSEQ_ENDLOOPONTRIG  # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                        toc1 = time.perf_counter()
                        # print(toc1 - tic1)
                        lStep = 2 * num_tweezers + 24
                        llSegment = int(len(wf_list) - 3*(self.AXA_num-self.AXA_counter) + 2)  # 2 * num_tweezers + 2  # sweep back by Lo4
                        llLoop = 1
                        llNext = 2 * num_tweezers + 25  # 0 # 2 * num_tweezers + 100  # next step is 0
                        llCondition =  SPCSEQ_ENDLOOPALWAYS # SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        # lStep = 2 * num_tweezers + 25
                        # llSegment = int(len(wf_list) - 2)  # 2 * num_tweezers + 3  # static 5.5lambda (not shifted)
                        # llLoop = 1
                        # llNext = 2 * num_tweezers + 26
                        # llCondition = SPCSEQ_ENDLOOPONTRIG  # unconditionally leave current step
                        # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                        #
                        # lStep = 2 * num_tweezers + 26
                        # llSegment = int(len(wf_list) - 1)  # 2 * num_tweezers + 4  # sweep to 5lambda spacing
                        # llLoop = 1
                        # llNext = 2 * num_tweezers + 27
                        # llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        lStep = 2 * num_tweezers + 25
                        llSegment = 2 * num_tweezers - 2  # static
                        llLoop = 1
                        llNext = 0
                        llCondition = SPCSEQ_ENDLOOPONTRIG
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    else:
                        lStep = 2 * num_tweezers + 100

                        if hold_drop:
                            # llSegment = 2 * num_tweezers - 1 + self.drop_counter # the drop waveform
                            llSegment = 2 * num_tweezers - 1 + 0 # the first drop waveform
                            llLoop = 1
                            llNext = 0
                            llCondition = SPCSEQ_ENDLOOPONTRIG  # unconditionally leave current step
                            # print(f'{loop_num + 3}th trig')
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                        else:
                            llSegment = 2 * num_tweezers - 2  # the static waveform
                            llLoop = 1
                            llNext = 0
                            llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                            # print(f'{loop_num + 3}th trig')
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                else:
                    print('no atoms!')
                    lStep = 1  # current step is step 1

                    llSegment = 2*num_tweezers-1 + self.drop_counter + 1 #2*num_tweezers - 2   # drop
                    # llLoop = int(25*4003200/wf_list[-1].SampleLength)  # pattern repeated once
                    llLoop = int(5 * 0.001 * SAMP_FREQ / wf_list[llSegment].SampleLength)  # pattern repeated once
                    llNext = 0  # go back to step 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                # toc = time.perf_counter()
                print(f'Cycle {self.i_counter:0.0f} of {self.Cycle_num:0.0f}')
                self.current_time = time.time()
                print("********************************")

                # date_dir_log = datetime.datetime.now().strftime("%Y\%m\%d")
                # DIR_DATA_log = Path('X:/', 'expdata-e6', 'data', date_dir_log, "run_test")
                # if not os.path.exists(DIR_DATA_log):
                #     os.makedirs(DIR_DATA_log)
                ################Write in logger file#######################
                # log_file_path = Path(DIR_DATA_log, "wavegen_log.txt")
                # current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # log_entry = f"{current_time}, Cycle {self.drop_counter:0.0f} of {self.drop_num:0.0f} in drop, " \
                #             f"Cycle {self.AXA_counter:0.0f} of {self.AXA_num:0.0f} in AXA \n"
                # with open(log_file_path, 'a') as log_file:
                #     log_file.write(log_entry)
                ##########################################################

                print(f'Cycle {self.drop_counter:0.0f} of {self.drop_num:0.0f} in drop waveforms')
                print(f'Cycle {self.AXA_counter:0.0f} of {self.AXA_num:0.0f} in AXA waveforms')
                print(f'Rearrangement loop {self.loop_counter:0.0f} of {self.loop_num:0.0f}')
                print("*******************************")
                # if (self.current_time - self.previous_time > 13):
                #     print('missed trigger!')
                #     self.i_counter = (self.i_counter + 2) % self.Cycle_num
                #     self.drop_counter = (self.drop_counter + 2) % self.drop_num
                #     # self.drop_counter = 0
                #     self.AXA_counter = (self.AXA_counter + 2) % self.AXA_num  # currently Cycle_num = AXA_num, and drop_num=1.
                # elif (self.current_time - self.previous_time < 4):
                #     print('missed trigger!')
                #     self.i_counter = (self.i_counter + 0) % self.Cycle_num
                #     self.drop_counter = (self.drop_counter + 0) % self.drop_num
                #     # self.drop_counter = 0
                #     self.AXA_counter = (self.AXA_counter + 0) % self.AXA_num  # currently Cycle_num = AXA_num, and drop_num=1.
                # else:
                self.i_counter = (self.i_counter + 1) % self.Cycle_num
                self.drop_counter = (self.drop_counter + 1) % self.drop_num
                # self.drop_counter = 0
                self.AXA_counter = (self.AXA_counter + 1) % self.AXA_num #currently Cycle_num = AXA_num, and drop_num=1.
                if multi_loop:
                    self.loop_counter = (self.loop_counter + 1) % self.loop_num

                self.previous_time = self.current_time
                self.shot_counter += 1
                print('shot', self.shot_counter)
                toc = time.perf_counter()
                print(f'analysis took {toc - self.tic:0.6f} seconds')
                print('bad_shot_list:', self.bad_shot_list)
                self.tic=toc


class TestEventHandler_1(PatternMatchingEventHandler):


    def __init__(self, drop_num,  *args, **kwargs):
        super(TestEventHandler_1, self).__init__(*args, **kwargs)
        self.drop_num = drop_num
        self.drop_counter=0
        self.last_created = None

    def on_created(self, event):

        print('\n====================================  start of a run =============================')

        # global tic_1
        tic_1 = time.perf_counter()

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
            tic_2 = time.perf_counter()
            try:
                print('tic_2-tic_1', tic_2 - tic_1)
                time_diff = tic_2 - tic_1
            except:
                time_diff = 0
            ##################################################################
            empty_list = np.array(empty_list)
            if 0 < atom_count:
                segment_queue_L = []
                segment_queue_R = []
                # now divide into left and right sides of the boundary
                mask_empty = np.diff(empty_list) > 1
                for i in range(len(mask_empty)):
                    if mask_empty[i] and empty_list[0] == 0:
                        empty_list_reduced = empty_list[i+1:]
                        break
                    else:
                        empty_list_reduced = empty_list
                for i in range(len(mask_empty)):
                    if mask_empty[-1-i] and empty_list[-1] == num_tweezers-1:
                        empty_list_reduced = empty_list_reduced[:-1-i]
                        break
                # now divide into left and right sides of the boundary
                empty_list_reduced=np.array(empty_list_reduced)
                print('empty_list_reduced:', empty_list_reduced)
                num_empty = len(empty_list)
                boundary = empty_list[int(num_empty / 2)]
                print('boundary:', boundary)
                mask_L = empty_list_reduced < boundary
                mask_R = empty_list_reduced >= boundary
                empty_list_L = empty_list_reduced[mask_L]
                empty_list_R = empty_list_reduced[mask_R]
                for i in empty_list_L:
                    if i > 0:
                        segment_queue_L.append(segment_list[i - 1])
                for i in empty_list_R:
                    if i < num_tweezers-1:
                        segment_queue_R.append(segment_list[2*(num_tweezers-1)-i-1])
                segment_queue_R = np.flip(segment_queue_R)
                print(f'segment_queue_L = {segment_queue_L}')
                print(f'segment_queue_R = {segment_queue_R}')

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
                        # llSegment = 2 * num_tweezers - 2  # the static waveform
                        llLoop = 1
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
                    llSegment = 2*num_tweezers-2 # the static waveform
                    llNext = 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                lStep = 2 * num_tweezers + 21
                llSegment = 2 * num_tweezers - 2  # the static waveform
                llLoop = 1  # pattern repeated once
                llNext = 0  # 0  # next step is 0
                llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

            else:
                lStep = 1  # current step is step 1
                llSegment = 2*num_tweezers-2 # static
                llLoop = 1  # pattern repeated once
                llNext = 0  # go back to step 0
                llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

            toc = time.perf_counter()
            # print(f'analysis 1 took {toc - tic:0.6f} seconds')


class TestEventHandler_2(PatternMatchingEventHandler):

    # i_counter=0

    def __init__(self, missed_trigger_event, *args, **kwargs):
        super(TestEventHandler_2, self).__init__(*args, **kwargs)
        self.last_created = None
        self.missed_trigger_event=missed_trigger_event

    def on_created(self, event):
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
            empty_list_new = []
            for ii in range(len(empty_list)):
                if empty_list[ii]> ii and empty_list[ii]< 40+ii-len(empty_list):
                    empty_list_new.append(empty_list[ii])
            print("*************")
            print(empty_list_new)
            print("*************")
            num_defects = np.sum((np.array(empty_list_new) < 28) & (np.array(empty_list_new) > 12))
            print(f'num_defects={num_defects}')
            if num_defects >= 8:
                self.missed_trigger_event = True
            global missed_trigger_event
            missed_trigger_event = self.missed_trigger_event
            print(f'missed_trigger_event={missed_trigger_event}')
            print('====================================  end of a run =============================')


if __name__ == '__main__':
    # REGULAR SPACING
    # spacing = 0.64
    # #FOUR LAMBDA
    # # spacing = 0.64
    # startfreq = 79.04
    # ntraps = 70 # this is the num of tweezers we want
    # ntraps_drop = 40 # tweezer num after dropping
    # # startfreq = 86.72
    # # ntraps = 46
    # # ntraps_drop = 40 # tweezer num after dropping
    # path_folder = 'four lambda spacing - 70 tweezers'
    # path_folder = 'four lambda spacing'
    # path_folder = 'waveforms_100_40Twz_5lambda_hysteresis'

    # FOUR LAMBDA, 40 tweezers
    spacing = 0.64
    startfreq = 88.64
    ntraps = 40  # this is the num of tweezers we want
    ntraps_drop = 40  # tweezer num after dropping
    path_folder = 'four lambda spacing - 70 tweezers'

    multi_trig = True #if False (True) there should be 3 (5) tweezer_RF_trigs in cicero sequence;
    multi_trig_loops = 1 # add 2 * (multi_trig_loops-1) RF trigs! This is the number of X frames per sorting loop
    dont_sort_AXA = True # set this to be True only if we don't want per-loop sorting
    hold_drop = True # True only if we want to drop several tweezer and stay at few tweezers, you will need to ramp twz intensity down in the cicero sequence at the same time
    num_loops = 7 # number of times to additionally loop the AXA sequence. num_loops=1 means we do AXA twice in the sequence.

    mol_frame_before_sort = True
    mol_frame_after_sort = False


    if num_loops>0:
        multi_loop=True
    else:
        multi_loop=False
    # AXA_list = [
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0l.h5', 'static_5,5lambda_Spock_node_Delta=0l.h5', 'sweep_from_5,5lambda_Spock_node_Delta=0l.h5']
    # ]
    # AXA_list = [['70tweezers_101.44center.h5','70tweezers_101.44center.h5','70tweezers_101.44center.h5']]
    # AXA_list = [['40tweezers_sweep_to_halfint_antinode_PG3.h5','40tweezers_101.44center_4.5L_PG3.h5','40tweezers_sweep_from_halfint_antinode_PG3.h5']]


    # AXA_list = [['40tweezers_sweep_to_halfint_antinode.h5', '40tweezers_101.44center_4.5L.h5',
    #              '40tweezers_sweep_from_halfint_antinode.h5']]
    #
    # AXA_list = [['40tweezers_sweep_to_halfint_node.h5', '40tweezers_101.44center_4.5L_node.h5',
    #              '40tweezers_sweep_from_halfint_node.h5']]


    # AXA_list = [['40tweezers_101.44center_4L_antinode.h5', '40tweezers_101.44center_4L_antinode.h5',
    #              '40tweezers_101.44center_4L_antinode.h5']]


    AXA_list = [['22_4L_antinode_HP.h5', '22_4L_antinode_HP.h5',
                 '22_4L_antinode_HP.h5']]

    # AXA_list = [['22_sweep4_to_4.5_antinode_HP.h5', '22_4.5_antinode_HP.h5',
    #              '22_sweep4.5_to_4_antinode_HP.h5']]


    # AXA_list = [['40tweezers_102.72center_4L_antinode.h5',
    #              '40tweezers_102.72center_4L_antinode.h5',
    #              '40tweezers_102.72center_4L_antinode.h5']]

    # AXA_list = [['46tweezers_101.44center_4L.h5', '46tweezers_101.44center_4L.h5',
    #              '46tweezers_101.44center_4L.h5']]


    # AXA_list = [['40tweezers_sweep_to_halfint_node.h5', '40tweezers_101.44center_4.5L_node.h5',
    #              '40tweezers_sweep_from_halfint_node.h5']]

    # AXA_list = [['70tweezers_sweep_to_halfint_node.h5', '70tweezers_101.44center_4.5L_node.h5',
    #              '70tweezers_sweep_from_halfint_node.h5']]
    # AXA_list = [['40tweezers_sweep_to_halfint_antinode.h5','40tweezers_101.44center_4.5L.h5','40tweezers_sweep_from_halfint_antinode.h5']]
    # AXA_list =[['40tweezers_101.44center_4L_PG3.h5','40tweezers_101.44center_4L_PG3.h5','40tweezers_101.44center_4L_PG3.h5']]
    # AXA_list =[['40tweezers_101.44center_4L.h5','40tweezers_101.44center_4L.h5','40tweezers_101.44center_4L.h5']]
    # AXA_list = [
    #     ['sweep_5to5,5lambda.h5', 'static_5,5lambda_antinode.h5',
    #      'sweep_5,5to5lambda.h5']
    # ]

    # 5.5 lambda node spock
    # AXA_list = [
    #     ['sweep_to_5,5lambda_Spock_node_Delta=-0.075l.h5', 'static_5,5lambda_Spock_node_Delta=-0.075l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=-0.075l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=-0.05l.h5', 'static_5,5lambda_Spock_node_Delta=-0.05l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=-0.05l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=-0.0375l.h5', 'static_5,5lambda_Spock_node_Delta=-0.0375l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=-0.0375l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=-0.025l.h5', 'static_5,5lambda_Spock_node_Delta=-0.025l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=-0.025l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=-0.0125l.h5', 'static_5,5lambda_Spock_node_Delta=-0.0125l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=-0.0125l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0l.h5', 'static_5,5lambda_Spock_node_Delta=0l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=0l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0.0125l.h5', 'static_5,5lambda_Spock_node_Delta=0.0125l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=0.0125l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0.025l.h5', 'static_5,5lambda_Spock_node_Delta=0.025l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=0.025l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0.0375l.h5', 'static_5,5lambda_Spock_node_Delta=0.0375l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=0.0375l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0.05l.h5', 'static_5,5lambda_Spock_node_Delta=0.05l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=0.05l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0.075l.h5', 'static_5,5lambda_Spock_node_Delta=0.075l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=0.075l.h5']
    #             ]

    # AXA_list = [
    #     ['sweep_to_5,5lambda_Spock_node_Delta=-0.025l.h5', 'static_5,5lambda_Spock_node_Delta=-0.025l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=-0.025l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=-0.0125l.h5', 'static_5,5lambda_Spock_node_Delta=-0.0125l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=-0.0125l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=-0.009375l.h5', 'static_5,5lambda_Spock_node_Delta=-0.009375l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=-0.009375l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=-0.00625l.h5', 'static_5,5lambda_Spock_node_Delta=-0.00625l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=-0.00625l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=-0.003125l.h5', 'static_5,5lambda_Spock_node_Delta=-0.003125l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=-0.003125l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0l.h5', 'static_5,5lambda_Spock_node_Delta=0l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=0l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0.003125l.h5', 'static_5,5lambda_Spock_node_Delta=0.003125l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=0.003125l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0.00625l.h5', 'static_5,5lambda_Spock_node_Delta=0.00625l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=0.00625l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0.009375l.h5', 'static_5,5lambda_Spock_node_Delta=0.009375l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=0.009375l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0.0125l.h5', 'static_5,5lambda_Spock_node_Delta=0.0125l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=0.0125l.h5'],
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0.025l.h5', 'static_5,5lambda_Spock_node_Delta=0.025l.h5',
    #      'sweep_from_5,5lambda_Spock_node_Delta=0.025l.h5'],
    # ]

    # AXA_list = [
    #     ['sweep_to_4,5lambda_Spock_node_Delta=0.00625l.h5', 'static_4,5lambda_Spock_node_Delta=0.00625l.h5',
    #      'sweep_from_4,5lambda_Spock_node_Delta=0.00625l.h5'],
    # ]


    # 5lambda node
    # AXA_list = [
    #     ['sweep_5lambda_shifted_Lo4.h5', 'static_5lambda_shifted_Lo4_short.h5',
    #      'sweep_5lambda_back_shifted_Lo4.h5']
    #             ]

    # AXA_list = [
    #     ['sweep_5to5,5lambda.h5', 'static_5,5lambda_antinode.h5',
    #      'sweep_5,5to5lambda.h5']
    #             ]

    # AXA_list = [
    #     ['sweep_to_5lambda_twogroup_node_Delta=-0.25l.h5', 'static_5lambda_twogroup_node_Delta=-0.25l.h5',
    #      'sweep_from_5lambda_twogroup_node_Delta=-0.25l.h5']
    #             ]

    # AXA_list = [
    #     ['sweep_to_5lambda_twogroup_node_Delta=-0.03125l.h5', 'static_5lambda_twogroup_node_Delta=-0.03125l.h5',
    #      'sweep_from_5lambda_twogroup_node_Delta=-0.03125l.h5']
    #             ]

    # AXA_list = [
    #     ['sweep_to_5lambda_twogroup_node_Delta=0l.h5', 'static_5lambda_twogroup_node_Delta=0l.h5',
    #      'sweep_from_5lambda_twogroup_node_Delta=0l.h5']
    #             ]

    # AXA_list = [
    #     ['70tweezers_101.44center.h5', '70tweezers_101.44center.h5',
    #      '70tweezers_101.44center.h5']
    #             ]

    # AXA_list = [
    #             ['sweep_to_half_shifted_Lo2_node_dualbias_Lo0.h5', 'static_half-shifted_Lo2_dualbias_Lo0.h5','sweep_from_half_shifted_Lo2_node_dualbias_Lo0.h5']
    #             ]
    # AXA_list = [
    #             ['sweep_to_half_shifted_Lo2_node_100.h5', 'static_shift_unbiased_v1.h5','sweep_from_half_shifted_Lo2_node_100.h5']
    #             ]

    # AXA_list = [
    #     ['sweep_to_half_shifted_Lo2_node_dualbias_Lo-4.h5', 'static_half-shifted_Lo2_dualbias_Lo-4.h5',
    #      'sweep_from_half_shifted_Lo2_node_dualbias_Lo-4.h5'],
    #     ['sweep_to_half_shifted_Lo2_node_dualbias_Lo-8.h5', 'static_half-shifted_Lo2_dualbias_Lo-8.h5',
    #      'sweep_from_half_shifted_Lo2_node_dualbias_Lo-8.h5'],
    #     ['sweep_to_half_shifted_Lo2_node_dualbias_Lo-16.h5', 'static_half-shifted_Lo2_dualbias_Lo-16.h5',
    #      'sweep_from_half_shifted_Lo2_node_dualbias_Lo-16.h5'],
    #     ['sweep_to_half_shifted_Lo2_node_dualbias_Lo-32.h5', 'static_half-shifted_Lo2_dualbias_Lo-32.h5',
    #      'sweep_from_half_shifted_Lo2_node_dualbias_Lo-32.h5'],
    #     ['sweep_to_half_shifted_Lo2_node_dualbias_Lo-64.h5', 'static_half-shifted_Lo2_dualbias_Lo-64.h5',
    #      'sweep_from_half_shifted_Lo2_node_dualbias_Lo-64.h5'],
    #     ['sweep_to_half_shifted_Lo2_node_dualbias_Lo0.h5', 'static_half-shifted_Lo2_dualbias_Lo0.h5',
    #      'sweep_from_half_shifted_Lo2_node_dualbias_Lo0.h5'],
    #     ['sweep_to_half_shifted_Lo2_node_dualbias_Lo64.h5', 'static_half-shifted_Lo2_dualbias_Lo64.h5',
    #      'sweep_from_half_shifted_Lo2_node_dualbias_Lo64.h5'],
    #     ['sweep_to_half_shifted_Lo2_node_dualbias_Lo32.h5', 'static_half-shifted_Lo2_dualbias_Lo32.h5',
    #      'sweep_from_half_shifted_Lo2_node_dualbias_Lo32.h5'],
    #     ['sweep_to_half_shifted_Lo2_node_dualbias_Lo16.h5', 'static_half-shifted_Lo2_dualbias_Lo16.h5',
    #      'sweep_from_half_shifted_Lo2_node_dualbias_Lo16.h5'],
    #     ['sweep_to_half_shifted_Lo2_node_dualbias_Lo8.h5', 'static_half-shifted_Lo2_dualbias_Lo8.h5',
    #      'sweep_from_half_shifted_Lo2_node_dualbias_Lo8.h5'],
    #     ['sweep_to_half_shifted_Lo2_node_dualbias_Lo4.h5', 'static_half-shifted_Lo2_dualbias_Lo4.h5',
    #      'sweep_from_half_shifted_Lo2_node_dualbias_Lo4.h5']
    # ]
    flattened_AXA_list = [item for row in AXA_list for item in row]

    # drop_list = ['drop_2_twz14,26.h5', 'drop_1_twz14.h5','drop_1_twz26.h5']
    # drop_list = ['drop_2_twz15,25_NPM_Power_Adjusted.h5']
    # drop_list = ['drop_2_twz18,22.h5']
    # drop_list = ['70tweezers_101.44center.h5','drop_8.h5','drop_10.h5','drop_12.h5','drop_14.h5','drop_16.h5','drop_18.h5']
    # drop_list=['drop_16.h5','drop_16.h5','drop_14.h5','drop_12.h5','drop_12.h5']
    # drop_list = ['70tweezers_101.44center.h5']
    # drop_list = ['drop_2_twz15,25.h5']
    # drop_list = ['drop_2_twz16,24.h5','drop_2_twz16,24.h5','drop_1_twz16.h5','drop_1_twz24.h5']
    # drop_list = ['drop_1_twz14.h5', 'drop_1_twz26.h5', 'drop_2_twz14,26.h5']
    # drop_list = ['drop_3_14,15,16.h5', 'drop_3_24,25,26.h5']
    # drop_list = ['drop_1_twz8.h5','drop_1_twz12.h5','drop_1_twz20.h5', 'drop_1_twz28.h5', 'drop_1_twz35.h5']
    # drop_list = ['drop_2_twz14,26.h5','drop_2_twz14,26.h5', 'drop_1_twz14.h5', 'drop_1_twz26.h5']
    # drop_list = ['drop_2_twz16,24.h5','drop_2_twz16,24.h5','drop_1_twz16.h5','drop_1_twz24.h5']
    # drop_list = ['drop_2_twz12,28.h5'] #, 'drop_2_twz12,28.h5', 'drop_1_twz12.h5', 'drop_1_twz28.h5']
    # drop_list = ['drop_1_twz10.h5', 'drop_1_twz30.h5']
    # drop_list = ['drop1_35.h5']
    # drop_list = ['drop_1_twz20.h5']
    # drop_list = ['70tweezers_101.44center.h5']
    # drop_list = ['40tweezers_101.44center_4L.h5','40tweezers_101.44center_4L.h5'] # length of drop_list should be num_loops+1
    # drop_list = ['drop1_10.h5', 'drop1_20.h5', 'drop1_30.h5', 'drop1_40.h5']  #<- this one is good for testing on camera
    # drop_list = ['40tweezers_101.44center_4L_antinode.h5']
                 # '40tweezers_101.44center_4L_antinode.h5, 40tweezers_101.44center_4L_antinode.h5,'
                 #  , '18tweezers_101.44center_4L.h5', '40tweezers_101.44center_4L_antinode.h5, ']
    # drop_list = ['70tweezers_101.44center.h5']
    drop_list = ['22_4L_antinode_HP.h5']
    if multi_loop:
        drop_list = [drop_list[0] for n in range(num_loops+1)]  # length of drop_list should be num_loops+1


    N_cycle = np.lcm(len(AXA_list),len(drop_list))

    # if multi_trig:
    #     # path_folder = 'waveforms_160_40Twz_5lambda_v2'
    #     path_folder = 'waveforms_160_40Twz_5lambda_susc-meas'
    #     multi_trig_list =

    # cycle_list = ['drop_20.h5'] #, 'drop_middle_10_v2.h5']
    # cycle_list = ['drop_16_v1.h5', 'drop_8_new.h5', '70tweezers_101.44center.h5']
    # cycle_list = ['drop_1_twz14.h5', 'drop_1_twz26.h5', 'drop_1_twz14.h5', 'drop_1_twz26.h5', 'drop_2_twz14,26.h5']
    # cycle_list = ['70tweezers_101.44center.h5'] #, 'drop_16_v1.h5', '70tweezers_101.44center.h5', 'drop_12.h5', '70tweezers_101.44center.h5', 'drop_8_new.h5', '70tweezers_101.44center.h5', 'drop_6.h5', 'drop_4.h5']


    # startfreq = spacing * 125
    # startfreq = 87.89 #5lambda_v1
    # startfreq = 88  # 5lambda_v2


    tweezer_freq_list = [startfreq + j * spacing for j in range(ntraps)]
    # tweezer_freq_list_drop = [101.44 + j * 0.72 for j in range(-(ntraps_drop//2), ntraps_drop//2)]
    tweezer_freq_list_drop = [101.44 + j * 0.64 for j in range(-(ntraps_drop//2), ntraps_drop//2)]
    # tweezer_freq_list_drop = [startfreq + (ntraps-ntraps_drop)/2*spacing + j * spacing for j in range(ntraps_drop)]


    print(tweezer_freq_list)

    num_tweezers = len(tweezer_freq_list)
    num_tweezers_drop = len(tweezer_freq_list_drop)
    date_dir = datetime.datetime.now().strftime("%Y\%m\%d")
    # DIR_DATA = Path('Y:/', 'expdata-e6', 'data', 'fluo_images_delete_1')
    DIR_DATA = Path('C:/', 'Users', 'CavityQED', 'Desktop', 'fluo_images_delete_1')
    DIR_DATA_2 = Path('C:/', 'Users', 'CavityQED', 'Desktop', 'fluo_images_delete_2')
    DIR_DATA_3 = Path('C:/', 'Users', 'CavityQED', 'Desktop', 'fluo_images_delete_3')
    DIR_DATA_N = Path('C:/', 'Users', 'CavityQED', 'Desktop', 'fluo_images_delete_n')  # for multi-loop

######################initialize logger file####################################
    # run_name_log = "run0"
    #
    # date_dir_log = datetime.datetime.now().strftime("%Y\%m\%d")
    # DIR_DATA_log = Path('X:/', 'expdata-e6', 'data', date_dir_log,'data', run_name_log)
    # if not os.path.exists(DIR_DATA_log):
    #     os.makedirs(DIR_DATA_log)
    # log_file_path = Path(DIR_DATA_log, "wavegen_log.txt")
    # log_entry_init = f"run name={run_name_log}\n "\
    # f"AXA_list = {AXA_list}\n"\
    # f"drop_list = {drop_list}\n"\
    # "######################################\n"
    # with open(log_file_path, 'a') as log_file:
    #     log_file.write(log_entry_init)

    #################### include sorting waveforms ########################
    # sort_list_L = [f'sweep_{num}.h5' for num in range(1, ntraps)]
    # sort_list_R = [f'sweep_{num}R.h5' for num in range(1, ntraps)]
    sort_list_L = [f'sweep40tweezers_{num}.h5' for num in range(1, ntraps_drop)]
    sort_list_R = [f'sweep40tweezers_{num}R.h5' for num in range(1, ntraps_drop)]
    # sort_list_L = ['70tweezers_101.44center.h5' for num in range(1, ntraps)]
    # sort_list_R = ['70tweezers_101.44center.h5' for num in range(1, ntraps)]
    sort_list = np.concatenate((sort_list_L, sort_list_R))

    sort_list_L_drop = [f'sweep40tweezers_{num}.h5' for num in range(1, ntraps_drop)]
    sort_list_R_drop = [f'sweep40tweezers_{num}R.h5' for num in range(1, ntraps_drop)]
    # sort_list_L = ['70tweezers_101.44center.h5' for num in range(1, ntraps)]
    # sort_list_R = ['70tweezers_101.44center.h5' for num in range(1, ntraps)]
    sort_list_drop = np.concatenate((sort_list_L_drop, sort_list_R_drop))
    # print(filename_list)
    wf_list = []

    for filename in sort_list:
        if os.access(Path(path_folder, filename), os.F_OK):  # ...retrieve the Waveforms from file.
            wav_temp=utilities.from_file(Path(path_folder, filename), 'AB')
            wf_list.append(wav_temp)
            # print("#########################")
            # print(f"filename={filename} ,  samplelength={wav_temp.SampleLength}")

    # include static waveform
    # wav_temp = utilities.from_file(Path(path_folder, '70tweezers_101.44center.h5'), 'A')
    wav_temp = utilities.from_file(Path(path_folder, '40tweezers_101.44center_4L_antinode.h5'), 'A')
    # wav_temp = utilities.from_file(Path(path_folder, '46tweezers_101.44center_4L.h5'), 'A')
    wf_list.append(wav_temp)

    # print("#########################")
    # print(f"filename=static ,  samplelength={wav_temp.SampleLength}")

    # include drop waveform
    for filename in drop_list:
        wf_list.append(utilities.from_file_simple(Path(path_folder, filename), 'A'))
    # include multi trig AXA waveforms
    for filename in flattened_AXA_list:
        wf_list.append(utilities.from_file_simple(Path(path_folder, filename), 'A'))
    # include shifted waveform
    # wf_list.append(utilities.from_file_simple(Path(path_folder, 'static_shifted_-23970.h5'), 'A'))
    # segment_list = range(num_tweezers+1)
    print(f"N_cycle={N_cycle}")
    print(f"wf_list_len={len(wf_list)}")
    segment_list = range(len(wf_list))

    wf_list_drop = wf_list.copy()
    for filename in sort_list_drop:
        if os.access(Path(path_folder, filename), os.F_OK):  # NEED TO CHANGE THIS TO THE CORRECT PATH FOR SORTING WAVEFORMS AFTER DROPPING
            wav_temp=utilities.from_file(Path(path_folder, filename), 'AB')
            wf_list_drop.append(wav_temp)
    segment_list_drop = range(len(wf_list_drop))
    print(f"wf_list_drop_len={len(wf_list_drop)}")
    print(f"wf_list_len={len(wf_list)}")


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
            # print("herehere")
            # print(wav.SampleLength)
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
    # setup_channels(amplitude=85, use_filter=False)
    setup_channels(amplitude=120, use_filter=False)
    _setup_clock()
    start_step = 0
    # step tells us which segment to loop for how many times, and what the next step is
    max_segments = len(wf_list_drop)
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
    for j in range(len(segment_list_drop)):
        pv_buf = pvAllocMemPageAligned(wf_list_drop[j].SampleLength * 2)
        pv_buf_list.append(pv_buf)
        pn_buf_list.append(cast(pv_buf, ptr16))
    for j in range(len(segment_list_drop)):
        # print("here")
        # print(j)
        # print(wf_list_drop[j].SampleLength)
        spcm_dwSetParam_i32(hCard, SPC_SEQMODE_WRITESEGMENT, segment_list_drop[j])  # set current config switch to segment j
        spcm_dwSetParam_i32(hCard, SPC_SEQMODE_SEGMENTSIZE, wf_list_drop[j].SampleLength)
        _write_segment([wf_list_drop[j]], pv_buf_list[j], pn_buf_list[j], offset=0)


########################################################################################################################
    # STEP 0: Static configuration (initial state)
    # This is the starting point of the sequence
    # Holds the static tweezer array configuration and waits for external trigger
    # After trigger, transitions to step 1 (sorting sequence)
    lStep = 0  # current step is step 0
    llSegment = 2*num_tweezers-2  # associated data memory segment is static waveform
    llLoop = 1  # pattern repeated once
    llNext = 1 # next step is step 1 (sorting sequence begins)
    llCondition = SPCSEQ_ENDLOOPONTRIG  # repeat current step until external trigger has occurred
    print('first trigger')
    # combine all parameters into one int64 bit value
    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

    lStep = 1
    llSegment = 2*num_tweezers-2
    llLoop = 1
    llNext = 0  # this is a dummy step
    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

    # print('here1')

#######################################################################################################################
    # set up watchdog
    print('watchdog')
    patterns = ["*"]
    ignore_patterns = None
    ignore_directories = False
    case_sensitive = True
    missed_trigger_event = False
    my_event_handler = TestEventHandler(N_cycle,len(drop_list), len(AXA_list), patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler_1 = TestEventHandler_1(N_cycle, patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler_2 = TestEventHandler_2(missed_trigger_event, patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler_3 = TestEventHandler_3(N_cycle, len(drop_list)-1, len(AXA_list), num_loops, patterns, ignore_patterns,ignore_directories, case_sensitive)

    print('here')


    path = DIR_DATA
    path_2 = DIR_DATA_2
    path_3 = DIR_DATA_3
    path_n = DIR_DATA_N
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path_2, recursive=go_recursively) #path_2 for 2nd sort
    my_observer.schedule(my_event_handler_3, path_n, recursive=go_recursively)  # path_n for the looping sort
    my_observer.schedule(my_event_handler_1, path, recursive=go_recursively) # for the first sort
    my_observer.schedule(my_event_handler_2, path_3, recursive=go_recursively) # for checking frame2 for missed trigger




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
        while not missed_trigger_event:
            time.sleep(1)
            # print('################################')
            # print('true')
            # print('###############################')

    except KeyboardInterrupt or missed_trigger_event:
        my_observer.stop()
        my_observer.join()
        print(f"missed_trigger_event={missed_trigger_event}")

    try:
        while True:
            time.sleep(1)
            # print('################################')
            # print('true')
            # print('###############################')

    except KeyboardInterrupt or missed_trigger_event:
        my_observer.stop()
        my_observer.join()
        print(f"missed_trigger_event={missed_trigger_event}")







