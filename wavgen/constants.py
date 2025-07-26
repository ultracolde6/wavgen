"""
Constants Module

This module defines global constants and parameters used throughout the wavgen package.
These constants control hardware limits, default values, and system configuration.

The module includes:
- Hardware limits (maximum sampling frequency, memory size, etc.)
- Default amplitudes and exposure settings
- Data processing limits (buffer sizes, plot limits)
- System configuration flags (verbose, debug modes)
- Sampling frequency and timing parameters

These constants ensure consistent behavior across the entire package and provide
centralized configuration management.
"""

### Parameters ###
NUMPY_MAX = int(2E8)   #: Max size of Software buffer for board_ transfers (in samples)
MAX_EXP = 150          #: Cap on the exposure value for ThorCam devices, `see here`_.
DEF_AMP = 210          #: Default maximum waveform output amplitude (milliVolts)
VERBOSE = True         #: Flag to de/activate operation messages throughout program.
DEBUG = False          #: Flag to de/activate debugging messages throughout program.

DATA_MAX = int(16E4)     #: Maximum number of samples to hold in array at once
PLOT_MAX = int(1E4)      #: Maximum number of data-points to plot at once
# SAMP_FREQ = int(999549000) #int(0.999*1000E6)  #: Desired Sampling Frequency
# SAMP_FREQ = int(1000129000) # 4.5lambda, spacing=0.719MHz
SAMP_FREQ = int(1E9) #int(0.999*1000E6)  #: Desired Sampling Frequency
REPEAT = 1

### Constants - DO NOT CHANGE ###
SAMP_VAL_MAX = (2 ** 15 - 1)  #: Maximum digital value of sample ~~ signed 16 bits
SAMP_FREQ_MAX = int(1250E6)   #: Maximum Sampling Frequency
MHZ = SAMP_FREQ / 1E6         #: Coverts samples/seconds to MHz
# TODO: Generalize by querying hardware every time program runs.
MEM_SIZE = 4_294_967_296  #: Size of the board_ memory (bytes)
MAX_LOOPS = 1_048_575