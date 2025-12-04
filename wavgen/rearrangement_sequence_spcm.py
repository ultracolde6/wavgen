import spcm
from spcm import units

import numpy as np

import msvcrt

import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from pathlib import Path
import datetime
import h5py
import numpy as np
from image_analysis import analyze_image
import datetime
from fractions import Fraction

USING_EXTERNAL_TRIGGER = True
SAMP_FREQ_newcode = int(1000000000) #int(1250000000) # for some reaswon the new SPCM library has max sampling at 1.25 seconds or 1.25e9 ns. 

cardvoltage = 4 # volts

def from_file(filepath, datapath):
    with h5py.File(filepath, 'r') as f:
    ## Maneuver to relevant Data location ##
        dat = f.get(datapath)
    return np.array(dat)

def kb_hit():
    """
    get the key that was pressed

    Returns
    -------
    int
        the ASCII code of the key that was pressed
    """
    return ord(msvcrt.getch()) if msvcrt.kbhit() else 0

def calculate_lcm_samplelength(frequencies, samplerate):
    """
    Calculate the least common multiple of the periods (in samples) for the given frequencies.
    Handles fractional periods accurately.

    Parameters:
        frequencies (list): List of frequencies in Hz.
        samplerate (float): Sampling rate in Hz.

    Returns:
        int: The LCM of the periods (in samples), rounded to the nearest integer.
    """
    # Calculate periods as fractions of samplerate / frequency
    # gcdfrequency = gcd(*frequencies)
    # sample_length = Fraction(samplerate / gcdfrequency).numerator
    # findmultiplier = gcd(sample_length, 32)
    # sample_length = sample_length / findmultiplier * 32
    # print(sample_length)
    # return int(sample_length)
    lcm = np.inf
    for f in frequencies:
        digits = 0
        while f % 10 == 0:
            f = f // 10
            digits += 1
        lcm = min(digits, lcm)
        """
        + 1
        """
    # print(lcm)
    # sample_length = (SAMP_FREQ / 10**lcm) * 32 * REPEAT
    gcd = np.gcd.reduce(np.array(frequencies, dtype=int))
    sample_length = 32 * Fraction(samplerate, gcd).numerator
    print(f"Sample_length={sample_length}")
    return int(sample_length)
def lcm(a, b):
    """Compute the least common multiple of a and b"""
    from math import gcd
    return abs(a * b) // gcd(a, b)

