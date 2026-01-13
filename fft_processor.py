#!/usr/bin/env python3
"""
FFT Processor Module
Processes audio data and generates frequency spectrum (20Hz-20KHz)
"""

import logging
import numpy as np
from scipy import signal
from typing import Tuple


class FFTProcessor:
    """FFT processor for audio visualization"""
    
    def __init__(self, audio_config: dict, viz_config: dict):
        """Initialize FFT processor"""
        self.logger = logging.getLogger(__name__)
        
        self.sample_rate = audio_config['sample_rate']
        self.fft_size = audio_config['fft_size']
        
        self.freq_min = viz_config['freq_min']
        self.freq_max = viz_config['freq_max']
        self.num_bins = viz_config['num_bins']
        self.freq_scale = viz_config['freq_scale']
        self.smoothing = viz_config['smoothing']
        self.color_scheme = viz_config['color_scheme']
        self.peak_hold = viz_config['peak_hold']
        self.peak_decay = viz_config['peak_decay']
        
        # Create window function for FFT
        self.window = signal.windows.hann(self.fft_size)
        
        # Calculate frequency bins
        self._calculate_frequency_bins()
        
        # Initialize smoothing buffers
        self.prev_spectrum = np.zeros(self.num_bins)
        self.peak_levels = np.zeros(self.num_bins)
        self.peak_hold_counters = np.zeros(self.num_bins, dtype=int)
        
        self.logger.info(f"FFT processor initialized: {self.num_bins} bins, {self.freq_min}-{self.freq_max} Hz")
    
    def _calculate_frequency_bins(self):
        """Calculate frequency bin edges based on scaling"""
        if self.freq_scale == 'logarithmic':
            # Logarithmic frequency scale (more natural for audio)
            self.freq_bins = np.logspace(
                np.log10(self.freq_min),
                np.log10(self.freq_max),
                self.num_bins + 1
            )
        else:
            # Linear frequency scale
            self.freq_bins = np.linspace(
                self.freq_min,
                self.freq_max,
                self.num_bins + 1
            )
        
        self.logger.debug(f"Frequency bins: {self.freq_bins[:5]}...{self.freq_bins[-5:]}")
    
    def process(self, audio_data: np.ndarray) -> dict:
        """
        Process audio data and return FFT spectrum
        
        Returns:
            dict with 'spectrum', 'peaks', and 'colors' arrays
        """
        # Ensure we have enough data
        if len(audio_data) < self.fft_size:
            # Pad with zeros if needed
            audio_data = np.pad(audio_data, (0, self.fft_size - len(audio_data)))
        else:
            # Take last fft_size samples
            audio_data = audio_data[-self.fft_size:]
        
        # Apply window function
        windowed_data = audio_data * self.window
        
        # Compute FFT
        fft_result = np.fft.rfft(windowed_data)
        fft_magnitude = np.abs(fft_result)
        
        # Convert to dB scale
        fft_db = 20 * np.log10(fft_magnitude + 1e-10)
        
        # Get frequency axis
        freqs = np.fft.rfftfreq(self.fft_size, 1.0 / self.sample_rate)
        
        # Map FFT bins to display bins
        spectrum = self._map_to_bins(freqs, fft_db)
        
        # Normalize to 0-1 range
        spectrum = self._normalize_spectrum(spectrum)
        
        # Apply smoothing
        spectrum = self._apply_smoothing(spectrum)
        
        # Update peak levels
        peaks = self._update_peaks(spectrum)
        
        # Generate colors based on spectrum
        colors = self._generate_colors(spectrum)
        
        return {
            'spectrum': spectrum,
            'peaks': peaks,
            'colors': colors
        }
    
    def _map_to_bins(self, freqs: np.ndarray, fft_db: np.ndarray) -> np.ndarray:
        """Map FFT frequency bins to display bins"""
        spectrum = np.zeros(self.num_bins)
        
        for i in range(self.num_bins):
            # Find frequencies in this bin range
            freq_low = self.freq_bins[i]
            freq_high = self.freq_bins[i + 1]
            
            # Find indices of frequencies in this range
            indices = np.where((freqs >= freq_low) & (freqs < freq_high))[0]
            
            if len(indices) > 0:
                # Take maximum value in this bin (for better peak detection)
                spectrum[i] = np.max(fft_db[indices])
        
        return spectrum
    
    def _normalize_spectrum(self, spectrum: np.ndarray) -> np.ndarray:
        """Normalize spectrum to 0-1 range"""
        # Define expected dB range (adjust based on input signal)
        db_min = -60  # Noise floor
        db_max = 0    # Maximum expected level
        
        # Clip and normalize
        normalized = (spectrum - db_min) / (db_max - db_min)
        normalized = np.clip(normalized, 0.0, 1.0)
        
        return normalized
    
    def _apply_smoothing(self, spectrum: np.ndarray) -> np.ndarray:
        """Apply temporal smoothing to spectrum"""
        if self.smoothing > 0:
            # Exponential moving average
            smoothed = (self.smoothing * self.prev_spectrum + 
                       (1 - self.smoothing) * spectrum)
            self.prev_spectrum = smoothed
            return smoothed
        else:
            self.prev_spectrum = spectrum
            return spectrum
    
    def _update_peaks(self, spectrum: np.ndarray) -> np.ndarray:
        """Update peak levels with hold and decay"""
        for i in range(self.num_bins):
            if spectrum[i] > self.peak_levels[i]:
                # New peak
                self.peak_levels[i] = spectrum[i]
                self.peak_hold_counters[i] = self.peak_hold
            else:
                # Decay peak
                if self.peak_hold_counters[i] > 0:
                    self.peak_hold_counters[i] -= 1
                else:
                    self.peak_levels[i] = max(0, self.peak_levels[i] - self.peak_decay)
        
        return self.peak_levels.copy()
    
    def _generate_colors(self, spectrum: np.ndarray) -> np.ndarray:
        """Generate RGB colors for each bin based on color scheme"""
        colors = np.zeros((self.num_bins, 3), dtype=np.uint8)
        
        if self.color_scheme == 'rainbow':
            # Rainbow gradient based on frequency
            for i in range(self.num_bins):
                hue = i / self.num_bins
                colors[i] = self._hsv_to_rgb(hue, 1.0, spectrum[i])
        
        elif self.color_scheme == 'fire':
            # Fire color scheme: black -> red -> orange -> yellow -> white
            for i in range(self.num_bins):
                intensity = spectrum[i]
                if intensity < 0.33:
                    # Black to red
                    r = int(intensity * 3 * 255)
                    colors[i] = [r, 0, 0]
                elif intensity < 0.66:
                    # Red to yellow
                    g = int((intensity - 0.33) * 3 * 255)
                    colors[i] = [255, g, 0]
                else:
                    # Yellow to white
                    b = int((intensity - 0.66) * 3 * 255)
                    colors[i] = [255, 255, b]
        
        elif self.color_scheme == 'ocean':
            # Ocean color scheme: black -> blue -> cyan -> white
            for i in range(self.num_bins):
                intensity = spectrum[i]
                if intensity < 0.5:
                    # Black to blue
                    b = int(intensity * 2 * 255)
                    colors[i] = [0, 0, b]
                else:
                    # Blue to cyan
                    g = int((intensity - 0.5) * 2 * 255)
                    colors[i] = [0, g, 255]
        
        elif self.color_scheme == 'matrix':
            # Matrix green color scheme
            for i in range(self.num_bins):
                g = int(spectrum[i] * 255)
                colors[i] = [0, g, 0]
        
        else:
            # Default: white
            for i in range(self.num_bins):
                intensity = int(spectrum[i] * 255)
                colors[i] = [intensity, intensity, intensity]
        
        return colors
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB color"""
        if s == 0.0:
            rgb = int(v * 255)
            return (rgb, rgb, rgb)
        
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i = i % 6
        
        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def set_color_scheme(self, scheme: str):
        """Change color scheme"""
        if scheme in ['rainbow', 'fire', 'ocean', 'matrix']:
            self.color_scheme = scheme
            self.logger.info(f"Color scheme changed to: {scheme}")
        else:
            self.logger.warning(f"Unknown color scheme: {scheme}")
