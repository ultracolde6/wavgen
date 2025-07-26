"""
Test Script for Simulated AWG Card

This script demonstrates the simulated AWG card functionality
without requiring actual hardware connection.
"""

import time
import logging
from toggle_sequence_with_simulator import SimulatedAWGCard, EnhancedSequenceController


def test_simulated_card():
    """Test the simulated AWG card functionality."""
    print("Testing Simulated AWG Card...")
    
    # Create simulated card
    card = SimulatedAWGCard()
    
    # Test setup
    print("1. Testing card setup...")
    card.setup_channels(amplitude=100, ch0=True, ch1=False, use_filter=True)
    status = card.get_status()
    print(f"   Card status: {status}")
    
    # Test waveform loading
    print("2. Testing waveform loading...")
    dummy_waveform = type('DummyWaveform', (), {'name': 'test_waveform'})()
    card.load_waveforms(dummy_waveform)
    status = card.get_status()
    print(f"   Card status after loading: {status}")
    
    # Test output
    print("3. Testing output...")
    card.wiggle_output(duration=2)  # Run for 2 seconds
    status = card.get_status()
    print(f"   Card status after output: {status}")
    
    # Test stop
    print("4. Testing stop...")
    card.stop_output()
    status = card.get_status()
    print(f"   Card status after stop: {status}")
    
    print("Simulated card test completed successfully!")


def test_controller():
    """Test the enhanced sequence controller."""
    print("\nTesting Enhanced Sequence Controller...")
    
    # Create controller with simulation
    controller = EnhancedSequenceController(use_simulation=True)
    
    # Test status
    print("1. Testing initial status...")
    status = controller.get_status()
    print(f"   Initial status: {status}")
    
    # Test static mode
    print("2. Testing static mode...")
    try:
        controller.start_static_mode()
        time.sleep(1)
        status = controller.get_status()
        print(f"   Status after starting static mode: {status}")
    except Exception as e:
        print(f"   Error in static mode: {e}")
    
    # Test stop
    print("3. Testing stop...")
    controller.stop_current_process()
    status = controller.get_status()
    print(f"   Status after stop: {status}")
    
    print("Controller test completed!")


def main():
    """Main test function."""
    print("Starting Simulator Tests...")
    print("=" * 50)
    
    # Test simulated card
    test_simulated_card()
    
    # Test controller
    test_controller()
    
    print("\nAll tests completed!")
    print("You can now run the full controller with:")
    print("python wavgen/toggle_sequence_with_simulator.py")


if __name__ == '__main__':
    main() 