def load_waveforms(sequence : spcm.Sequence):
    print("Calculation of output data")
    sort_seg_list = []
    drop_seg_list = []
    AXA_seg_list = []
    sweep_drop_seg_list = []
    waveformvoltage = 0.5 # volts
     ### Programming the segments
    # we generate different data on all active channels !
    maxdata = 32767
    freq=80E6 # Hz, static waveform on ch1
    for i,wf in enumerate(sort_wf_list):
        seg=sequence.add_segment(len(wf)) # segment indices: [channel, sample]
        seg[0,:]=wf*(maxdata*waveformvoltage/cardvoltage)  # scale according to voltage
        seg[1,:]=np.sin(2*np.pi*freq*np.arange(len(wf))/SAMP_FREQ_newcode)*(maxdata*waveformvoltage/cardvoltage)
        sort_seg_list.append(seg) 
        sample_length_temp = calculate_lcm_samplelength([freq], SAMP_FREQ_newcode)
        lcm_temp=lcm(len(wf),sample_length_temp)
        if lcm_temp!=len(wf):
            print(f"Warning: Sorting Segment {i} length {len(wf)} is not multiple of static waveform period {sample_length_temp}, lcm={lcm_temp}")
    for i,wf in enumerate(drop_wf_list):
        drop_seg=sequence.add_segment(len(wf)) # segment indices: [channel, sample]
        drop_seg[0,:]=wf*(maxdata*waveformvoltage/cardvoltage)  # scale according to voltage
        drop_seg[1,:]=np.sin(2*np.pi*freq*np.arange(len(wf))/SAMP_FREQ_newcode)*(maxdata*waveformvoltage/cardvoltage)
        drop_seg_list.append(drop_seg) 
        sample_length_temp = calculate_lcm_samplelength([freq], SAMP_FREQ_newcode)
        lcm_temp=lcm(len(wf),sample_length_temp)
        if lcm_temp!=len(wf):
            print(f"Warning: Drop Segment {i} length {len(wf)} is not multiple of static waveform period {sample_length_temp}, lcm={lcm_temp}")
    
    wav_static = from_file(Path(path_folder, 'static.h5'), 'A')
    static_seg=sequence.add_segment(len(wav_static))
    static_seg[0,:]=wav_static*(maxdata*waveformvoltage/cardvoltage)
    static_seg[1,:]=np.sin(2*np.pi*freq*np.arange(len(wav_static))/SAMP_FREQ_newcode)*(maxdata*waveformvoltage/cardvoltage)
    
    for i,wf in enumerate(flattened_AXA_list):
        seg=sequence.add_segment(len(wf)) # segment indices: [channel, sample]
        seg[0,:]=wf*(maxdata*waveformvoltage/cardvoltage)  # scale according to voltage
        seg[1,:]=np.sin(2*np.pi*freq*np.arange(len(wf))/SAMP_FREQ_newcode)*(maxdata*waveformvoltage/cardvoltage)
        AXA_seg_list.append(seg) 
        sample_length_temp = calculate_lcm_samplelength([freq], SAMP_FREQ_newcode)
        lcm_temp=lcm(len(wf),sample_length_temp)
        if lcm_temp!=len(wf):
            print(f"Warning: AXA Segment {i} length {len(wf)} is not multiple of static waveform period {sample_length_temp}, lcm={lcm_temp}")
    
    for i,wf in enumerate(sweep_drop_wf_list):
        seg=sequence.add_segment(len(wf)) # segment indices: [channel, sample]
        seg[0,:]=wf*(maxdata*waveformvoltage/cardvoltage)  # scale according to voltage
        seg[1,:]=np.sin(2*np.pi*freq*np.arange(len(wf))/SAMP_FREQ_newcode)*(maxdata*waveformvoltage/cardvoltage)
        sweep_drop_seg_list.append(seg) 
        sample_length_temp = calculate_lcm_samplelength([freq], SAMP_FREQ_newcode)
        lcm_temp=lcm(len(wf),sample_length_temp)
        if lcm_temp!=len(wf):
            print(f"Warning: Sweep Drop Segment {i} length {len(wf)} is not multiple of static waveform period {sample_length_temp}, lcm={lcm_temp}")
    
    return sort_seg_list, drop_seg_list, AXA_seg_list, static_seg, sweep_drop_seg_list     

def setup_sequence(sequence : spcm.Sequence, segment_queue_L, segment_queue_R, drop_counter, AXA_counter, frame_idx):
    ## Programming the steps
    static_step_0=sequence.add_step(static_seg, loops=1) # static waveform step, very first step
    static_step_1=sequence.add_step(static_seg, loops=1) # static waveform step, to be used after sorting
    static_step_2=sequence.add_step(static_seg, loops=1) # static waveform step, to be used after drop
    final_static=sequence.add_step(static_seg, loops=1) # final static waveform step, to be used at the end of the sequence
    drop_step=sequence.add_step(drop_seg_list[drop_counter], loops=int(10 * 0.001 * SAMP_FREQ_newcode/len(drop_wf_list[drop_counter]))) # drop step held for 10ms
    sort_step_list=[]
    AXA_step_list=[]
    sweep_drop_step_list=[]
    if len(segment_queue_L) > 0:
        print('left sorting')
        for k in range(len(segment_queue_L) - 1):
            sort_step_list.append(sequence.add_step(sort_seg_list[segment_queue_L[k]], loops=1))
    if len(segment_queue_R) > 0:
        print('right sorting')
        for k in range(len(segment_queue_R) - 1):
            sort_step_list.append(sequence.add_step(sort_seg_list[segment_queue_R[k]], loops=1))
    for i in range(len(AXA_list[0])):  # assuming all AXA_list have the same length
        AXA_step_list.append(sequence.add_step(AXA_seg_list[AXA_counter], loops=1))
        AXA_counter += 1
    for i in range(len(sweep_droplist)):
        sweep_drop_step_list.append(sequence.add_step(sweep_drop_seg_list[i], loops=1))         
    ### Programming the transitions between the different steps

    # Configure which step is executed first
    sequence.entry_step(static_step_0)
    
    # Define the sorting transitions
    static_step_0.set_transition(sort_step_list[0], on_trig=True)
    for i in range(len(sort_step_list)-1):
        sort_step_list[i].set_transition(sort_step_list[i+1])
    
    sort_step_list[-1].set_transition(static_step_1)
    
    # Define what to do after sorting
    if frame_idx==0:
        static_step_1.set_transition(final_static) # done with first sort
        
    elif frame_idx==1: # after the second sort, move onto other parts of the sequence
        static_step_1.set_transition(drop_step)
        
        if multi_trig:
            drop_step.set_transition(static_step_2)
            static_step_2.set_transition(AXA_step_list[0], on_trig=True)
            AXA_step_list[0].set_transition(AXA_step_list[1])
            AXA_step_list[1].set_transition(AXA_step_list[2], on_trig=True)
            AXA_step_list[2].set_transition(final_static)
            final_static.set_transition(final_static)
            
        elif hold_drop:
            drop_step.set_transition(final_static, on_trig=True) # only go to final static on trigger
            
        elif hold_drop_sweep:
            drop_step.set_transition(sweep_drop_step_list[0], on_trig=True) # drop goes to sweep
            sweep_drop_step_list[0].set_transition(sweep_drop_step_list[1]) # sweep goes to static far apart tweezers
            sweep_drop_step_list[1].set_transition(final_static, on_trig=True) # static far apart tweezers goes to final static
            
        else:
            drop_step.set_transition(final_static) # no trigger
        print(f'drop_counter={drop_counter}, AXA_counter={AXA_counter}')
    
