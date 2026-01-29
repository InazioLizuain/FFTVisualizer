#!/usr/bin/env python3
"""
FFT Audio Visualizer - Main Application
Raspberry Pi 4 + Adafruit RGB Matrix HAT + 64x64 LED Matrix
Supports both low-level (10mV-1V) and high-power (40W) audio inputs
"""

import sys
import time
import signal
import logging
from typing import Optional

import yaml
import numpy as np

from audio_input import AudioInput
from fft_processor import FFTProcessor
from led_display import LEDDisplay
from menu_system import MenuSystem


class FFTVisualizer:
    """Main FFT Audio Visualizer application"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """Initialize the FFT visualizer with configuration"""
        self.running = False
        self.config = self._load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing FFT Audio Visualizer")
        
        # Initialize components
        try:
            self.audio_input = AudioInput(self.config['audio'])
            self.fft_processor = FFTProcessor(self.config['audio'], self.config['visualization'])
            self.led_display = LEDDisplay(self.config['display'])
            self.menu_system = MenuSystem(self.config['menu'], self)
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise

        # Sync FFT configuration to the selected default input mode
        self.change_input_mode(self.config['audio'].get('default_mode', 'low_level'))
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("FFT Audio Visualizer initialized successfully")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Configuration file {config_path} not found!")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing configuration file: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = logging.DEBUG if self.config['system']['debug'] else logging.INFO
        log_file = self.config['system']['log_file']
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def start(self):
        """Start the FFT visualizer"""
        self.logger.info("Starting FFT Audio Visualizer")
        self.running = True
        
        # Start audio input
        self.audio_input.start()
        
        # Start menu system in separate thread
        self.menu_system.start()
        
        # Main visualization loop
        self._run_visualization_loop()
    
    def stop(self):
        """Stop the FFT visualizer"""
        self.logger.info("Stopping FFT Audio Visualizer")
        self.running = False
        
        # Stop all components
        if hasattr(self, 'audio_input'):
            self.audio_input.stop()
        if hasattr(self, 'menu_system'):
            self.menu_system.stop()
        if hasattr(self, 'led_display'):
            self.led_display.clear()
    
    def _run_visualization_loop(self):
        """Main visualization loop - process audio and update display"""
        frame_count = 0
        fps_start_time = time.time()
        
        try:
            while self.running:
                # Get audio data from input
                audio_data = self.audio_input.get_audio_data()
                
                if audio_data is not None and len(audio_data) > 0:
                    # Process FFT
                    fft_data = self.fft_processor.process(audio_data)
                    
                    # Update LED display
                    self.led_display.update(fft_data)
                    
                    # Calculate and log FPS periodically
                    frame_count += 1
                    if frame_count % 30 == 0:
                        elapsed = time.time() - fps_start_time
                        fps = 30 / elapsed
                        self.logger.debug(f"FPS: {fps:.1f}")
                        fps_start_time = time.time()
                else:
                    # No audio data, small delay to prevent CPU spinning
                    time.sleep(0.01)
        
        except Exception as e:
            self.logger.error(f"Error in visualization loop: {e}", exc_info=True)
            self.stop()
    
    def change_input_mode(self, mode: str):
        """Change audio input mode (low_level or high_power)"""
        self.logger.info(f"Changing input mode to: {mode}")
        self.audio_input.set_mode(mode)
        self.config['audio']['default_mode'] = mode

        # Update FFT processor sample rate for correct frequency axis.
        if mode == 'low_level':
            low_cfg = self.config['audio'].get('low_level', {})
            sr = int(low_cfg.get('sample_rate', self.config['audio']['sample_rate']))
            self.fft_processor.set_sample_rate(sr)

            # Clamp visualization range to Nyquist for low sample rates
            nyquist = sr / 2.0
            freq_min = float(self.config['visualization']['freq_min'])
            freq_max = float(self.config['visualization']['freq_max'])
            self.fft_processor.set_frequency_range(freq_min, min(freq_max, nyquist))
        else:
            sr = int(self.config['audio']['sample_rate'])
            self.fft_processor.set_sample_rate(sr)
            self.fft_processor.set_frequency_range(
                float(self.config['visualization']['freq_min']),
                float(self.config['visualization']['freq_max'])
            )
    
    def set_brightness(self, brightness: int):
        """Set LED display brightness (0-100)"""
        self.logger.info(f"Setting brightness to: {brightness}")
        self.led_display.set_brightness(brightness)
        self.config['display']['brightness'] = brightness
    
    def set_color_scheme(self, scheme: str):
        """Set visualization color scheme"""
        self.logger.info(f"Setting color scheme to: {scheme}")
        self.fft_processor.set_color_scheme(scheme)
        self.config['visualization']['color_scheme'] = scheme
    
    def get_status(self) -> dict:
        """Get current system status"""
        return {
            'running': self.running,
            'input_mode': self.config['audio']['default_mode'],
            'brightness': self.config['display']['brightness'],
            'color_scheme': self.config['visualization']['color_scheme'],
            'sample_rate': self.config['audio']['sample_rate']
        }


def main():
    """Main entry point"""
    print("=" * 60)
    print("FFT Audio Visualizer for Raspberry Pi 4")
    print("64x64 RGB LED Matrix - 20Hz to 20KHz")
    print("=" * 60)
    print()
    
    # Create and start visualizer
    visualizer = FFTVisualizer()
    
    try:
        visualizer.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        visualizer.stop()
        print("FFT Audio Visualizer stopped")


if __name__ == '__main__':
    main()
