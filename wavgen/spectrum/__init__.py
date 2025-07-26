"""
Spectrum Hardware Interface

This module provides the Python interface to Spectrum hardware drivers for
controlling AWG (Arbitrary Waveform Generator) devices. It includes low-level
hardware communication and driver management.

The module includes:
- Hardware driver initialization and management
- Low-level communication protocols
- Error handling and status checking
- Hardware parameter configuration
- Memory management for waveform data

This module serves as the bridge between the wavgen package and the physical
Spectrum hardware, providing the necessary interfaces for waveform output.
"""

# This module contains the Spectrum hardware interface components
from .spcm_tools import *
from .pyspcm import *

