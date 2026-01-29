# FFT Audio Visualizer

A professional DIY project for real-time audio frequency spectrum visualization (20Hz-20KHz) using Raspberry Pi 4, Adafruit RGB Matrix HAT, and 64x64 RGB LED Matrix.

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%204-red.svg)

## Features

✨ **Dual Input Modes**
- **Low-Level Mode**: Ambient/near-field audio capture via digital I2S microphone (SPH0645)
- **High-Power Mode**: 40W audio amplifier outputs for music visualization (via USB audio interface)

📊 **Real-Time FFT Processing**
- 20Hz to 20KHz frequency range
- Logarithmic or linear frequency scaling
- 64 frequency bins for optimal display
- Configurable smoothing and peak detection

🎨 **Multiple Color Schemes**
- Rainbow: Frequency-based color gradient
- Fire: Black → Red → Orange → Yellow → White
- Ocean: Black → Blue → Cyan → White
- Matrix: Classic green monochrome

🖥️ **Interactive Menu System**
- 20x4 character LCD or 128x64 OLED display
- I2C OLED menu display (128x64)
- Rotary encoder navigation (rotate + press)
- Real-time settings adjustment
- System status display

⚡ **High Performance**
- Optimized for Raspberry Pi 4
- Hardware-accelerated LED matrix control
- 30+ FPS visualization
- Low latency audio processing

## Hardware Requirements

### Core Components
- Raspberry Pi 4 Model B (2GB+ RAM)
- Adafruit RGB Matrix HAT + RTC (Product ID: 2345)
- 64x64 RGB LED Matrix Panel, 3mm pitch (Product ID: 3649)
- 5V 4A Power Supply

### Audio Input (Low-Level)
- Digital MEMS I2S microphone (SPH0645)
- I2S/PCM wiring to Raspberry Pi GPIO (BCLK/LRCLK/DOUT)

### Audio Input (High-Power)
- USB Audio Interface (e.g., Behringer UCA202)
- Voltage divider/attenuator circuit (10:1 ratio)
- High-wattage resistors and heatsinking

### Menu Display
- 0.96" OLED Display (128x64, I2C) (SSD1306-compatible)

### Navigation
- I2C Rotary Encoder board (Adafruit Seesaw-based, address 0x49)

### Miscellaneous
- MicroSD Card (16GB+, Class 10)
- Heatsinks and cooling
- Enclosure/case
- Cables and connectors

**Full Bill of Materials and circuit diagrams: See [HARDWARE.md](HARDWARE.md)**

## Quick Start

### 1. Install Dependencies
```bash
# System packages
sudo apt-get update
sudo apt-get install -y python3-pip git i2c-tools portaudio19-dev

# RGB Matrix library
cd ~
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix
make build-python PYTHON=$(which python3)
sudo make install-python PYTHON=$(which python3)
```

### 2. Clone Repository
```bash
cd ~
git clone https://github.com/InazioLizuain/FFTVisualizer.git
cd FFTVisualizer
```

### 3. Install Python Dependencies
```bash
pip3 install -r requirements.txt
```

### 4. Configure
```bash
# Edit configuration file
nano config.yaml

# Adjust settings:
# - Default input mode (low_level or high_power)
# - LED matrix brightness
# - GPIO pin assignments
# - Audio parameters
```

### 5. Run
```bash
# Run visualizer (requires sudo for LED matrix access)
sudo python3 fft_visualizer.py
```

**Detailed installation instructions: See [INSTALL.md](INSTALL.md)**

## Documentation

- **[HARDWARE.md](HARDWARE.md)** - Complete hardware setup, BOM, circuit diagrams, and assembly instructions
- **[INSTALL.md](INSTALL.md)** - Step-by-step installation guide for software and dependencies
- **[USAGE.md](USAGE.md)** - Operating instructions, configuration, and troubleshooting

## Project Structure

