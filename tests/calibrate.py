"""
Camera Calibration Test Script

This script provides tools for calibrating camera settings and testing camera
integration with the wavgen system. It includes exposure adjustment and
camera feedback testing for optical tweezer experiments.

The script includes:
- Camera initialization and setup
- Exposure adjustment algorithms
- Live video streaming for calibration
- Integration testing with waveform output
- Camera parameter optimization

This script is used for system setup and calibration to ensure proper camera
functionality for optical tweezer experiments.
"""

import wavgen.constants
from instrumental import instrument, u
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from wavgen.utilities import fix_exposure
from matplotlib.widgets import Button, Slider

# from .spectrum import *
from wavgen import utilities
import os
import time

if __name__ == '__main__':
    dwCard = wavgen.Card()
    myWave = wavgen.waveform.Superposition([90E6,96E6], mags=[0.5,0.5])  # Define a waveform

    dwCard.load_waveforms(myWave,mode='continuous')
    # dwCard.wiggle_output(block=False)
    dwCard.wiggle_output(block=False, cam=True)
    # cam = instrument('ChamberCam')
    # which_cam = 1
    # cam.start_live_video(framerate=10 * u.hertz, exposure_time=100*u.milliseconds)
    # if cam.wait_for_frame():
    #     im = cam.latest_frame()[390:450, 520:580]
    #     plt.imshow(im)
    #     print('hello')
    # plt.show()
    # print(cam._get_exposure())
    #
    # cam.start_live_video(framerate=10 * u.hertz)
    # cam._set_exposure(0.87 * u.milliseconds)
    # if cam.wait_for_frame():
    #     im = cam.latest_frame()[390:450, 520:580]
    #     plt.imshow(im)
    #     print('hello')
    # plt.show()
    #
    # print(cam._get_exposure())
    #
    #
    # dwCard.stabilize_intensity(dwCard.Wave, cam, which_cam)

    # dwCard._error_check()
    # dwCard.load_waveforms(myWave, mode='continuous')
    # dwCard.wiggle_output(block=False)
    # # time.sleep(2)
    # dwCard.stabilize_intensity(myWave)  # Pass it into the optimizer
