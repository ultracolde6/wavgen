# Spectrum SPCM AWG Programming

This directory contains your AWG (Arbitrary Waveform Generator) project using the Spectrum Instrumentation SPCM library.

## Quick Start

### 1. Test Your Setup

Run the integration test to verify everything is working:

```bash
python wavgen/test_spcm_integration.py
```

### 2. Run Examples

Execute the SPCM examples to see both low-level and high-level approaches:

```bash
python wavgen/spcm_examples.py
```

### 3. Use Your Existing Code

Your project already has a sophisticated AWG implementation:

```python
from wavgen.card import Card
from wavgen.waveform import Superposition

# Create card and waveform
card = Card()
frequencies = [1e6, 2e6]  # 1 MHz and 2 MHz
phases = [0, np.pi/2]     # 0° and 90° phase
waveform = Superposition(frequencies, phases=phases)

# Setup and run
card.setup_channels(amplitude=1000, ch0=True)
card.load_waveforms(waveform)
card.wiggle_output(duration=5)  # Run for 5 seconds
```

## Project Structure

- **`card.py`**: High-level hardware interface
- **`waveform.py`**: Complex waveform generation
- **`spectrum/`**: Low-level SPCM interface
- **`utilities.py`**: Helper functions and analysis
- **`spcm_examples.py`**: Examples using both approaches
- **`spcm_guide.md`**: Comprehensive programming guide
- **`test_spcm_integration.py`**: Integration test suite

## Key Features

### Your Existing Implementation

Your `Card` class provides a high-level interface:

```python
# Basic usage
card = Card()
card.setup_channels(amplitude=1000, ch0=True, ch1=False, use_filter=True)
card.load_waveforms(waveform)
card.wiggle_output(duration=5)

# Sequence mode
card.load_sequence(waveforms=[wave1, wave2, wave3])
card.wiggle_output(duration=10)

# Camera integration
card.stabilize_intensity(waveform, cam=camera, which_cam=1)
```

### Low-level SPCM API

For direct hardware control:

```python
from wavgen.spectrum import *
from ctypes import create_string_buffer

# Open card
hCard = spcm_hOpen(create_string_buffer(b'/dev/spcm0'))

# Setup
spcm_dwSetParam_i32(hCard, SPC_CARDMODE, SPC_REP_STDSEQ)
spcm_dwSetParam_i32(hCard, SPC_CHENABLE, CHANNEL0)
spcm_dwSetParam_i32(hCard, SPC_AMP0, 1000)
spcm_dwSetParam_i64(hCard, SPC_SAMPLERATE, 100000000)

# Transfer waveform data
spcm_dwDefTransfer_i64(hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, 0,
                       waveform_data.ctypes.data_as(ctypes.c_void_p),
                       0, buffer_size)

# Start output
spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER)
```

## Documentation

- **Official SPCM Documentation**: https://spectruminstrumentation.github.io/spcm/spcm.html
- **GitHub Examples**: https://github.com/SpectrumInstrumentation/spcm/tree/master/src/examples
- **Your Guide**: `spcm_guide.md` - Comprehensive programming guide

## Hardware Requirements

- Spectrum Instrumentation AWG card
- Proper drivers installed
- Card detected as `/dev/spcm0` (Linux) or similar

## Common Tasks

### Generate Simple Waveform

```python
from wavgen.card import Card
from wavgen.waveform import Superposition

card = Card()
card.setup_channels(amplitude=1000, ch0=True)

# Create 1 MHz sine wave
waveform = Superposition([1e6])
card.load_waveforms(waveform)
card.wiggle_output(duration=5)
```

### Multi-Frequency Waveform

```python
# Create complex waveform with multiple frequencies
frequencies = [1e6, 2e6, 3e6]  # 1, 2, 3 MHz
phases = [0, np.pi/2, np.pi]    # 0°, 90°, 180°
waveform = Superposition(frequencies, phases=phases)

card.load_waveforms(waveform)
card.wiggle_output(duration=10)
```

### Sequence Mode

```python
# Create multiple waveforms for sequence
wave1 = Superposition([1e6])
wave2 = Superposition([2e6])
wave3 = Superposition([3e6])

card.load_sequence(waveforms=[wave1, wave2, wave3])
card.wiggle_output(duration=15)
```

### Trigger Configuration

```python
# Configure external trigger
card.setup_channels(amplitude=1000, ch0=True)
# Your card class handles trigger setup internally
```

## Error Handling

Your implementation includes comprehensive error checking:

```python
try:
    card = Card()
    card.setup_channels(amplitude=1000, ch0=True)
    card.load_waveforms(waveform)
    card.wiggle_output(duration=5)
except Exception as e:
    print(f"Error: {e}")
    # Card will be cleaned up automatically
```

## Performance Tips

1. **Reuse Card instances**: Don't create/destroy frequently
2. **Pre-allocate waveforms**: Generate once, use many times
3. **Use sequence mode**: For complex multi-step operations
4. **Enable filters**: For cleaner output signals
5. **Check hardware limits**: Respect sample rate and memory constraints

## Troubleshooting

### Common Issues

1. **Card not found**: Check drivers and device path
2. **Import errors**: Verify all dependencies installed
3. **Memory errors**: Reduce waveform size or sample rate
4. **Timing issues**: Check trigger configuration

### Debug Information

```python
# Get card information
card_type = spcm_dwGetParam_i32(hCard, SPC_PCITYP)
serial_number = spcm_dwGetParam_i32(hCard, SPC_PCISERIALNO)
max_sample_rate = spcm_dwGetParam_i64(hCard, SPC_SAMPLERATE)

print(f"Card Type: {card_type}")
print(f"Serial Number: {serial_number}")
print(f"Max Sample Rate: {max_sample_rate/1e6:.1f} MHz")
```

## Next Steps

1. **Run the test suite**: `python wavgen/test_spcm_integration.py`
2. **Explore examples**: `python wavgen/spcm_examples.py`
3. **Read the guide**: Check `spcm_guide.md` for detailed information
4. **Connect hardware**: Test with actual Spectrum card
5. **Customize waveforms**: Use your existing `Superposition` class

Your project provides an excellent foundation for AWG programming with both high-level convenience and low-level control when needed.
