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

# Original watchdog class
# class TestEventHandler(PatternMatchingEventHandler):
#     def __init__(self, *args, **kwargs):
#         super(TestEventHandler, self).__init__(*args, **kwargs)
#         self.last_created = None
#
#     def on_created(self, event):
#         path = event.src_path
#         if path != self.last_created:
#             self.last_created = path
#             tic = time.perf_counter()
#             print(f'{event.src_path} has been created!')
#             time.sleep(0.1)
#             try:
#                 hf = h5py.File(f'{event.src_path} ', 'r')
#             except:
#                 time.sleep(0.1)
#                 hf = h5py.File(f'{event.src_path} ', 'r')
#                 print('exception')
#             print('read file')
#             im_array = np.array(hf['frame-00'])
#             hf.close()
#             atom_count, empty_list = analyze_image(im_array, tweezer_freq_list, num_tweezers)
#             print(atom_count, empty_list)
#
#             if 0 < atom_count:
#                 segment_queue = []
#                 for i in range(len(empty_list)):
#                     if empty_list[i] > 0:
#                         segment_queue.append(segment_list[empty_list[i] - 1])
#                 if len(segment_queue) > 0:
#                     for k in range(len(segment_queue) - 1):
#                         lStep = k + 1  # current step is step k+1 (+1 because step0 is the static config)
#                         llSegment = segment_queue[k]  # associated data memory segment
#                         llLoop = 1  # pattern repeated once
#                         llNext = k + 2  # next step is the next sweep
#                         llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
#                         llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
#                         spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
#
#                         # lStep = k + 1  # current step is step k+1 (+1 because step0 is the static config)
#                         # llSegment = segment_queue[k]  # associated data memory segment
#                         # llLoop = 1  # pattern repeated once
#                         # llNext = 10 + k  # next step is {0,1,2,3,4} config (10 chosen randomly)
#                         # llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
#                         # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
#                         # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
#                         # # print(f'step {k} configured')
#                         #
#                         # lStep = 10 + k
#                         # llSegment = num_tweezers-1  # {0,1,2,3,4} config to reinitialize for next arrangement
#                         # llLoop = 1
#                         # llNext = k + 2  # next step is the next sweep
#                         # llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
#                         # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
#                         # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
#
#                     lStep = len(segment_queue)  # current step is the last one in segment_queue
#                     llSegment = segment_queue[-1]  # associated data memory segment
#                     llLoop = 1  # pattern repeated once
#                     llNext = 20  # next step is 20
#                     llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
#                     llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
#                     spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
#
#                     lStep = 20  # 20 chosen randomly
#                     llSegment = num_tweezers  # the drop waveform
#                     llLoop = 1  # pattern repeated
#                     llNext = 0  # next step is 0
#                     llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
#                     llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
#                     spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
#
#                 else:
#                     lStep = 1  # 20 chosen randomly
#                     llSegment = num_tweezers  # the drop waveform
#                     llLoop = 1  # pattern repeated once
#                     llNext = 0  # next step is 0
#                     llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
#                     llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
#                     spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
#
#                     # lStep = 1  # current step is step 1
#                     # llSegment = num_tweezers-1  # associated data memory segment
#                     # llLoop = 1  # pattern repeated once
#                     # llNext = 20  # go back to step 0
#                     # llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
#                     # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
#                     # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
#                     #
#                     # lStep = 20  # 20 chosen randomly
#                     # llSegment = num_tweezers  # the drop waveform
#                     # llLoop = 5  # pattern repeated once
#                     # llNext = 0  # next step is 0
#                     # llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
#                     # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
#                     # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
#
#             else:
#                 lStep = 1  # current step is step 1
#                 llSegment = num_tweezers - 1  # associated data memory segment
#                 llLoop = 1  # pattern repeated once
#                 llNext = 0  # go back to step 0
#                 llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
#                 llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
#                 spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
#
#             toc = time.perf_counter()
#             print(f'analysis took {toc - tic:0.6f} seconds')