class TestEventHandler(PatternMatchingEventHandler):

    # i_counter=0

    def __init__(self, Cycle_num, drop_num, AXA_num, frame_idx, *args, **kwargs):
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
        self.frame_idx=frame_idx


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
                
                # run the sequence
                setup_sequence(sequence, segment_queue_L, segment_queue_R, self.drop_counter, self.AXA_counter, self.frame_idx)

                print(f'Cycle {self.drop_counter:0.0f} of {self.drop_num:0.0f} in drop waveforms')
                print(f'Cycle {self.AXA_counter:0.0f} of {self.AXA_num:0.0f} in AXA waveforms')
                print("*******************************")
               
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



if __name__ == '__main__':
    # REGULAR SPACING
    spacing = 0.8
    #FOUR LAMBDA
    # spacing = 0.64
    startfreq = 88
    ntraps = 40 # this is the num of tweezers we want
    path_folder = 'waveforms_80_40Twz_5lambda_susc-meas'
    # path_folder = 'four lambda spacing'
    # path_folder = 'waveforms_100_40Twz_5lambda_hysteresis'

    multi_trig = False #if False (True) there should be 3 (5) tweezer_RF_trigs in cicero sequence;
    hold_drop = False # True only if we want to drop several tweezer and stay at few tweezers, you will need to ramp twz intensity down in the cicero sequence at the same time
    hold_drop_sweep= False
    # AXA_list = [
    #     ['sweep_to_5,5lambda_Spock_node_Delta=0l.h5', 'static_5,5lambda_Spock_node_Delta=0l.h5', 'sweep_from_5,5lambda_Spock_node_Delta=0l.h5']
    # ]
    AXA_list = [['static.h5', 'static.h5', 'static.h5']]
    # AXA_list = [['50tweezers.h5','50tweezers.h5','50tweezers.h5']]
    # AXA_list = [
    #     ['sweep_5to5,5lambda.h5', 'static_5,5lambda_antinode.h5',
    #      'sweep_5,5to5lambda.h5']
    # ]
    flattened_AXA_list = [item for row in AXA_list for item in row]
    drop_list = ['static.h5']
    # drop_list = ['drop_22.h5','drop_1_twz20.h5']
    # sweep_droplist = ['sweep_to_twz10,15,20,25,30.h5', 'drop5_twz10,15,20,25,30.h5']
    sweep_droplist=['static.h5']
    N_cycle = np.lcm(len(AXA_list),len(drop_list))
    
    # cycle_list = ['drop_20.h5'] #, 'drop_middle_10_v2.h5']
    # cycle_list = ['drop_16_v1.h5', 'drop_8_new.h5', 'static.h5']
    # cycle_list = ['drop_1_twz14.h5', 'drop_1_twz26.h5', 'drop_1_twz14.h5', 'drop_1_twz26.h5', 'drop_2_twz14,26.h5']
    # cycle_list = ['static.h5'] #, 'drop_16_v1.h5', 'static.h5', 'drop_12.h5', 'static.h5', 'drop_8_new.h5', 'static.h5', 'drop_6.h5', 'drop_4.h5']



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
    sort_list = np.concatenate((sort_list_L, sort_list_R))
    print('sort list size',len(sort_list))
    print(len(drop_list),len(flattened_AXA_list))
    # print(filename_list)
    sort_wf_list = []
    drop_wf_list = []
    AXA_wf_list = []
    sweep_drop_wf_list = []

    for filename in sort_list:
        if os.access(Path(path_folder, filename), os.F_OK):  # ...retrieve the Waveforms from file.
            wav_temp=from_file(Path(path_folder, filename), 'AB')
            sort_wf_list.append(wav_temp)
            # print("#########################")
            # print(f"filename={filename} ,  samplelength={wav_temp.SampleLength}")

    # include drop waveform
    for filename in drop_list:
        drop_wf_list.append(from_file(Path(path_folder, filename), 'A'))
    # include multi trig AXA waveforms
    for filename in flattened_AXA_list:
        AXA_wf_list.append(from_file(Path(path_folder, filename), 'A'))
    for filename in sweep_droplist:
        sweep_drop_wf_list.append(from_file(Path(path_folder, filename), 'A'))
   
    print(f"N_cycle={N_cycle}")
    segment_list = range(len(sort_list))
    
    
  ################################################
    card : spcm.Card
