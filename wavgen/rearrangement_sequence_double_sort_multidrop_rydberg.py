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


class SortingHelper:
    """
    Helper class for processing sorting operations in the double sort system.
    Encapsulates common sorting logic used by both event handlers.
    """
    
    def __init__(self, num_tweezers, segment_list, hCard):
        """
        Initialize the sorting helper.
        
        Parameters
        ----------
        num_tweezers : int
            Total number of tweezers
        segment_list : list
            List of segment indices mapping to waveforms
        hCard : ctypes handle
            Handle to the SPCM card
        """
        self.num_tweezers = num_tweezers
        self.segment_list = segment_list
        self.hCard = hCard
    
    def process_empty_list(self, empty_list, include_boundary_in_left=False):
        """
        Process the empty tweezer list: remove edges, find boundary, split left/right.
        
        Parameters
        ----------
        empty_list : np.array
            Array of empty tweezer indices
        include_boundary_in_left : bool
            If True, use <= for left mask (second sort). If False, use < (first sort).
            
        Returns
        -------
        tuple : (empty_list_L, empty_list_R, boundary)
            Left and right empty lists, and the boundary tweezer index
        """
        # Remove empty tweezers at edges
        mask_empty = np.diff(empty_list) > 1
        empty_list_reduced = empty_list.copy()
        
        # Remove leading edge (position 0)
        for i in range(len(mask_empty)):
            if mask_empty[i] and empty_list[0] == 0:
                empty_list_reduced = empty_list[i+1:]
                break
        
        # Remove trailing edge (position num_tweezers-1)
        for i in range(len(mask_empty)):
            if mask_empty[-1-i] and empty_list[-1] == self.num_tweezers-1:
                empty_list_reduced = empty_list_reduced[:-1-i]
                break
        
        # Sort and find boundary
        empty_list_reduced = np.sort(empty_list_reduced)
        num_empty = len(empty_list)
        boundary = empty_list[int(num_empty / 2)]
        
        # Split into left and right
        if include_boundary_in_left:
            mask_L = empty_list_reduced <= boundary
        else:
            mask_L = empty_list_reduced < boundary
        mask_R = empty_list_reduced > boundary
        
        empty_list_L = empty_list_reduced[mask_L]
        empty_list_R = empty_list_reduced[mask_R]
        
        return empty_list_L, empty_list_R, boundary
    
    def build_segment_queues(self, empty_list_L, empty_list_R):
        """
        Build segment queues for left and right sorting operations.
        
        Parameters
        ----------
        empty_list_L : np.array
            Left side empty tweezer indices
        empty_list_R : np.array
            Right side empty tweezer indices
            
        Returns
        -------
        tuple : (segment_queue_L, segment_queue_R)
            Lists of segment indices for left and right sorting
        """
        segment_queue_L = []
        segment_queue_R = []
        
        # Left side: use left-to-right sweep waveforms
        for i in empty_list_L:
            if i > 0:
                segment_queue_L.append(self.segment_list[i - 1])
        
        # Right side: use right-to-left sweep waveforms (reversed)
        for i in empty_list_R:
            if i < self.num_tweezers - 1:
                segment_queue_R.append(self.segment_list[2*(self.num_tweezers-1)-i-1])
        
        segment_queue_R = np.flip(segment_queue_R)
        
        return segment_queue_L, segment_queue_R
    
    def configure_left_sorting(self, segment_queue_L, start_step=1, next_if_no_right=None):
        """
        Configure AWG sequence steps for left-to-right sorting.
        
        Parameters
        ----------
        segment_queue_L : list
            List of segment indices for left sorting
        start_step : int
            Starting step number (default: 1)
        next_if_no_right : int, optional
            Next step if there's no right sorting to do
            
        Returns
        -------
        int : Last step number configured
        """
        if len(segment_queue_L) == 0:
            return start_step - 1
        
        print('left sorting')
        
        # Configure intermediate steps
        for k in range(len(segment_queue_L) - 1):
            lStep = start_step + k
            llSegment = segment_queue_L[k]
            llLoop = 1
            llNext = start_step + k + 1
            llCondition = SPCSEQ_ENDLOOPALWAYS
            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
            spcm_dwSetParam_i64(self.hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
        
        # Configure last step
        lStep = start_step + len(segment_queue_L) - 1
        llSegment = segment_queue_L[-1]
        llLoop = 1
        
        return lStep
    
    def configure_right_sorting(self, segment_queue_R, start_step, final_next_step):
        """
        Configure AWG sequence steps for right-to-left sorting.
        
        Parameters
        ----------
        segment_queue_R : list
            List of segment indices for right sorting
        start_step : int
            Starting step number
        final_next_step : int
            Final next step after right sorting completes
            
        Returns
        -------
        int : Last step number configured
        """
        if len(segment_queue_R) == 0:
            return start_step - 1
        
        print('right sorting')
        
        # Configure intermediate steps
        for k in range(len(segment_queue_R) - 1):
            lStep = start_step + k
            llSegment = segment_queue_R[k]
            llLoop = 1
            llNext = start_step + k + 1
            llCondition = SPCSEQ_ENDLOOPALWAYS
            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
            spcm_dwSetParam_i64(self.hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
        
        # Configure last step
        lStep = start_step + len(segment_queue_R) - 1
        llSegment = segment_queue_R[-1]
        llLoop = 1
        llNext = final_next_step
        llCondition = SPCSEQ_ENDLOOPALWAYS
        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
        spcm_dwSetParam_i64(self.hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
        
        return lStep
    
    def configure_sorting_sequence(self, empty_list_L, empty_list_R, 
                                   include_boundary_in_left=False,
                                   start_step=1,
                                   final_next_step=None,
                                   next_if_no_right=None,
                                   next_if_no_left=None):
        """
        Complete sorting sequence configuration: processes empty list and configures all steps.
        
        Parameters
        ----------
        empty_list_L : np.array
            Left side empty tweezer indices
        empty_list_R : np.array
            Right side empty tweezer indices
        include_boundary_in_left : bool
            Whether to include boundary in left side (second sort)
        start_step : int
            Starting step number
        final_next_step : int
            Final next step after sorting completes
        next_if_no_right : int, optional
            Next step if no right sorting
        next_if_no_left : int, optional
            Next step if no left sorting
            
        Returns
        -------
        dict : Configuration results with step numbers and queues
        """
        # Build segment queues
        segment_queue_L, segment_queue_R = self.build_segment_queues(empty_list_L, empty_list_R)
        
        # Configure left sorting
        if len(segment_queue_L) > 0:
            last_left_step = self.configure_left_sorting(segment_queue_L, start_step, next_if_no_right)
            
            # Set next step for last left step
            if len(segment_queue_R) > 0:
                llNext = last_left_step + 1  # Go to right sorting
            else:
                llNext = next_if_no_right if next_if_no_right else final_next_step
                if llNext == 2*self.num_tweezers + 21:
                    print('dropping')
            
            # Update last left step
            llSegment = segment_queue_L[-1]
            llLoop = 1
            llCondition = SPCSEQ_ENDLOOPALWAYS
            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
            spcm_dwSetParam_i64(self.hCard, SPC_SEQMODE_STEPMEM0 + last_left_step, int64(llValue))
            
            # Configure right sorting if needed
            if len(segment_queue_R) > 0:
                right_start = last_left_step + 1
                self.configure_right_sorting(segment_queue_R, right_start, final_next_step)
            else:
                # No right sorting, go to final step
                if next_if_no_right is None:
                    lStep = 2 * self.num_tweezers + 100
                    llSegment = 2 * self.num_tweezers - 2  # static
                    llLoop = 1
                    llNext = 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(self.hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
        
        # Only right sorting (no left)
        elif len(segment_queue_R) > 0:
            print('right sorting 2')
            self.configure_right_sorting(segment_queue_R, start_step, final_next_step)
        
        # No sorting needed
        else:
            if next_if_no_left:
                lStep = start_step
                llLoop = 1
                llSegment = 2*self.num_tweezers - 2  # static
                llNext = next_if_no_left
                llCondition = SPCSEQ_ENDLOOPALWAYS
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(self.hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
        
        return {
            'segment_queue_L': segment_queue_L,
            'segment_queue_R': segment_queue_R,
            'empty_list_L': empty_list_L,
            'empty_list_R': empty_list_R
        }


class TestEventHandler(PatternMatchingEventHandler):

    # i_counter=0

    def __init__(self, Cycle_num, drop_num, AXA_num, sorting_helper, *args, **kwargs):
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
        self.sorting_helper = sorting_helper


    def on_created(self, event):
        # global tic_1
        tic_1 = time.perf_counter()

        path = event.src_path
        print('on created')
        # Check if file was created within the last 5 minutes
        try:
            file_path = Path(path)
            file_creation_time = file_path.stat().st_ctime
            current_time = time.time()
            time_since_creation = current_time - file_creation_time
            
            # Only process files created within the last 5 minutes (300 seconds)
            if time_since_creation > 300:
                print(f'Skipping {path}: file is {time_since_creation/60:.2f} minutes old (older than 5 minutes)')
                return
        except (OSError, ValueError) as e:
            print(f'Error checking file creation time for {path}: {e}')
            return
        
        if path != self.last_created:
            self.last_created = path
            # tic = time.perf_counter()
            print(f'{event.src_path} has been created!')
            time.sleep(0.005)

            try:
                curr_time = time.perf_counter()
                # print("Current time: ", curr_time)
                time_since_trig = curr_time - tic_1
                # print("Time since trigger: ", time_since_trig)
                hf = h5py.File(f'{event.src_path} ', 'r')
            except:
                time.sleep(0.005)
                hf = h5py.File(f'{event.src_path} ', 'r')
                print('exception')
            # print('read file')
            im_array = np.array(hf['frame-00'])
            hf.close()
            atom_count, empty_list = analyze_image(im_array, tweezer_freq_list, num_tweezers)
            # print("Total atoms detected: ", atom_count)
            num_empty = len(empty_list)
            # print("Total empty tweezers detected: ", num_empty)
            print(atom_count, empty_list)

            tic_2 = time.perf_counter()
            try:
                print('Elapsed time (ms): ', np.round(1000*(tic_2-tic_1),3))
                time_diff = tic_2-tic_1
                print('before event handler')
            except:
                time_diff = 0

            if time_diff>0.8:
                print('bad shot occurred due to slow time, skipping')
                self.bad_shot_list.append(self.shot_counter+1)
                lStep = 1
                llSegment = 2 * num_tweezers - 2
                llLoop = 1
                llNext = 0  # next step is the next sweep
                llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
            else:
            ##################################################################
                print('event handler')
                if 0 < atom_count:
                    # Use helper to process empty list and build queues (second sort: include boundary in left)
                    empty_list_L, empty_list_R, boundary = self.sorting_helper.process_empty_list(
                        empty_list, include_boundary_in_left=True
                    )
                    segment_queue_L, segment_queue_R = self.sorting_helper.build_segment_queues(
                        empty_list_L, empty_list_R
                    )
                    # print(f'segment_queue_L = {segment_queue_L}')
                    # print(f'segment_queue_R = {segment_queue_R}')

                    # Configure sorting sequence using helper methods
                    if len(segment_queue_L) > 0:
                        # Left sorting exists
                        last_left_step = self.sorting_helper.configure_left_sorting(segment_queue_L, start_step=1)
                        
                        # Set next step for last left step
                        if len(segment_queue_R) > 0:
                            llNext = last_left_step + 1  # Go to right sorting
                        else:
                            print('dropping')
                            llNext = 2*num_tweezers + 21  # Go to drop
                        
                        # Update last left step
                        llSegment = segment_queue_L[-1]
                        llLoop = 1
                        llCondition = SPCSEQ_ENDLOOPALWAYS
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + last_left_step, int64(llValue))
                        
                        # Configure right sorting if needed
                        if len(segment_queue_R) > 0:
                            right_start = last_left_step + 1
                            self.sorting_helper.configure_right_sorting(segment_queue_R, right_start, 2*num_tweezers + 21)
                        else:
                            # No right sorting, go to static then drop
                            lStep = 2 * num_tweezers + 100
                            llSegment = 2 * num_tweezers - 2  # static
                            llLoop = 1
                            llNext = 0
                            llCondition = SPCSEQ_ENDLOOPALWAYS
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                    
                    elif len(segment_queue_R) > 0:
                        # Only right sorting
                        self.sorting_helper.configure_right_sorting(segment_queue_R, start_step=1, final_next_step=2*num_tweezers + 21)
                    
                    else:
                        # No sorting needed, go to drop
                        lStep = 1
                        llLoop = 1
                        llSegment = 2*num_tweezers-1 + self.drop_counter  # the drop waveform
                        llNext = 0
                        llCondition = SPCSEQ_ENDLOOPALWAYS
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                    lStep = 2 * num_tweezers + 21
                    print(f"####################{self.drop_counter}###################")
                    llSegment = 2 * num_tweezers - 1 + self.drop_counter  # the drop waveform
                    llLoop = int(5 * 0.001 * SAMP_FREQ / wf_list[llSegment].SampleLength)  # pattern repeated once
                    llNext = 2 * num_tweezers + 100  # 0  # next step is 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    tic1 = time.perf_counter()
                    # print('2nd trig')
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                    print('start of axa')

                    ##################### Start of AXA ############################
                    if multi_trig == True:
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
                            llSegment = 2 * num_tweezers - 1 + self.drop_counter # the drop waveform
                            llLoop = 1
                            llNext = 0
                            llCondition = SPCSEQ_ENDLOOPONTRIG
                            # print(f'{loop_num + 3}th trig')
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                        elif hold_drop_sweep:
                            print('hold drop sweep')
                            llSegment = 2 * num_tweezers - 1 + self.drop_counter  # the drop waveform
                            llLoop = 1
                            llNext = 2 * num_tweezers + 101
                            llCondition = SPCSEQ_ENDLOOPONTRIG
                            # print(f'{loop_num + 3}th trig')
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                            lStep=2 * num_tweezers + 101
                            llSegment = 2 * num_tweezers - 1 + len(drop_list) + len(flattened_AXA_list)   # sweep
                            llLoop = 1
                            llNext = 2 * num_tweezers + 102
                            llCondition = SPCSEQ_ENDLOOPALWAYS
                            # print(f'{loop_num + 3}th trig')
                            llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                            spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                            lStep = 2 * num_tweezers + 102
                            llSegment = 2 * num_tweezers - 1 + len(drop_list) +len(flattened_AXA_list)+1 #
                            llLoop = 1
                            llNext = 0
                            llCondition = SPCSEQ_ENDLOOPONTRIG
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
                    llLoop = int(1 * 0.001 * SAMP_FREQ / wf_list[llSegment].SampleLength)  # pattern repeated once
                    llNext = 0  # go back to step 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS  # unconditionally leave current step
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))

                # toc = time.perf_counter()
                # print(f'Cycle {self.i_counter:0.0f} of {self.Cycle_num:0.0f}')
                self.current_time = time.time()
                # print("********************************")

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

                # print(f'Cycle {self.drop_counter:0.0f} of {self.drop_num:0.0f} in drop waveforms')
                # print(f'Cycle {self.AXA_counter:0.0f} of {self.AXA_num:0.0f} in AXA waveforms')
                # print("*******************************")
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
                print(f'analysis took {toc - self.tic:0.4f} seconds')
                print('bad_shot_list:', self.bad_shot_list)
                self.tic=toc


class TestEventHandler_1(PatternMatchingEventHandler):


    def __init__(self, drop_num, sorting_helper, *args, **kwargs):
        super(TestEventHandler_1, self).__init__(*args, **kwargs)
        self.drop_num = drop_num
        self.drop_counter=0
        self.last_created = None
        self.sorting_helper = sorting_helper

    def on_created(self, event):

        print('\n====================================  start of a run =============================')

        # global tic_1
        tic_1 = time.perf_counter()

        path = event.src_path
        
        # Check if file was created within the last 5 minutes
        try:
            file_path = Path(path)
            file_creation_time = file_path.stat().st_ctime
            current_time = time.time()
            time_since_creation = current_time - file_creation_time
            
            # Only process files created within the last 5 minutes (300 seconds)
            if time_since_creation > 300:
                print(f'Skipping {path}: file is {time_since_creation/60:.2f} minutes old (older than 5 minutes)')
                return
        except (OSError, ValueError) as e:
            print(f'Error checking file creation time for {path}: {e}')
            return
        
        if path != self.last_created:
            self.last_created = path
            # tic = time.perf_counter()
            print(f'{event.src_path} has been created!')
            time.sleep(0.005)
            try:
                hf = h5py.File(f'{event.src_path} ', 'r')
            except:
                time.sleep(0.005)
                hf = h5py.File(f'{event.src_path} ', 'r')
                print('exception')
            # print('read file')
            im_array = np.array(hf['frame-00'])
            hf.close()
            atom_count, empty_list = analyze_image(im_array, tweezer_freq_list, num_tweezers)
            # print("Total atoms detected: ", atom_count)
            num_empty = len(empty_list)
            # print("Total empty tweezers detected: ", num_empty)
            print(atom_count, empty_list)
            tic_2 = time.perf_counter()
            try:
                print('Elapsed time (ms): ', np.round(1000*(tic_2 - tic_1),3))
                time_diff = tic_2 - tic_1
                print('time diff')
            except:
                time_diff = 0
            ##################################################################
            empty_list = np.array(empty_list)
            if 0 < atom_count:
                # Use helper to process empty list and build queues (first sort: exclude boundary from left)
                empty_list_L, empty_list_R, boundary = self.sorting_helper.process_empty_list(
                    empty_list, include_boundary_in_left=False
                )
                segment_queue_L, segment_queue_R = self.sorting_helper.build_segment_queues(
                    empty_list_L, empty_list_R
                )
                # print(f'segment_queue_L = {segment_queue_L}')
                # print(f'segment_queue_R = {segment_queue_R}')

                # Configure sorting sequence using helper methods (first sort)
                if len(segment_queue_L) > 0:
                    # Left sorting exists
                    last_left_step = self.sorting_helper.configure_left_sorting(segment_queue_L, start_step=1)
                    
                    # Set next step for last left step
                    if len(segment_queue_R) > 0:
                        llNext = last_left_step + 1  # Go to right sorting
                    else:
                        print('dropping')
                        llNext = 2*num_tweezers + 21  # Go to final step
                    
                    # Update last left step
                    llSegment = segment_queue_L[-1]
                    llLoop = 1
                    llCondition = SPCSEQ_ENDLOOPALWAYS
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + last_left_step, int64(llValue))
                    
                    # Configure right sorting if needed
                    if len(segment_queue_R) > 0:
                        right_start = last_left_step + 1
                        self.sorting_helper.configure_right_sorting(segment_queue_R, right_start, 2*num_tweezers + 21)
                    else:
                        # No right sorting, go to static
                        lStep = 2 * num_tweezers + 100
                        llSegment = 2 * num_tweezers - 2  # static
                        llLoop = 1
                        llNext = 0
                        llCondition = SPCSEQ_ENDLOOPALWAYS
                        llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                        spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                
                elif len(segment_queue_R) > 0:
                    # Only right sorting
                    self.sorting_helper.configure_right_sorting(segment_queue_R, start_step=1, final_next_step=2*num_tweezers + 21)
                
                else:
                    # No sorting needed, go to static
                    lStep = 1
                    llLoop = 1
                    llSegment = 2*num_tweezers-2  # static
                    llNext = 0
                    llCondition = SPCSEQ_ENDLOOPALWAYS
                    llValue = (llCondition << 32) | (llLoop << 32) | (llNext << 16) | (llSegment)
                    spcm_dwSetParam_i64(hCard, SPC_SEQMODE_STEPMEM0 + lStep, int64(llValue))
                
                # Final step always goes to static then back to step 0
                lStep = 2 * num_tweezers + 21
                llSegment = 2 * num_tweezers - 2  # static
                llLoop = 1
                llNext = 0
                llCondition = SPCSEQ_ENDLOOPALWAYS
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
        
        # Check if file was created within the last 5 minutes
        try:
            file_path = Path(path)
            file_creation_time = file_path.stat().st_ctime
            current_time = time.time()
            time_since_creation = current_time - file_creation_time
            
            # Only process files created within the last 5 minutes (300 seconds)
            if time_since_creation > 300:
                print(f'Skipping {path}: file is {time_since_creation/60:.2f} minutes old (older than 5 minutes)')
                return
        except (OSError, ValueError) as e:
            print(f'Error checking file creation time for {path}: {e}')
            return
        
        if path != self.last_created:
            self.last_created = path
            # tic = time.perf_counter()
            print(f'{event.src_path} has been created!')
            time.sleep(0.005)

            try:
                hf = h5py.File(f'{event.src_path} ', 'r')
            except:
                time.sleep(0.005)
                hf = h5py.File(f'{event.src_path} ', 'r')
                print('exception')
            # print('read file')
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
    print('running this file')
    # REGULAR SPACING
    # spacing = 0.8
    #FOUR LAMBDA
    # spacing = 0.64
    # startfreq = 88
    # ntraps = 40 # this is the num of tweezers we want
    # path_folder = 'waveforms_80_40Twz_5lambda_susc-meas'
    # path_folder = 'four lambda spacing'
    # path_folder = 'waveforms_100_40Twz_5lambda_hysteresis'

    # eight lambda
    # spacing = 1.28
    # startfreq = 88
    # ntraps = 30
    # path_folder = 'EightLambda'

    # six lambda
    # spacing = 0.96
    # startfreq = 83
    # ntraps = 40
    # path_folder = 'SixLambda-FortyTweezers'

    path_folder = 'waveforms_80_40Twz_5lambda_susc-meas'
    spacing = 0.8
    startfreq = 88
    ntraps = 40
    spacing = 0.8
    ntraps_drop = 40

    multi_trig = False #if False (True) there should be 2 (5) tweezer_RF_trigs in cicero sequence; UPDATE 1/30/25 we realized we only need 2 triggers if multi_trig=False
    hold_drop = False# True only if we want to drop several tweezer and stay at few tweezers, you will need to ramp twz intensity down in the cicero sequence at the same time
    hold_drop_sweep= False # requires 4 tweezer triggers (tweezer sweep trig)
    if hold_drop_sweep: hold_drop = False
    # AXA_list = [
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0l.h5', 'static_5,5lambda_Spock_node_Delta=0l.h5', 'sweep_from_5,5lambda_Spock_node_Delta=0l.h5']
    # ]
    AXA_list = [['static.h5', 'static.h5', 'static.h5']]
    # AXA_list = [['50tweezers.h5','50tweezers.h5','50tweezers.h5']]
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
    #     ['static.h5', 'static.h5',
    #      'static.h5']
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
    # # drop_list = ['drop_2_twz15,25_NPM_Power_Adjusted.h5']
    # drop_list = ['drop_2_twz18,22.h5','drop_1_twz18.h5','drop_1_twz22.h5']
    # drop_list = ['static.h5','drop_8.h5','drop_10.h5','drop_12.h5','drop_14.h5','drop_16.h5','drop_18.h5']
    # drop_list=['drop_16.h5','drop_16.h5','drop_14.h5','drop_12.h5','drop_12.h5']
    # drop_list = ['drop_2_twz15,25_not_phase_match.h5']
    # drop_list = ['drop2_20,25.h5']
    # drop_list = ['drop_2_twz15,25.h5']
    # drop_list = ['drop_2_twz16,24.h5','drop_2_twz16,24.h5','drop_1_twz16.h5','drop_1_twz24.h5']
    # drop_list = ['drop_1_twz14.h5', 'drop_1_twz26.h5', 'drop_2_twz14,26.h5', 'drop_2_twz14,26.h5']
    # drop_list = ['drop_3_14,15,16.h5', 'drop_3_24,25,26.h5']
    # drop_list = ['drop_1_twz8.h5','drop_1_twz12.h5','drop_1_twz20.h5', 'drop_1_twz28.h5', 'drop_1_twz35.h5']
    # drop_list = ['drop_2_twz14,26.h5','drop_2_twz14,26.h5', 'drop_1_twz14.h5', 'drop_1_twz26.h5']
    # drop_list = ['drop_2_twz16,24.h5','drop_2_twz16,24.h5','drop_1_twz16.h5','drop_1_twz24.h5']
    # drop_list = ['drop_2_twz12,28.h5'] #, 'drop_2_twz12,28.h5', 'drop_1_twz12.h5', 'drop_1_twz28.h5']
    # drop_list = ['drop_1_twz10.h5', 'drop_1_twz30.h5']
    # drop_list = ['drop5_twz18,19,20,21,22.h5'] # for mcm
    # drop_list = ['drop_1_twz16.h5']
    drop_list = ['static.h5']
    # drop_list = ['drop_22.h5','drop_1_twz20.h5']
    # sweep_droplist = ['sweep_to_twz10,15,20,25,30.h5', 'drop5_twz10,15,20,25,30.h5']
    sweep_droplist=['static.h5']
    N_cycle = np.lcm(len(AXA_list),len(drop_list))
    # static_list =

    # if multi_trig:
    #     # path_folder = 'waveforms_160_40Twz_5lambda_v2'
    #     path_folder = 'waveforms_160_40Twz_5lambda_susc-meas'
    #     multi_trig_list =

    # cycle_list = ['drop_20.h5'] #, 'drop_middle_10_v2.h5']
    # cycle_list = ['drop_16_v1.h5', 'drop_8_new.h5', 'static.h5']
    # cycle_list = ['drop_1_twz14.h5', 'drop_1_twz26.h5', 'drop_1_twz14.h5', 'drop_1_twz26.h5', 'drop_2_twz14,26.h5']
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
    DIR_DATA_2 = Path('C:/', 'Users', 'CavityQED', 'Desktop', 'fluo_images_delete_2')
    DIR_DATA_3 = Path('C:/', 'Users', 'CavityQED', 'Desktop', 'fluo_images_delete_3')

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
    sort_list_L = [f'sweep_{num}.h5' for num in range(1, ntraps)]
    sort_list_R = [f'sweep_{num}R.h5' for num in range(1, ntraps)]
    # sort_list_L = ['static.h5' for num in range(1, ntraps)]
    # sort_list_R = ['static.h5' for num in range(1, ntraps)]
    sort_list = np.concatenate((sort_list_L, sort_list_R))
    # print('buffer index:', 1+len(sort_list)+len(drop_list)+len(flattened_AXA_list)+len(sweep_droplist))
    # print('sort list size',len(sort_list))
    print(len(drop_list),len(flattened_AXA_list))
    # print(filename_list)
    wf_list = []


    for filename in sort_list:
        if os.access(Path(path_folder, filename), os.F_OK):  # ...retrieve the Waveforms from file.
            wav_temp=utilities.from_file(Path(path_folder, filename), 'AB')
            wf_list.append(wav_temp)
            # print("#########################")
            # print(f"filename={filename} ,  samplelength={wav_temp.SampleLength}")

    # include static waveform
    wav_temp = utilities.from_file(Path(path_folder, 'static.h5'), 'A')
    wf_list.append(wav_temp)

    # print("#########################")
    # print(f"filename=static ,  samplelength={wav_temp.SampleLength}")

    # include drop waveform
    for filename in drop_list:
        wf_list.append(utilities.from_file_simple(Path(path_folder, filename), 'A'))
    # include multi trig AXA waveforms
    for filename in flattened_AXA_list:
        wf_list.append(utilities.from_file_simple(Path(path_folder, filename), 'A'))
    for filename in sweep_droplist:
        wf_list.append(utilities.from_file_simple(Path(path_folder, filename), 'A'))
    # include shifted waveform
    # wf_list.append(utilities.from_file_simple(Path(path_folder, 'static_shifted_-23970.h5'), 'A'))
    # segment_list = range(num_tweezers+1)
    print(f"N_cycle={N_cycle}")
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
    setup_channels(amplitude=120, use_filter=False)
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
        # print("here")
        # print(j)
        # print(wf_list[j].SampleLength)
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

    # print('here1')

#######################################################################################################################
    # set up watchdog
    print('watchdog')
    patterns = ["*"]
    ignore_patterns = None
    ignore_directories = False
    case_sensitive = True
    missed_trigger_event = False
    
    # Create sorting helper to be shared by both event handlers
    sorting_helper = SortingHelper(num_tweezers, segment_list, hCard)
    
    my_event_handler = TestEventHandler(N_cycle, len(drop_list), len(AXA_list), sorting_helper, 
                                       patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler_1 = TestEventHandler_1(N_cycle, sorting_helper, 
                                           patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler_2 = TestEventHandler_2(missed_trigger_event, patterns, ignore_patterns, ignore_directories, case_sensitive)

    # print('here')
    print('hold drop sweep', hold_drop_sweep)


    path = DIR_DATA
    path_2 = DIR_DATA_2
    path_3 = DIR_DATA_3
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path_2, recursive=go_recursively) #path_2 for 2nd sort
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