# Zhenjie modified watchdog class, add a counter to cycle through different atom numbers
class TestEventHandler(PatternMatchingEventHandler):

    i_counter=0
    # Cycle_num=8

    def __init__(self, Cycle_num, tweezer_freq_list,  *args, **kwargs):
        super(TestEventHandler, self).__init__(*args, **kwargs)
        self.last_created = None
        self.Cycle_num = Cycle_num
        self.tweezer_freq_list = tweezer_freq_list
        self.num_tweezers = len(tweezer_freq_list)
        self.segment_list = range(self.num_tweezers + self.Cycle_num)

    def on_created(self, event):
        path = event.src_path
        if path != self.last_created:
            self.last_created = path
            tic = time.perf_counter()
            print(f'{event.src_path} has been created!')
            time.sleep(0.1)
            try:
                hf = h5py.File(f'{event.src_path} ', 'r')
            except:
                time.sleep(0.1)
                hf = h5py.File(f'{event.src_path} ', 'r')
                print('exception')
            print('read file')
            im_array = np.array(hf['frame-00'])
            hf.close()
            atom_count, empty_list = analyze_image(im_array, self.tweezer_freq_list, self.num_tweezers)
            print(atom_count, empty_list)

            if 0 < atom_count:
                segment_queue = []
                for i in range(len(empty_list)):
                    if empty_list[i] > 0:
                        segment_queue.append(self.segment_list[empty_list[i] - 1])
                if len(segment_queue) > 0:
                    for k in range(len(segment_queue) - 1):
                        lStep = k + 1  # current step is step k+1 (+1 because step0 is the static config)
                        llSegment = segment_queue[k]  # associated data memory segment
                        llLoop = 1  # pattern repeated once
                        llNext = k + 2  # next step is the next sweep
                        llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                        # lStep = k + 1  # current step is step k+1 (+1 because step0 is the static config)
                        # llSegment = segment_queue[k]  # associated data memory segment
                        # llLoop = 1  # pattern repeated once
                        # llNext = 10 + k  # next step is {0,1,2,3,4} config (10 chosen randomly)
                        # llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                        # # print(f'step {k} configured')
                        #
                        # lStep = 10 + k
                        # llSegment = num_tweezers-1  # {0,1,2,3,4} config to reinitialize for next arrangement
                        # llLoop = 1
                        # llNext = k + 2  # next step is the next sweep
                        # llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                        # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = len(segment_queue)  # current step is the last one in segment_queue
                    llSegment = segment_queue[-1]  # associated data memory segment
                    llLoop = 1  # pattern repeated once
                    llNext = 20  # next step is 20
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 20  # 20 chosen randomly
                    llSegment = self.num_tweezers + self.i_counter # the drop waveform
                    llLoop = 1  # pattern repeated
                    llNext = 0  # next step is 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                else:
                    lStep = 1  # 20 chosen randomly
                    llSegment = self.num_tweezers + self.i_counter # the drop waveform
                    llLoop = 1  # pattern repeated once
                    llNext = 0  # next step is 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))


                    # lStep = 1  # current step is step 1
                    # llSegment = num_tweezers-1  # associated data memory segment
                    # llLoop = 1  # pattern repeated once
                    # llNext = 20  # go back to step 0
                    # llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                    #
                    # lStep = 20  # 20 chosen randomly
                    # llSegment = num_tweezers  # the drop waveform
                    # llLoop = 5  # pattern repeated once
                    # llNext = 0  # next step is 0
                    # llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    # llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    # spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

            else:
                lStep = 1  # current step is step 1
                llSegment = self.num_tweezers - 1  # associated data memory segment
                llLoop = 1  # pattern repeated once
                llNext = 0  # go back to step 0
                llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

            toc = time.perf_counter()
            print(f'analysis took {toc - tic:0.6f} seconds')
            print(f'Cycle {self.i_counter:0.0f} of {self.Cycle_num:0.0f}')
            self.i_counter = (self.i_counter + 1) % self.Cycle_num
