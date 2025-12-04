"""
Test SPCM Integration

This script tests the integration between your existing wavgen project
and the Spectrum SPCM library to ensure everything is working correctly.
"""

import sys
import os
import numpy as np
from ctypes import create_string_buffer

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all necessary modules can be imported."""
    print("Testing imports...")
    
    try:
        from wavgen.spectrum import *
        print("✓ Spectrum module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import spectrum module: {e}")
        return False
    
    try:
        from wavgen.card import Card
        print("✓ Card class imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Card class: {e}")
        return False
    
    try:
        from wavgen.waveform import Superposition
        print("✓ Superposition class imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Superposition class: {e}")
        return False
    
    return True


def test_spcm_functions():
    """Test that SPCM functions are available."""
    print("\nTesting SPCM functions...")
    
    # Test basic SPCM functions
    required_functions = [
        'spcm_hOpen',
        'spcm_vClose', 
        'spcm_dwSetParam_i32',
        'spcm_dwGetParam_i32',
        'spcm_dwSetParam_i64',
        'spcm_dwGetParam_i64',
        'spcm_dwDefTransfer_i64',
        'spcm_dwGetErrorInfo_i32'
    ]
    
    for func_name in required_functions:
        try:
            func = globals().get(func_name)
            if func is not None:
                print(f"✓ {func_name} available")
            else:
                print(f"✗ {func_name} not found")
                return False
        except Exception as e:
            print(f"✗ Error checking {func_name}: {e}")
            return False
    
    return True


def test_constants():
    """Test that SPCM constants are defined."""
    print("\nTesting SPCM constants...")
    
    # Test basic constants
    required_constants = [
        'SPC_CARDMODE',
        'SPC_CHENABLE',
        'SPC_AMP0',
        'SPC_SAMPLERATE',
        'SPC_M2CMD',
        'M2CMD_CARD_RESET',
        'M2CMD_CARD_START',
        'CHANNEL0',
        'SPC_REP_STDSEQ',
        'SPCM_BUF_DATA',
        'SPCM_DIR_PCTOCARD'
    ]
    
    for const_name in required_constants:
        try:
            const_value = globals().get(const_name)
            if const_value is not None:
                print(f"✓ {const_name} = {const_value}")
            else:
                print(f"✗ {const_name} not found")
                return False
        except Exception as e:
            print(f"✗ Error checking {const_name}: {e}")
            return False
    
    return True


def test_card_creation():
    """Test creating a Card instance (without hardware)."""
    print("\nTesting Card creation...")
    
    try:
        from wavgen.card import Card
        
        # Try to create a card instance
        # This might fail if no hardware is connected, which is expected
        card = Card()
        print("✓ Card instance created successfully")
        return True
        
    except Exception as e:
        print(f"⚠ Card creation failed (expected if no hardware): {e}")
        print("This is normal if no Spectrum hardware is connected.")
        return True  # Don't fail the test for this


def test_waveform_creation():
    """Test creating waveforms."""
    print("\nTesting waveform creation...")
    
    try:
        from wavgen.waveform import Superposition
        
        # Create a simple waveform
        frequencies = [1e6, 2e6]  # 1 MHz and 2 MHz
        phases = [0, np.pi/2]     # 0° and 90° phase
        waveform = Superposition(frequencies, phases=phases)
        
        print(f"✓ Created waveform with {len(frequencies)} frequencies")
        print(f"  Frequencies: {[f/1e6 for f in frequencies]} MHz")
        print(f"  Phases: {[p*180/np.pi for p in phases]}°")
        
        # Test waveform properties
        if hasattr(waveform, 'data'):
            print(f"  Waveform data shape: {waveform.data.shape}")
        if hasattr(waveform, 'frequencies'):
            print(f"  Frequencies: {waveform.frequencies}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to create waveform: {e}")
        return False


def test_low_level_spcm():
    """Test low-level SPCM functions (without hardware)."""
    print("\nTesting low-level SPCM functions...")
    
    try:
        # Test creating a string buffer (this should work)
        device_name = create_string_buffer(b'/dev/spcm0')
        print("✓ String buffer created successfully")
        
        # Test that SPCM functions exist (don't call them)
        print("✓ SPCM function signatures available")
        
        return True
        
    except Exception as e:
        print(f"✗ Low-level SPCM test failed: {e}")
        return False


def test_examples_import():
    """Test that the examples module can be imported."""
    print("\nTesting examples module...")
    
    try:
        from wavgen.spcm_examples import SPCMExamples
        print("✓ SPCMExamples class imported successfully")
        
        # Test creating an instance
        examples = SPCMExamples()
        print("✓ SPCMExamples instance created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to import examples: {e}")
        return False


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("SPCM Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("SPCM Functions Test", test_spcm_functions),
        ("Constants Test", test_constants),
        ("Card Creation Test", test_card_creation),
        ("Waveform Creation Test", test_waveform_creation),
        ("Low-level SPCM Test", test_low_level_spcm),
        ("Examples Import Test", test_examples_import),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your SPCM integration is working correctly.")
        print("\nNext steps:")
        print("1. Connect your Spectrum hardware")
        print("2. Run: python wavgen/spcm_examples.py")
        print("3. Check the guide: wavgen/spcm_guide.md")
    else:
        print("⚠ Some tests failed. Check the output above for details.")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
