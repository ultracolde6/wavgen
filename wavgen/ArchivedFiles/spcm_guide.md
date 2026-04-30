# Spectrum SPCM AWG Programming Guide

This guide explains how to program Arbitrary Waveform Generators (AWG) using the Spectrum Instrumentation SPCM library, based on the official documentation and your existing project structure.

## Table of Contents

1. [Overview](#overview)
2. [Installation and Setup](#installation-and-setup)
3. [Basic Concepts](#basic-concepts)
4. [Card Control](#card-control)
5. [Waveform Generation](#waveform-generation)
6. [Sequence Mode](#sequence-mode)
7. [Trigger Configuration](#trigger-configuration)
8. [Advanced Features](#advanced-features)
9. [Your Existing Implementation](#your-existing-implementation)
10. [Best Practices](#best-practices)

## Overview

The Spectrum SPCM library provides a comprehensive interface for controlling AWG hardware. Your project already has a sophisticated implementation that wraps the low-level SPCM functions into a high-level API.

### Key Components

- **Card**: Main hardware interface
- **Channels**: Individual output channels
- **Clock**: Sample rate and timing control
- **Trigger**: Synchronization and timing
- **DataTransfer**: Buffer management
- **DDS**: Direct Digital Synthesis (if supported)

## Installation and Setup

### Prerequisites

Your project already has the necessary dependencies:
```bash
pip install numpy scipy matplotlib h5py
```

### Hardware Setup

1. Install Spectrum drivers for your operating system
2. Connect the AWG card to your computer
3. Verify the card is detected: `/dev/spcm0` (Linux) or similar

## Basic Concepts

### Card Modes

- **SPC_REP_STDSEQ**: Standard sequence mode (most common)
- **SPC_REP_STDLOOP**: Standard loop mode
- **SPC_REP_FIFO_SINGLE**: FIFO mode for real-time data

### Data Types

- **16-bit integers**: Most common for AWG output
- **32-bit integers**: Higher precision
- **Floating point**: For calculations, converted to integers for output

### Buffer Management

- **SPCM_BUF_DATA**: Main data buffer
- **SPCM_BUF_ABA**: ABA buffer (if supported)
- **SPCM_BUF_TIMESTAMP**: Timestamp buffer

## Card Control

### Opening and Initializing

```python
from ctypes import create_string_buffer
from wavgen.spectrum import *

# Open the card
hCard = spcm_hOpen(create_string_buffer(b'/dev/spcm0'))

# Reset the card
spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_RESET)

# Set card mode
spcm_dwSetParam_i32(hCard, SPC_CARDMODE, SPC_REP_STDSEQ)
```

### Channel Configuration

```python
# Enable channels
spcm_dwSetParam_i32(hCard, SPC_CHENABLE, CHANNEL0 | CHANNEL1)

# Set amplitude (in mV)
spcm_dwSetParam_i32(hCard, SPC_AMP0, 1000)  # 1V amplitude
spcm_dwSetParam_i32(hCard, SPC_AMP1, 500)   # 0.5V amplitude

# Set offset
spcm_dwSetParam_i32(hCard, SPC_OUTOFFSET0, 0)
spcm_dwSetParam_i32(hCard, SPC_OUTOFFSET1, 0)
```

### Clock Configuration

```python
# Set sample rate
spcm_dwSetParam_i64(hCard, SPC_SAMPLERATE, 100000000)  # 100 MHz

# Set clock mode
spcm_dwSetParam_i32(hCard, SPC_CLOCKMODE, SPC_CM_INTPLL)
```

## Waveform Generation

### Simple Waveform

```python
import numpy as np

# Generate sine wave
sample_rate = 100000000  # 100 MHz
frequency = 1000000      # 1 MHz
duration = 0.001         # 1 ms
num_samples = int(sample_rate * duration)

t = np.linspace(0, duration, num_samples, endpoint=False)
waveform = np.sin(2 * np.pi * frequency * t)

# Convert to 16-bit integers
waveform_int = (waveform * 32767).astype(np.int16)

# Transfer to card
buffer_size = len(waveform_int) * 2
spcm_dwSetParam_i64(hCard, SPC_SEGMENTSIZE, num_samples)
spcm_dwDefTransfer_i64(hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, 0,
                       waveform_int.ctypes.data_as(ctypes.c_void_p),
                       0, buffer_size)

# Start output
spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER)
```

### Complex Waveforms

Your existing `Superposition` class is excellent for complex waveforms:

```python
from wavgen.waveform import Superposition

# Create multi-frequency waveform
frequencies = [1e6, 2e6, 3e6]  # 1, 2, 3 MHz
phases = [0, np.pi/2, np.pi]    # 0°, 90°, 180°
waveform = Superposition(frequencies, phases=phases)

# Use with your Card class
card = Card()
card.setup_channels(amplitude=1000, ch0=True)
card.load_waveforms(waveform)
card.wiggle_output(duration=5)
```

## Sequence Mode

Sequence mode allows complex multi-step operations with different waveforms.

### Basic Sequence

```python
# Create multiple waveforms
waveforms = []
for i in range(3):
    freq = (i + 1) * 1e6  # 1, 2, 3 MHz
    t = np.linspace(0, 32000/100e6, 32000, endpoint=False)
    wave = np.sin(2 * np.pi * freq * t)
    waveforms.append((wave * 32767).astype(np.int16))

# Setup sequence mode
spcm_dwSetParam_i32(hCard, SPC_CARDMODE, SPC_REP_STDSEQ)
spcm_dwSetParam_i64(hCard, SPC_SEGMENTSIZE, 32000)

# Transfer waveforms to segments
for i, waveform in enumerate(waveforms):
    buffer_size = len(waveform) * 2
    spcm_dwDefTransfer_i64(hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, i,
                           waveform.ctypes.data_as(ctypes.c_void_p),
                           0, buffer_size)

# Define sequence steps
sequence_steps = [
    (0, 1000, 1),  # Segment 0, 1000 loops, next = 1
    (1, 500, 2),    # Segment 1, 500 loops, next = 2
    (2, 2000, 0),   # Segment 2, 2000 loops, next = 0 (loop back)
]

# Setup sequence
for step_idx, (segment, loops, next_step) in enumerate(sequence_steps):
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_AVAILMAXSEGMENTS, step_idx)
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_SEGMENT0 + step_idx, segment)
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_LOOPS0 + step_idx, loops)
    spcm_dwSetParam_i32(hCard, SPC_SEQMODE_NEXT0 + step_idx, next_step)
```

## Trigger Configuration

### External Trigger

```python
# Configure external trigger
spcm_dwSetParam_i32(hCard, SPC_TRIG_ORMASK, SPC_TMASK_EXT0)
spcm_dwSetParam_i32(hCard, SPC_TRIG_EXT0_MODE, SPC_TM_POS)   # Positive edge
spcm_dwSetParam_i32(hCard, SPC_TRIG_EXT0_LEVEL0, 1500)       # 1.5V level
spcm_dwSetParam_i32(hCard, SPC_TRIG_EXT0_LEVEL1, 2500)       # 2.5V hysteresis

# Set trigger delay
spcm_dwSetParam_i64(hCard, SPC_TRIG_DELAY, 1000)  # 1 μs delay
```

### Software Trigger

```python
# Enable software trigger
spcm_dwSetParam_i32(hCard, SPC_TRIG_ORMASK, SPC_TMASK_SOFTWARE)

# Send software trigger
spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER)
```

## Advanced Features

### Output Filtering

```python
# Enable output filter
spcm_dwSetParam_i32(hCard, SPC_FILTER0, 1)
spcm_dwSetParam_i32(hCard, SPC_FILTER1, 1)
```

### Termination

```python
# Set 50Ω termination
spcm_dwSetParam_i32(hCard, SPC_50OHM0, 1)
spcm_dwSetParam_i32(hCard, SPC_50OHM1, 1)
```

### Memory Segments

```python
# Configure multiple segments
spcm_dwSetParam_i64(hCard, SPC_SEGMENTSIZE, 32000)
spcm_dwSetParam_i32(hCard, SPC_SEGMENTS, 4)  # 4 segments
```

## Your Existing Implementation

Your project has an excellent high-level interface that wraps the SPCM functions:

### Card Class Usage

```python
from wavgen.card import Card
from wavgen.waveform import Superposition

# Create card instance
card = Card()

# Setup channels
card.setup_channels(amplitude=1000, ch0=True, ch1=False, use_filter=True)

# Create waveform
frequencies = [1e6, 2e6]
phases = [0, np.pi/2]
waveform = Superposition(frequencies, phases=phases)

# Load and run
card.load_waveforms(waveform)
card.wiggle_output(duration=5)
```

### Sequence Mode

```python
# Your existing sequence implementation
card.load_sequence(waveforms=[waveform1, waveform2, waveform3])
card.wiggle_output(duration=10)
```

### Camera Integration

Your implementation includes camera feedback for intensity stabilization:

```python
# Stabilize intensity with camera feedback
card.stabilize_intensity(waveform, cam=camera, which_cam=1)
```

## Best Practices

### Error Handling

```python
def error_check(hCard, halt=True):
    """Check for hardware errors."""
    ErrBuf = create_string_buffer(ERRORTEXTLEN)
    if spcm_dwGetErrorInfo_i32(hCard, None, None, ErrBuf) != ERR_OK:
        print(f"Error: {ErrBuf.value}")
        if halt:
            spcm_vClose(hCard)
            exit(1)
        return False
    return True
```

### Resource Management

```python
# Always clean up resources
try:
    # Your AWG code here
    pass
finally:
    spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_STOP)
    spcm_vClose(hCard)
```

### Performance Optimization

1. **Pre-allocate buffers**: Reuse buffer memory when possible
2. **Use appropriate data types**: 16-bit integers for most AWG applications
3. **Minimize data transfers**: Batch operations when possible
4. **Use sequence mode**: For complex multi-step operations

### Debugging

```python
# Get card information
card_type = spcm_dwGetParam_i32(hCard, SPC_PCITYP)
serial_number = spcm_dwGetParam_i32(hCard, SPC_PCISERIALNO)
max_sample_rate = spcm_dwGetParam_i64(hCard, SPC_SAMPLERATE)

print(f"Card Type: {card_type}")
print(f"Serial Number: {serial_number}")
print(f"Max Sample Rate: {max_sample_rate/1e6:.1f} MHz")
```

## Integration with Your Project

Your existing project structure is well-designed:

- **`wavgen/card.py`**: High-level hardware interface
- **`wavgen/waveform.py`**: Complex waveform generation
- **`wavgen/spectrum/`**: Low-level SPCM interface
- **`wavgen/utilities.py`**: Helper functions and analysis

The examples in `wavgen/spcm_examples.py` show how to use both approaches:
1. Direct SPCM API calls for low-level control
2. Your existing Card class for high-level operations

## Next Steps

1. **Run the examples**: Execute `wavgen/spcm_examples.py` to see both approaches
2. **Explore your existing code**: Your implementation already covers most use cases
3. **Check the official examples**: Visit the [GitHub repository](https://github.com/SpectrumInstrumentation/spcm/tree/master/src/examples) for more examples
4. **Consult the documentation**: The [official API docs](https://spectruminstrumentation.github.io/spcm/spcm.html) provide detailed parameter information

Your project demonstrates excellent software engineering practices with a clean separation between low-level hardware control and high-level application logic. The SPCM library integration is well-implemented and provides a solid foundation for AWG programming.
