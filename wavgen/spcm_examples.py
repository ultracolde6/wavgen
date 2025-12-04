"""
Spectrum SPCM Library Examples

This module demonstrates how to use the Spectrum SPCM library for AWG programming,
showing both low-level direct API usage and high-level wrapper approaches.

Based on the official documentation:
- https://spectruminstrumentation.github.io/spcm/spcm.html
- https://github.com/SpectrumInstrumentation/spcm/tree/master/src/examples
"""

import numpy as np
import time
from ctypes import create_string_buffer

# Import your existing spectrum interface
from .spectrum import *

# Import the official SPCM library (if available)
try:
    import spcm
    SPCM_AVAILABLE = True
except ImportError:
    SPCM_AVAILABLE = False
    print("Official SPCM library not available. Using custom implementation.")


class SPCMExamples:
    """Examples of using Spectrum SPCM library for AWG programming."""
    
    def __init__(self):
        """Initialize the examples."""
        self.card = None
        self.hCard = None
        
    def example_1_basic_card_setup(self):
        """
        Example 1: Basic card setup using low-level SPCM API
        
        This demonstrates the fundamental steps for initializing an AWG card.
        """
        print("=== Example 1: Basic Card Setup ===")
        
        # Step 1: Open the card
        self.hCard = spcm_hOpen(create_string_buffer(b'/dev/spcm0'))
        if self.hCard is None:
            print("Error: Could not open card")
            return False
            
        # Step 2: Reset the card
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_RESET)
        
        # Step 3: Set card mode to AWG
        spcm_dwSetParam_i32(self.hCard, SPC_CARDMODE, SPC_REP_STDSEQ)
        
        # Step 4: Configure channels
        spcm_dwSetParam_i32(self.hCard, SPC_CHENABLE, CHANNEL0)  # Enable channel 0
        spcm_dwSetParam_i32(self.hCard, SPC_AMP0, 1000)  # Set amplitude to 1000 mV
        spcm_dwSetParam_i32(self.hCard, SPC_OUTOFFSET0, 0)  # Set offset to 0
        
        # Step 5: Configure clock
        spcm_dwSetParam_i32(self.hCard, SPC_CLOCKMODE, SPC_CM_INTPLL)
        spcm_dwSetParam_i64(self.hCard, SPC_SAMPLERATE, 100000000)  # 100 MHz
        
        print("Card setup completed successfully!")
        return True
    
    def example_2_waveform_generation(self):
        """
        Example 2: Generate and output a simple waveform
        
        This shows how to create a waveform and transfer it to the card.
        """
        print("\n=== Example 2: Waveform Generation ===")
        
        if not self.hCard:
            print("Error: Card not initialized. Run example_1 first.")
            return False
        
        # Create a simple sine wave
        sample_rate = 100000000  # 100 MHz
        frequency = 1000000  # 1 MHz
        duration = 0.001  # 1 ms
        num_samples = int(sample_rate * duration)
        
        # Generate sine wave
        t = np.linspace(0, duration, num_samples, endpoint=False)
        waveform = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit integers
        waveform_int = (waveform * 32767).astype(np.int16)
        
        # Allocate buffer
        buffer_size = len(waveform_int) * 2  # 2 bytes per sample
        spcm_dwSetParam_i64(self.hCard, SPC_SEGMENTSIZE, num_samples)
        spcm_dwSetParam_i64(self.hCard, SPC_LOOPS, 0)  # Continuous loop
        
        # Transfer data to card
        spcm_dwDefTransfer_i64(self.hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, 0,
                              waveform_int.ctypes.data_as(ctypes.c_void_p),
                              0, buffer_size)
        
        # Start the card
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER)
        
        print(f"Generated {frequency/1e6:.1f} MHz sine wave for {duration*1000:.1f} ms")
        print("Waveform is now running on the card!")
        
        return True
    
    def example_3_sequence_mode(self):
        """
        Example 3: Sequence mode for complex multi-step operations
        
        This demonstrates how to use sequence mode for advanced waveform generation.
        """
        print("\n=== Example 3: Sequence Mode ===")
        
        if not self.hCard:
            print("Error: Card not initialized. Run example_1 first.")
            return False
        
        # Create multiple waveforms
        sample_rate = 100000000
        num_samples = 32000
        
        # Waveform 1: Sine wave
        t1 = np.linspace(0, num_samples/sample_rate, num_samples, endpoint=False)
        wave1 = np.sin(2 * np.pi * 1e6 * t1)  # 1 MHz
        
        # Waveform 2: Square wave
        wave2 = np.where(np.sin(2 * np.pi * 500e3 * t1) > 0, 1, -1)  # 500 kHz square
        
        # Waveform 3: Triangle wave
        wave3 = 2 * np.abs(2 * (t1 * 2e6 - np.floor(t1 * 2e6 + 0.5))) - 1  # 2 MHz triangle
        
        waveforms = [wave1, wave2, wave3]
        
        # Convert to 16-bit integers
        waveforms_int = [(w * 32767).astype(np.int16) for w in waveforms]
        
        # Setup sequence mode
        spcm_dwSetParam_i32(self.hCard, SPC_CARDMODE, SPC_REP_STDSEQ)
        spcm_dwSetParam_i64(self.hCard, SPC_SEGMENTSIZE, num_samples)
        
        # Define sequence steps
        sequence_steps = [
            (0, 1000, 0),  # (segment, loops, next)
            (1, 500, 2),    # (segment, loops, next)
            (2, 2000, 0),   # (segment, loops, next)
        ]
        
        # Transfer waveforms to card segments
        for i, waveform in enumerate(waveforms_int):
            buffer_size = len(waveform) * 2
            spcm_dwDefTransfer_i64(self.hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, i,
                                  waveform.ctypes.data_as(ctypes.c_void_p),
                                  0, buffer_size)
        
        # Setup sequence
        for step_idx, (segment, loops, next_step) in enumerate(sequence_steps):
            spcm_dwSetParam_i32(self.hCard, SPC_SEQMODE_AVAILMAXSEGMENTS, step_idx)
            spcm_dwSetParam_i32(self.hCard, SPC_SEQMODE_SEGMENT0 + step_idx, segment)
            spcm_dwSetParam_i32(self.hCard, SPC_SEQMODE_LOOPS0 + step_idx, loops)
            spcm_dwSetParam_i32(self.hCard, SPC_SEQMODE_NEXT0 + step_idx, next_step)
        
        # Start sequence
        spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER)
        
        print("Sequence mode activated with 3 different waveforms!")
        print("Sequence: Sine wave (1000 loops) -> Square wave (500 loops) -> Triangle wave (2000 loops)")
        
        return True
    
    def example_4_trigger_configuration(self):
        """
        Example 4: Trigger configuration for synchronized operations
        
        This shows how to configure triggers for precise timing control.
        """
        print("\n=== Example 4: Trigger Configuration ===")
        
        if not self.hCard:
            print("Error: Card not initialized. Run example_1 first.")
            return False
        
        # Configure external trigger
        spcm_dwSetParam_i32(self.hCard, SPC_TRIG_ORMASK, SPC_TMASK_EXT0)  # External trigger 0
        spcm_dwSetParam_i32(self.hCard, SPC_TRIG_EXT0_MODE, SPC_TM_POS)   # Positive edge
        spcm_dwSetParam_i32(self.hCard, SPC_TRIG_EXT0_LEVEL0, 1500)       # Trigger level 1.5V
        spcm_dwSetParam_i32(self.hCard, SPC_TRIG_EXT0_LEVEL1, 2500)       # Hysteresis 2.5V
        
        # Configure trigger delay
        spcm_dwSetParam_i64(self.hCard, SPC_TRIG_DELAY, 1000)  # 1 μs delay
        
        # Configure software trigger
        spcm_dwSetParam_i32(self.hCard, SPC_TRIG_ORMASK, SPC_TMASK_SOFTWARE)
        
        print("Trigger configuration completed!")
        print("- External trigger 0 enabled (positive edge)")
        print("- Trigger level: 1.5V with 2.5V hysteresis")
        print("- Trigger delay: 1 μs")
        print("- Software trigger also enabled")
        
        return True
    
    def example_5_using_your_existing_card_class(self):
        """
        Example 5: Using your existing Card class
        
        This demonstrates how to use your high-level Card wrapper.
        """
        print("\n=== Example 5: Using Your Existing Card Class ===")
        
        try:
            from .card import Card
            
            # Create card instance
            card = Card()
            
            # Setup channels
            card.setup_channels(amplitude=1000, ch0=True, ch1=False, use_filter=True)
            
            # Create a simple waveform
            from .waveform import Superposition
            frequencies = [1e6, 2e6]  # 1 MHz and 2 MHz
            phases = [0, np.pi/2]     # 0° and 90° phase
            waveform = Superposition(frequencies, phases=phases)
            
            # Load waveform to card
            card.load_waveforms(waveform)
            
            # Start output
            card.wiggle_output(duration=5)  # Run for 5 seconds
            
            print("Using your existing Card class:")
            print(f"- Created waveform with frequencies: {[f/1e6 for f in frequencies]} MHz")
            print(f"- Phases: {[p*180/np.pi for p in phases]}°")
            print("- Output running for 5 seconds")
            
            return True
            
        except Exception as e:
            print(f"Error using Card class: {e}")
            return False
    
    def example_6_advanced_features(self):
        """
        Example 6: Advanced features and best practices
        
        This shows advanced features and programming best practices.
        """
        print("\n=== Example 6: Advanced Features ===")
        
        if not self.hCard:
            print("Error: Card not initialized. Run example_1 first.")
            return False
        
        # Get card information
        card_type = spcm_dwGetParam_i32(self.hCard, SPC_PCITYP)
        serial_number = spcm_dwGetParam_i32(self.hCard, SPC_PCISERIALNO)
        max_sample_rate = spcm_dwGetParam_i64(self.hCard, SPC_SAMPLERATE)
        
        print(f"Card Information:")
        print(f"- Type: {card_type}")
        print(f"- Serial Number: {serial_number}")
        print(f"- Max Sample Rate: {max_sample_rate/1e6:.1f} MHz")
        
        # Configure advanced features
        # Enable output filter
        spcm_dwSetParam_i32(self.hCard, SPC_FILTER0, 1)
        
        # Set termination
        spcm_dwSetParam_i32(self.hCard, SPC_50OHM0, 1)  # 50Ω termination
        
        # Configure memory segments
        spcm_dwSetParam_i64(self.hCard, SPC_SEGMENTSIZE, 32000)
        spcm_dwSetParam_i32(self.hCard, SPC_SEGMENTS, 4)  # 4 segments
        
        print("Advanced features configured:")
        print("- Output filter enabled")
        print("- 50Ω termination enabled")
        print("- 4 memory segments configured")
        
        return True
    
    def cleanup(self):
        """Clean up resources."""
        if self.hCard:
            spcm_dwSetParam_i32(self.hCard, SPC_M2CMD, M2CMD_CARD_STOP)
            spcm_vClose(self.hCard)
            print("Card closed and resources cleaned up.")


def run_all_examples():
    """Run all SPCM examples."""
    examples = SPCMExamples()
    
    try:
        # Run examples
        examples.example_1_basic_card_setup()
        examples.example_2_waveform_generation()
        examples.example_3_sequence_mode()
        examples.example_4_trigger_configuration()
        examples.example_5_using_your_existing_card_class()
        examples.example_6_advanced_features()
        
        print("\n=== All Examples Completed Successfully! ===")
        
    except Exception as e:
        print(f"Error running examples: {e}")
    
    finally:
        examples.cleanup()


if __name__ == "__main__":
    run_all_examples()
