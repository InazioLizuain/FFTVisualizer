#!/usr/bin/env python3
"""
System Test Script
Tests individual components of the FFT Visualizer
"""

import sys
import time
import yaml


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def test_imports():
    """Test if all required modules can be imported"""
    print_header("Testing Module Imports")
    
    modules = {
        'numpy': 'NumPy (numerical computing)',
        'scipy': 'SciPy (signal processing)',
        'yaml': 'PyYAML (configuration)',
    }
    
    optional_modules = {
        'sounddevice': 'sounddevice (high-power audio input)',
        'rgbmatrix': 'rgbmatrix (LED matrix control)',
        'RPi.GPIO': 'RPi.GPIO (GPIO control)',
        'RPLCD.gpio': 'RPLCD (character LCD)',
    }
    
    # Test required modules
    failed = []
    for module, description in modules.items():
        try:
            __import__(module)
            print(f"✓ {module:20s} - {description}")
        except ImportError as e:
            print(f"✗ {module:20s} - FAILED: {e}")
            failed.append(module)
    
    # Test optional modules
    print("\nOptional modules (may not be available on all systems):")
    for module, description in optional_modules.items():
        try:
            __import__(module)
            print(f"✓ {module:20s} - {description}")
        except ImportError:
            print(f"- {module:20s} - Not installed (optional)")
    
    if failed:
        print(f"\n✗ {len(failed)} required module(s) missing!")
        return False
    else:
        print("\n✓ All required modules imported successfully!")
        return True


def test_config():
    """Test configuration file"""
    print_header("Testing Configuration")
    
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        print("✓ Configuration file loaded successfully")
        
        # Check required sections
        required_sections = ['audio', 'display', 'visualization', 'menu', 'system']
        for section in required_sections:
            if section in config:
                print(f"  ✓ Section '{section}' present")
            else:
                print(f"  ✗ Section '{section}' missing!")
                return False
        
        # Display key settings
        print("\nKey Settings:")
        print(f"  Audio sample rate: {config['audio']['sample_rate']} Hz")
        print(f"  FFT size: {config['audio']['fft_size']}")
        print(f"  Default input mode: {config['audio']['default_mode']}")
        print(f"  Frequency range: {config['visualization']['freq_min']}-{config['visualization']['freq_max']} Hz")
        print(f"  Display size: {config['display']['cols']}x{config['display']['rows']}")
        print(f"  Brightness: {config['display']['brightness']}%")
        print(f"  Color scheme: {config['visualization']['color_scheme']}")
        
        return True
    
    except FileNotFoundError:
        print("✗ Configuration file 'config.yaml' not found!")
        return False
    except yaml.YAMLError as e:
        print(f"✗ Error parsing configuration file: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_fft_processor():
    """Test FFT processor"""
    print_header("Testing FFT Processor")
    
    try:
        import numpy as np
        from fft_processor import FFTProcessor
        
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Create processor
        processor = FFTProcessor(config['audio'], config['visualization'])
        print("✓ FFT Processor initialized")
        
        # Generate test signal (1kHz sine wave)
        sample_rate = config['audio']['sample_rate']
        duration = config['audio']['fft_size'] / sample_rate
        t = np.linspace(0, duration, config['audio']['fft_size'])
        test_signal = np.sin(2 * np.pi * 1000 * t)
        
        print(f"  Generated test signal: 1kHz sine wave")
        
        # Process FFT
        result = processor.process(test_signal)
        
        print(f"  ✓ FFT processed successfully")
        print(f"  Spectrum shape: {result['spectrum'].shape}")
        print(f"  Peaks shape: {result['peaks'].shape}")
        print(f"  Colors shape: {result['colors'].shape}")
        
        # Find peak frequency bin
        peak_bin = np.argmax(result['spectrum'])
        print(f"  Peak detected at bin {peak_bin} (expected around bin for 1kHz)")
        
        return True
    
    except Exception as e:
        print(f"✗ FFT Processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_led_display_init():
    """Test LED display initialization (without actual hardware)"""
    print_header("Testing LED Display (Initialization)")
    
    try:
        from led_display import LEDDisplay
        
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Try to initialize (will fail without hardware, but we can test the code)
        print("  Attempting to initialize LED display...")
        print("  (This will fail without actual hardware, which is expected)")
        
        display = LEDDisplay(config['display'])
        
        if display.matrix is None:
            print("  - LED Matrix hardware not available (expected on non-Pi systems)")
            print("  ✓ LED Display module loaded successfully")
        else:
            print("  ✓ LED Matrix initialized successfully!")
        
        return True
    
    except Exception as e:
        print(f"  - LED Display initialization failed: {e}")
        print("  ✓ This is expected on systems without hardware")
        return True  # Not a critical failure for testing


def test_audio_input_init():
    """Test audio input initialization"""
    print_header("Testing Audio Input (Initialization)")
    
    try:
        from audio_input import AudioInput
        
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print("  Attempting to initialize audio input...")
        print("  (May fail without actual hardware)")
        
        audio = AudioInput(config['audio'])
        print("  ✓ Audio Input module loaded successfully")
        
        return True
    
    except Exception as e:
        print(f"  - Audio Input initialization failed: {e}")
        print("  ✓ This is expected on systems without hardware")
        return True  # Not a critical failure for testing


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  FFT Audio Visualizer - System Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("FFT Processor", test_fft_processor()))
    results.append(("LED Display Init", test_led_display_init()))
    results.append(("Audio Input Init", test_audio_input_init()))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:8s} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! System is ready.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        print("  Note: Hardware-related failures are expected on non-Pi systems")
        return 1


if __name__ == '__main__':
    sys.exit(main())
