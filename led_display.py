#!/usr/bin/env python3
"""
LED Display Module
Controls 64x64 RGB LED Matrix via Adafruit RGB Matrix HAT
"""

import logging
import numpy as np

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
except ImportError:
    RGBMatrix = None
    RGBMatrixOptions = None
    logging.warning("rgbmatrix library not available, LED display disabled")


class LEDDisplay:
    """LED Matrix display controller"""
    
    def __init__(self, config: dict):
        """Initialize LED display with configuration"""
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        self.rows = config['rows']
        self.cols = config['cols']
        
        # Initialize RGB Matrix
        self.matrix = self._init_matrix()
        
        # Create offscreen canvas for double buffering
        if self.matrix:
            self.canvas = self.matrix.CreateFrameCanvas()
        else:
            self.canvas = None
        
        self.logger.info(f"LED display initialized: {self.cols}x{self.rows}")
    
    def _init_matrix(self):
        """Initialize RGB matrix with hardware configuration"""
        if RGBMatrix is None or RGBMatrixOptions is None:
            self.logger.warning("RGB Matrix library not available")
            return None
        
        try:
            # Configure matrix options
            options = RGBMatrixOptions()
            
            # Matrix dimensions
            options.rows = self.rows
            options.cols = self.cols
            options.chain_length = self.config['chain_length']
            options.parallel = self.config['parallel']
            
            # Hardware mapping for Adafruit HAT
            options.hardware_mapping = self.config['hardware_mapping']
            
            # Display quality settings
            options.pwm_bits = self.config['pwm_bits']
            options.brightness = self.config['brightness']
            options.gpio_slowdown = self.config['gpio_slowdown']
            
            # Performance settings
            options.disable_hardware_pulsing = False
            options.show_refresh_rate = False
            
            # Create matrix
            matrix = RGBMatrix(options=options)
            self.logger.info("RGB Matrix initialized successfully")
            return matrix
        
        except Exception as e:
            self.logger.error(f"Failed to initialize RGB Matrix: {e}")
            return None
    
    def update(self, fft_data: dict):
        """Update display with FFT data"""
        if self.matrix is None or self.canvas is None:
            return
        
        spectrum = fft_data['spectrum']
        peaks = fft_data['peaks']
        colors = fft_data['colors']
        
        # Clear canvas
        self.canvas.Clear()
        
        # Draw spectrum bars
        self._draw_spectrum_bars(spectrum, colors)
        
        # Draw peak indicators
        self._draw_peaks(peaks, colors)
        
        # Swap buffers
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def _draw_spectrum_bars(self, spectrum: np.ndarray, colors: np.ndarray):
        """Draw vertical spectrum bars"""
        num_bars = len(spectrum)
        
        # Calculate bar width (may be 1 or more pixels wide)
        bar_width = max(1, self.cols // num_bars)
        
        for i in range(num_bars):
            # Calculate bar height based on spectrum value
            bar_height = int(spectrum[i] * self.rows)
            
            # Get color for this bar
            r, g, b = colors[i]
            
            # Calculate x position
            x = i * bar_width
            
            # Draw vertical bar from bottom
            for y in range(bar_height):
                y_pos = self.rows - 1 - y  # Flip to draw from bottom
                
                # Draw pixels for bar width
                for dx in range(bar_width):
                    if x + dx < self.cols:
                        # Optional: fade color towards bottom
                        fade = 0.5 + 0.5 * (y / max(1, bar_height))
                        r_faded = int(r * fade)
                        g_faded = int(g * fade)
                        b_faded = int(b * fade)
                        
                        self.canvas.SetPixel(x + dx, y_pos, r_faded, g_faded, b_faded)
    
    def _draw_peaks(self, peaks: np.ndarray, colors: np.ndarray):
        """Draw peak hold indicators"""
        num_bars = len(peaks)
        bar_width = max(1, self.cols // num_bars)
        
        for i in range(num_bars):
            # Calculate peak position
            peak_height = int(peaks[i] * self.rows)
            
            if peak_height > 0:
                # Get color for this peak (brighter than spectrum)
                r, g, b = colors[i]
                
                # Calculate x position
                x = i * bar_width
                
                # Draw peak indicator
                y_pos = self.rows - peak_height
                
                for dx in range(bar_width):
                    if x + dx < self.cols and y_pos >= 0:
                        self.canvas.SetPixel(x + dx, y_pos, r, g, b)
    
    def clear(self):
        """Clear the display"""
        if self.matrix and self.canvas:
            self.canvas.Clear()
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def set_brightness(self, brightness: int):
        """Set display brightness (0-100)"""
        if self.matrix:
            brightness = max(0, min(100, brightness))
            self.matrix.brightness = brightness
            self.config['brightness'] = brightness
            self.logger.info(f"Brightness set to {brightness}")
    
    def test_pattern(self):
        """Display a test pattern"""
        if self.matrix is None or self.canvas is None:
            return
        
        self.canvas.Clear()
        
        # Draw rainbow gradient
        for x in range(self.cols):
            hue = x / self.cols
            for y in range(self.rows):
                intensity = y / self.rows
                r, g, b = self._hsv_to_rgb(hue, 1.0, intensity)
                self.canvas.SetPixel(x, y, r, g, b)
        
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
        self.logger.info("Test pattern displayed")
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> tuple:
        """Convert HSV to RGB"""
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
