#!/usr/bin/env python3
"""audio_input.py

Audio Input Module

Supports two input modes:
- low_level: Digital I2S microphone input (e.g., SPH0645) via PortAudio/ALSA (sounddevice)
- high_power: USB audio interface line-in via PortAudio/ALSA (sounddevice)
"""

import logging
import threading
import queue
import time
from typing import Optional

import numpy as np

try:
    import sounddevice as sd
except ImportError:
    sd = None
    logging.warning("sounddevice not available, audio input disabled")


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
        """Initialize I2S microphone capture settings for low-level input."""
        self.low_level_device = None
        self.low_level_sample_rate = None
        self.low_level_channels = None
        self.low_level_channel_index = 0
        self.low_level_gain = 1.0
        self.low_level_remove_dc = True
        self.low_level_dtype = 'float32'

        if sd is None:
            self.logger.warning("sounddevice not available, low-level input disabled")
            return

        try:
            low_cfg = self.config.get('low_level', {})

            device = low_cfg.get('device', 'default')
            if device == 'default':
                self.low_level_device = sd.default.device[0]  # Default input device
            else:
                # Allow either numeric index or a PortAudio device name/substring
                self.low_level_device = int(device) if str(device).isdigit() else str(device)

            self.low_level_sample_rate = int(low_cfg.get('sample_rate', self.sample_rate))
            self.low_level_channels = int(low_cfg.get('channels', 1))
            self.low_level_channel_index = int(low_cfg.get('channel_index', 0))
            self.low_level_gain = float(low_cfg.get('gain', 1.0))
            self.low_level_remove_dc = bool(low_cfg.get('remove_dc', True))
            self.low_level_dtype = str(low_cfg.get('dtype', 'float32'))

            self.logger.info(
                "Low-level input initialized (I2S mic): "
                f"device={self.low_level_device}, sr={self.low_level_sample_rate}, "
                f"channels={self.low_level_channels}, ch_index={self.low_level_channel_index}"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize low-level (I2S) input: {e}")
            self.low_level_device = None
    
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
        """Capture loop for low-level input using an I2S digital microphone."""
        if sd is None or self.low_level_device is None:
            self.logger.error("Low-level input device not initialized")
            return

        low_cfg = self.config.get('low_level', {})
        sr = int(self.low_level_sample_rate or low_cfg.get('sample_rate', self.sample_rate))
        channels = int(self.low_level_channels or low_cfg.get('channels', 1))
        channel_index = int(low_cfg.get('channel_index', self.low_level_channel_index))
        gain = float(low_cfg.get('gain', self.low_level_gain))
        remove_dc = bool(low_cfg.get('remove_dc', self.low_level_remove_dc))
        dtype = str(low_cfg.get('dtype', self.low_level_dtype))

        def audio_callback(indata, frames, time_info, status):
            if status:
                self.logger.warning(f"Low-level audio callback status: {status}")

            if indata is None:
                return

            if getattr(indata, 'ndim', 1) == 1:
                data = indata
            else:
                idx = max(0, min(channel_index, indata.shape[1] - 1))
                data = indata[:, idx]

            audio_data = np.asarray(data, dtype=np.float32)
            if remove_dc:
                audio_data = audio_data - float(np.mean(audio_data))
            if gain != 1.0:
                audio_data = audio_data * gain
            audio_data = np.clip(audio_data, -1.0, 1.0)

            try:
                self.audio_queue.put_nowait(audio_data.copy())
            except queue.Full:
                pass

        try:
            with sd.InputStream(
                device=self.low_level_device,
                channels=channels,
                samplerate=sr,
                blocksize=self.buffer_size,
                dtype=dtype,
                callback=audio_callback,
            ):
                while self.running:
                    sd.sleep(100)
        except Exception as e:
            self.logger.error(f"Error in low-level (I2S) input loop: {e}")
    
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