# with spcm.Card('/dev/spcm0') as card:                         # if you want to open a specific card
# with spcm.Card('TCPIP::192.168.1.10::inst0::INSTR') as card:  # if you want to open a remote card
# with spcm.Card(serial_number=12345) as card:                  # if you want to open a card by its serial number
    with spcm.Card(card_type=spcm.SPCM_TYPE_AO, verbose=False) as card:          # if you want to open the first card of a specific type
        
        # setup card mode
        card.card_mode(spcm.SPC_REP_STD_SEQUENCE)
        
        # set up the channels
        channels = spcm.Channels(card, card_enable=spcm.CHANNEL0| spcm.CHANNEL1) # two channels enabled
        channels.enable(True)
        channels.output_load(units.highZ) # high impedance
        channels.amp(cardvoltage * units.V)
        channels.stop_level(spcm.SPCM_STOPLVL_HOLDLAST)

        # set up the mode
        sequence = spcm.Sequence(card)

        # set up trigger
        trigger = spcm.Trigger(card)
        if USING_EXTERNAL_TRIGGER:
            trigger.or_mask(spcm.SPC_TMASK_EXT0)  # external trigger
            trigger.ext0_mode(spcm.SPC_TM_POS)
            trigger.ext0_level0(0.5 * units.V)
            trigger.ext0_coupling(spcm.COUPLING_DC)
            trigger.termination(1)  # 50 Ohm termination
        else:
            trigger.or_mask(spcm.SPC_TMASK_NONE)  # none trigger (using force trigger from software)

        # Setup the clock
        clock = spcm.Clock(card)
        clock.sample_rate(100*100/125 * units.percent)  # percent of the maximum sample rate
        clock.clock_output(False)

        # generate the data and transfer it to the card
        sort_seg_list, drop_seg_list, AXA_seg_list, static_seg, sweep_drop_seg_list = load_waveforms(sequence)
        print("... loading waveforms")

        # # Test the step setup
        # print(sequence)

        # We'll start and wait until all sequences are replayed.
        card.timeout(0) # no timeout
        print("Starting the card")
        card.start(spcm.M2CMD_CARD_ENABLETRIGGER, spcm.M2CMD_CARD_FORCETRIGGER)

        print(" key: ESC ... stop replay and end program")

        card_status = 0
        sequence_status_old = 0
        sequence_status = 0
        
         ################################
        # set up watchdog
        print('watchdog')
        patterns = ["*"]
        ignore_patterns = None
        ignore_directories = False
        case_sensitive = True
        missed_trigger_event = False
        
        
        path = DIR_DATA
        path_2 = DIR_DATA_2
        path_3 = DIR_DATA_3
        go_recursively = True
        my_observer = Observer()
        
        my_event_handler = TestEventHandler(N_cycle,len(drop_list), len(AXA_list), 0, patterns, ignore_patterns, ignore_directories, case_sensitive) # frame_idx=0
        my_event_handler_1 = TestEventHandler(N_cycle,len(drop_list), len(AXA_list), 1, patterns, ignore_patterns, ignore_directories, case_sensitive) # frame_idx=1
        
        my_observer.schedule(my_event_handler, path, recursive=go_recursively) # for the first sort
        my_observer.schedule(my_event_handler_1, path_2, recursive=go_recursively) # path2 for the second sort
        
        

        print('here')

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

        while True:
            key = kb_hit()
            if key == 27:  # ESC
                card.stop()
                break

            # end loop if card reports "ready" state, meaning that it has reached the end of the sequence
            if not card.is_demo_card():
                card_status = card.status()
                if (card_status & spcm.M2STAT_CARD_READY) != 0:
                    break
            
        print("... Finished the sequence and stopping the card")
    
    
