#!/usr/bin/env python3
"""
Audio Input Module
Handles dual input modes: low-level (10mV-1V) and high-power (40W output)
"""

import logging
import threading
import queue
from typing import Optional

import numpy as np

try:
    import sounddevice as sd
except ImportError:
    sd = None
    logging.warning("sounddevice not available, audio input disabled")

try:
    # For ADC input (low-level signals)
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
except ImportError:
    ADS = None
    AnalogIn = None
    logging.warning("ADC libraries not available, low-level input disabled")


class AudioInput:
    """Audio input handler with dual input modes"""
    
    def __init__(self, config: dict):
        """Initialize audio input with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.mode = config.get('default_mode', 'low_level')
        self.sample_rate = config['sample_rate']
        self.buffer_size = config['buffer_size']
        
        # Audio data queue
        self.audio_queue = queue.Queue(maxsize=10)
        
        # Threading
        self.running = False
        self.input_thread = None
        
        # Initialize input devices
        self._init_low_level_input()
        self._init_high_power_input()
        
        self.logger.info(f"Audio input initialized in {self.mode} mode")
    
    def _init_low_level_input(self):
        """Initialize ADC for low-level signal input (10mV-1V)"""
        self.adc = None
        self.adc_channel = None
        
        if ADS is None:
            self.logger.warning("ADC not available, low-level input disabled")
            return
        
        try:
            # Initialize I2C and ADC
            i2c = busio.I2C(board.SCL, board.SDA)
            self.adc = ADS.ADS1115(i2c)
            
            # Configure ADC channel with appropriate gain for 10mV-1V range
            channel_num = self.config['low_level']['adc_channel']
            if channel_num == 0:
                self.adc_channel = AnalogIn(self.adc, ADS.P0)
            elif channel_num == 1:
                self.adc_channel = AnalogIn(self.adc, ADS.P1)
            elif channel_num == 2:
                self.adc_channel = AnalogIn(self.adc, ADS.P2)
            elif channel_num == 3:
                self.adc_channel = AnalogIn(self.adc, ADS.P3)
            
            # Set gain for better resolution in low voltage range
            # Gain of 16 gives range of +/- 0.256V which is suitable for our 10mV-1V range
            self.adc.gain = 16
            
            self.logger.info("ADC initialized for low-level input")
        except Exception as e:
            self.logger.error(f"Failed to initialize ADC: {e}")
            self.adc = None
    
    def _init_high_power_input(self):
        """Initialize audio device for high-power signal input (40W output)"""
        self.audio_device = None
        
        if sd is None:
            self.logger.warning("sounddevice not available, high-power input disabled")
            return
        
        try:
            # Get default or specified audio device
            device = self.config['high_power'].get('device', 'default')
            if device == 'default':
                self.audio_device = sd.default.device[0]  # Default input device
            else:
                self.audio_device = int(device)
            
            self.logger.info(f"Audio device initialized: {self.audio_device}")
        except Exception as e:
            self.logger.error(f"Failed to initialize audio device: {e}")
            self.audio_device = None
    
    def start(self):
        """Start audio input capture"""
        if self.running:
            self.logger.warning("Audio input already running")
            return
        
        self.running = True
        self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()
        self.logger.info("Audio input started")
    
    def stop(self):
        """Stop audio input capture"""
        self.running = False
        if self.input_thread:
            self.input_thread.join(timeout=2.0)
        self.logger.info("Audio input stopped")
    
    def _input_loop(self):
        """Main input loop - runs in separate thread"""
        if self.mode == 'low_level':
            self._low_level_input_loop()
        elif self.mode == 'high_power':
            self._high_power_input_loop()
    
    def _low_level_input_loop(self):
        """Capture loop for low-level signals using ADC"""
        if self.adc is None or self.adc_channel is None:
            self.logger.error("ADC not initialized for low-level input")
            return
        
        gain = self.config['low_level']['gain']
        buffer = []
        
        try:
            while self.running:
                # Read voltage from ADC
                voltage = self.adc_channel.voltage
                
                # Apply gain and convert to normalized audio sample (-1.0 to 1.0)
                sample = (voltage * gain) / 3.3  # Normalize to -1 to 1 range
                sample = np.clip(sample, -1.0, 1.0)
                
                buffer.append(sample)
                
                # When buffer is full, send to queue
                if len(buffer) >= self.buffer_size:
                    audio_data = np.array(buffer, dtype=np.float32)
                    
                    # Try to put in queue, discard if full
                    try:
                        self.audio_queue.put_nowait(audio_data)
                    except queue.Full:
                        pass  # Drop frame if queue is full
                    
                    buffer = []
        
        except Exception as e:
            self.logger.error(f"Error in low-level input loop: {e}")
    
    def _high_power_input_loop(self):
        """Capture loop for high-power signals using audio device"""
        if sd is None or self.audio_device is None:
            self.logger.error("Audio device not initialized for high-power input")
            return
        
        attenuation = self.config['high_power']['attenuation']
        
        def audio_callback(indata, frames, time_info, status):
            """Callback for audio input"""
            if status:
                self.logger.warning(f"Audio callback status: {status}")
            
            # Apply attenuation to high-power signal
            audio_data = indata[:, 0] * attenuation  # Use first channel
            
            # Try to put in queue, discard if full
            try:
                self.audio_queue.put_nowait(audio_data.copy())
            except queue.Full:
                pass  # Drop frame if queue is full
        
        try:
            with sd.InputStream(
                device=self.audio_device,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                callback=audio_callback
            ):
                while self.running:
                    sd.sleep(100)  # Sleep in ms
        
        except Exception as e:
            self.logger.error(f"Error in high-power input loop: {e}")
    
    def get_audio_data(self) -> Optional[np.ndarray]:
        """Get audio data from queue"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
    
    def set_mode(self, mode: str):
        """Change input mode"""
        if mode not in ['low_level', 'high_power']:
            self.logger.error(f"Invalid input mode: {mode}")
            return
        
        if mode == self.mode:
            return  # Already in this mode
        
        # Stop current input
        was_running = self.running
        if was_running:
            self.stop()
        
        # Change mode
        self.mode = mode
        self.logger.info(f"Input mode changed to: {mode}")
        
        # Restart if it was running
        if was_running:
            self.start()
    
    def get_input_level(self) -> float:
        """Get current input signal level (for monitoring/calibration)"""
        try:
            audio_data = self.audio_queue.get_nowait()
            if audio_data is not None:
                return np.abs(audio_data).max()
        except queue.Empty:
            pass
        return 0.0