```
FFTVisualizer/
├── fft_visualizer.py      # Main application entry point
├── audio_input.py         # Dual-mode audio input handler (I2S mic + USB Audio)
├── fft_processor.py       # FFT processing and frequency analysis
├── led_display.py         # RGB LED matrix display driver
├── menu_system.py         # OLED/LCD menu and input navigation
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── HARDWARE.md            # Hardware documentation
├── INSTALL.md             # Installation guide
└── USAGE.md               # Usage guide
```

## Configuration

Key settings in `config.yaml`:

```yaml
audio:
  sample_rate: 44100           # Audio sampling rate
  fft_size: 2048               # FFT window size
  default_mode: 'low_level'    # Input mode

visualization:
  freq_min: 20                 # Minimum frequency (Hz)
  freq_max: 20000              # Maximum frequency (Hz)
  freq_scale: 'logarithmic'    # Frequency scaling
  color_scheme: 'rainbow'      # Color scheme
  smoothing: 0.7               # Temporal smoothing (0-1)

display:
  brightness: 75               # LED brightness (0-100)
  hardware_mapping: 'adafruit-hat'
```

## Usage Examples

### Music Visualization
```bash
# Set to high-power mode for music
# Connect speaker output through attenuator to USB audio interface
sudo python3 fft_visualizer.py
# Use menu to select: Input Mode → High Power
```

### Signal Generator Testing
```bash
# Set to low-level mode for I2S microphone
# Ensure the I2S mic appears in `arecord -l` and config.yaml is set correctly
sudo python3 fft_visualizer.py
# Use menu to select: Input Mode → Low Level
```

### Auto-Start on Boot
```bash
# Install as systemd service
sudo cp fft-visualizer.service /etc/systemd/system/
sudo systemctl enable fft-visualizer.service
sudo systemctl start fft-visualizer.service
```

## Troubleshooting

### LED Matrix Not Working
- Check 5V power supply connection
- Verify ribbon cable orientation
- Increase `gpio_slowdown` in config.yaml
- Ensure HAT is properly seated

### No Audio Input
- Verify I2C devices: `i2cdetect -y 1` (OLED/encoder/RTC)
- Check capture devices: `arecord -l`
- For low-level (I2S mic): verify I2S/PCM is enabled and the correct overlay is loaded
- Verify `audio.low_level.device`, `channels`, and `channel_index` in config.yaml

### Display Flickering
- Increase `gpio_slowdown` (1-4)
- Check power supply capacity
- Reduce `brightness`
- Verify cable connections

**More troubleshooting: See [INSTALL.md](INSTALL.md) and [USAGE.md](USAGE.md)**

## Performance

Typical performance on Raspberry Pi 4:
- FFT Processing: ~30-60 FPS
- Display Update: ~30 FPS (limited by LED matrix refresh)
- CPU Usage: ~40-60% (single core)
- Latency: ~50-100ms (configurable)

## Safety Notes

⚠️ **Important Safety Information:**

1. **High-Power Audio Input**
   - Never connect speaker output directly to audio interface
   - Always use proper attenuation circuit
   - Use high-wattage resistors with heatsinking
   - Verify connections before applying power

2. **Power Supply**
   - Use adequate 5V 4A supply for LED matrix
   - Ensure proper grounding
   - Use fuses on all power inputs

3. **Electrical Safety**
   - Never touch exposed circuits while powered
   - Use proper insulation and enclosures
   - Keep away from flammable materials

## Contributing

Contributions are welcome! Please feel free to submit issues, fork the repository, and create pull requests.

## License

This project is open source and available under the MIT License.

## Credits

- Built for Raspberry Pi 4
- Uses [hzeller/rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) library
- Designed for Adafruit RGB Matrix HAT and LED panels

## Support

For questions, issues, or suggestions:
- Open an issue on GitHub
- Check the documentation files
- Review existing issues for solutions

## Acknowledgments

- Adafruit Industries for excellent hardware and documentation
- Henner Zeller for the RGB LED matrix library
- The Raspberry Pi community

---

**Enjoy your FFT Audio Visualizer!** 🎵 🌈 💡
