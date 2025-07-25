import sys
import time
import logging
# import watchdog
from watchdog.events import LoggingEventHandler
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from pathlib import Path
import datetime
import h5py
import numpy as np
from image_analysis import analyze_image


class TestEventHandler(PatternMatchingEventHandler):
    def __init__(self, *args, **kwargs):
        super(TestEventHandler, self).__init__(*args, **kwargs)
        self.last_created = None

    def on_created(self, event):
        path = event.src_path
        # print(f'last_created = {self.last_created}')
        if path != self.last_created:
            tic = time.perf_counter()
            print(f'{event.src_path} has been created!')
            self.last_created = path
            time.sleep(0.05)
            hf = h5py.File(f'{event.src_path}', 'r')
            print('read file')
            im_array = np.array(hf['frame-00'])
            print(analyze_image(im_array, tweezer_freq_list, num_tweezers))
            toc = time.perf_counter()
            print(f'analysis took {toc - tic:0.6f} seconds')

    def on_deleted(self, event):
        path = event.src_path
        if path == self.last_created:
            self.last_created = None


if __name__ == "__main__":
    run_name = 'run10'
    # tweezer_freq_list = [99.693, 100.307]
    tweezer_freq_list = [98, 99, 100, 101, 102]

    num_tweezers = len(tweezer_freq_list)
    date_dir = datetime.datetime.now().strftime("%Y\%m\%d")
    # print(date_dir)
    # DIR_DATA = Path('Y:/', 'expdata-e6', 'data', str(date_dir), 'data', run_name, 'High NA Imaging')  # path where the data is saved
    DIR_DATA = Path('Y:/', 'expdata-e6', 'data', 'fluo_images_delete')
    # DIR_DATA = Path('Y:/', 'expdata-e6', 'data', 'fluo_images_delete', str(date_dir), 'data', run_name, 'High NA Imaging')


    patterns = ["*"]
    ignore_patterns = None
    ignore_directories = False
    case_sensitive = True
    my_event_handler = TestEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)

    # last_created = None

    # def on_created(event):
    #     tic = time.perf_counter()
    #     print(f'{event.src_path} has been created!')
    #     # time.sleep(0.05)
    #     # hf = h5py.File(f'{event.src_path}', 'r')
    #     # print('read file')
    #     # im_array = np.array(hf['frame-00'])
    #     # print(analyze_image(im_array, tweezer_freq_list, num_tweezers))
    #     toc = time.perf_counter()
    #     print(f'analysis took {toc-tic:0.6f} seconds')

    # my_event_handler.on_created = on_created
    # path = '.'
    path = DIR_DATA
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive = go_recursively)
    my_observer.start()

    try:
        while True:
            time.sleep(1)
            # print('here')

    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()

    # logging.basicConfig(level=logging.INFO,
    #                     format='%(asctime)s - %(message)s',
    #                     datefmt='%Y-%m-%d %H:%M:%S')
    # path = sys.argv[1] if len(sys.argv) > 1 else '.'
    # event_handler = LoggingEventHandler()
    # observer = Observer()
    # observer.schedule(event_handler, path, recursive=True)
    # observer.start()
    # try:
    #     while observer.isAlive():
    #         observer.join(1)
    # finally:
    #     observer.stop()
    #     observer.join()