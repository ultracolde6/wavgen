import wavgen.constants
from instrumental import instrument
from wavgen import utilities
import os

if __name__ == '__main__':
    dwCard = wavgen.Card()
    myWave = wavgen.waveform.Superposition([92E6,94E6])  # Define a waveform
    cam = instrument('ChamberCam')
    # dwCard.stabilize_intensity(myWave,cam=cam)  # Pass it into the optimizer
    # dwCard.load_waveforms(myWave)
    # dwCard.wiggle_output(cam=True)
    dwCard.stabilize_intensity(myWave)  # Pass it into the optimizer
