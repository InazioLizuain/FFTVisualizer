# Usage Guide

## Quick Start

### Starting the Visualizer

#### Manual Start
```bash
cd ~/FFTVisualizer
sudo python3 fft_visualizer.py
```

#### Using systemd Service
```bash
# Start
sudo systemctl start fft-visualizer.service

# Stop
sudo systemctl stop fft-visualizer.service

# Restart
sudo systemctl restart fft-visualizer.service

# Check status
sudo systemctl status fft-visualizer.service
```

### Stopping the Visualizer
- Press `Ctrl+C` if running manually
- Use the rotary encoder long-press to go back
- Or use systemctl stop command

---

## Input Modes

The FFT Visualizer supports two distinct audio input modes:

### 1. Low-Level Mode (10mV-1V)

**Use Case:** Ambient/near-field audio capture with a digital I2S microphone (SPH0645)

**Features:**
- Full audio-bandwidth sampling (commonly 48kHz)
- No analog biasing/ADC required
- Stable frequency axis (sample rate is defined in config)

**Connection:**
- Wire the SPH0645 to the Raspberry Pi I2S/PCM pins (see HARDWARE.md)
- Enable I2S/PCM + correct overlay so the mic appears in `arecord -l`

**To Activate:**
- Use menu system: `Input Mode` → `Low Level`
- Or edit config.yaml: `default_mode: 'low_level'`

**Tuning:**
- If the device exposes 2 channels but only one has audio, set `audio.low_level.channels: 2` and flip `audio.low_level.channel_index` between 0 and 1.
- Use `audio.low_level.gain` for simple level scaling.

### 2. High-Power Mode (40W Audio)

**Use Case:** Speaker outputs, audio amplifiers, music visualization

**Features:**
- Uses USB audio interface
- Attenuated input for high-power signals
- Real-time music visualization
- Standard audio sampling

**Connection:**
- Connect speaker output through attenuator circuit
- Use USB audio interface for capture
- WARNING: Never connect speaker output directly!

**To Activate:**
- Use menu system: `Input Mode` → `High Power`
- Or edit config.yaml: `default_mode: 'high_power'`

**Setup:**
1. Connect attenuator to speaker output
2. Connect attenuator output to USB audio interface line-in
3. Test with low volume first
4. Gradually increase volume while monitoring display

---

## Menu System Navigation

### Rotary Encoder Functions (I2C)

- **Rotate clockwise**: Next menu item
- **Rotate counter-clockwise**: Previous menu item
- **Press (short)**: Select/activate current menu item
- **Press (long)**: Back to main menu

### Menu Structure

```
Main Menu
├── Input Mode
│   ├── Low Level (10mV-1V)
│   ├── High Power (40W)
│   └── Back
├── Brightness
│   ├── 25%
│   ├── 50%
│   ├── 75%
│   ├── 100%
│   └── Back
├── Color Scheme
│   ├── Rainbow
│   ├── Fire
│   ├── Ocean
│   ├── Matrix
│   └── Back
└── System Info
    └── (Display current settings)
```

---

## Display Interpretation

### Understanding the Visualization

The 64x64 LED matrix displays the frequency spectrum from 20Hz to 20KHz:

```
Top of display    = Maximum amplitude
Bottom of display = No signal
Left side         = Low frequencies (20Hz)
Right side        = High frequencies (20KHz)
```

### Frequency Mapping

With logarithmic scaling (default):
- Columns 1-10: Bass (20Hz - 200Hz)
- Columns 11-25: Lower mids (200Hz - 800Hz)
- Columns 26-45: Upper mids (800Hz - 4kHz)
- Columns 46-64: Treble (4kHz - 20kHz)

With linear scaling:
- Each column represents approximately 312.5Hz (20000/64)

### Visual Elements

1. **Spectrum Bars**: Vertical bars showing current amplitude at each frequency
2. **Peak Indicators**: Bright dots at top of recent peak levels
3. **Color Coding**: Colors indicate frequency (rainbow mode) or intensity (other modes)

---

## Color Schemes

### Rainbow
- Colors represent frequency range
- Low frequencies (bass) = Red/Orange
- Mid frequencies = Green/Yellow
- High frequencies (treble) = Blue/Purple
- Best for: General music visualization

### Fire
- Black → Red → Orange → Yellow → White
- Colors represent intensity
- Hottest signals = Brightest colors
- Best for: Dramatic effect, dance music

### Ocean
- Black → Blue → Cyan → White
- Cool color palette
- Calming visual effect
- Best for: Ambient music, quiet environments

### Matrix
- Classic green monochrome
- Retro computer aesthetic
- Easy on the eyes in dark rooms
- Best for: Dark environments, retro look

---

## Configuration

### Editing Configuration

```bash
cd ~/FFTVisualizer
nano config.yaml
```

### Key Settings

#### Audio Settings
```yaml
audio:
  sample_rate: 44100        # Higher = better resolution, more CPU
  fft_size: 2048            # Higher = better freq resolution, slower
  buffer_size: 4096         # Larger = more latency, more stable
```

#### Visualization Settings
```yaml
visualization:
  freq_min: 20              # Minimum frequency to display (Hz)
  freq_max: 20000           # Maximum frequency to display (Hz)
  num_bins: 64              # Must match LED matrix width
  freq_scale: 'logarithmic' # 'linear' or 'logarithmic'
  smoothing: 0.7            # 0-1, higher = smoother but slower response
  color_scheme: 'rainbow'   # 'rainbow', 'fire', 'ocean', 'matrix'
  peak_hold: 15             # Frames to hold peak indicator
  peak_decay: 0.05          # Rate of peak decay
```

#### Display Settings
```yaml
display:
  brightness: 75            # 0-100, affects power consumption
  pwm_bits: 11              # 1-11, higher = more colors, slower
  gpio_slowdown: 2          # 0-4, increase if display flickers
```

### Applying Configuration Changes

After editing config.yaml:
```bash
# Restart the service
sudo systemctl restart fft-visualizer.service
```

---

## Performance Tuning

### For Better Frequency Resolution
- Increase `fft_size` (e.g., 4096)
- Trade-off: Higher CPU usage, more latency

### For Faster Response
- Decrease `smoothing` (e.g., 0.3)
- Decrease `buffer_size`
- Trade-off: More jittery display

### For Better Visual Quality
- Increase `pwm_bits` (up to 11)
- Increase `brightness`
- Trade-off: Higher CPU usage, more power

### For Stability
- Increase `gpio_slowdown` (especially on Pi 4)
- Decrease `pwm_bits`
- Trade-off: Fewer colors, lower visual quality

---

## Use Cases and Examples

### 1. Audio Testing Lab
**Mode:** Low-Level
**Settings:**
- `freq_scale: 'linear'` for accurate frequency measurement
- `smoothing: 0.1` for fast response
- `color_scheme: 'matrix'` for clear reading

**Use:**
- Connect signal generator
- Sweep frequency to verify range
- Check amplitude response

### 2. Music Visualization
**Mode:** High-Power
**Settings:**
- `freq_scale: 'logarithmic'` for natural music representation
- `smoothing: 0.7` for smooth animation
- `color_scheme: 'rainbow'` or 'fire' for visual appeal

**Use:**
- Connect to amplifier speaker output
- Adjust volume to achieve good visualization
- Enjoy the light show!

### 3. Room Acoustics Analysis
**Mode:** Either (depends on source)
**Settings:**
- `freq_scale: 'logarithmic'`
- `smoothing: 0.5`
- Record display over time
- Identify resonant frequencies

### 4. DJ/Performance Use
**Mode:** High-Power
**Settings:**
- `brightness: 100` for visibility
- `color_scheme: 'fire'` or 'rainbow' for effect
- Mount display prominently
- Sync with music for audience engagement

---

## Monitoring and Logs

### Real-Time Monitoring
```bash
# Watch logs
tail -f /var/log/fft_visualizer.log

# Check system status
sudo systemctl status fft-visualizer.service

# Monitor CPU usage
htop  # Look for python3 process
```

### Debug Mode
Enable debug in config.yaml:
```yaml
system:
  debug: true
```

This provides:
- Detailed FFT calculations
- Frame rate information
- Audio input levels
- More verbose logging

---

## Troubleshooting

### No Visualization
1. Check audio input is connected
2. Verify input mode matches source
3. Check audio levels: `arecord -l` and/or a short `arecord` test recording
4. Increase `brightness` in config
5. Check logs for errors

### Choppy/Laggy Display
1. Reduce `pwm_bits` in config
2. Increase `gpio_slowdown`
3. Disable desktop environment
4. Close other applications
5. Check CPU temperature (may be throttling)

### Incorrect Frequencies
1. Verify `sample_rate` matches audio input
2. Check `fft_size` is appropriate
3. Calibrate with known frequency source
4. Adjust gain settings for input mode

### Display Flickering
1. Increase `gpio_slowdown` (up to 4)
2. Check power supply is adequate
3. Verify all cable connections
4. Reduce `brightness`

---

## Safety and Maintenance

### Safety
- Never touch exposed circuits while powered
- Use proper insulation on high-power connections
- Keep display away from flammable materials
- Ensure adequate ventilation

### Maintenance
- Clean LED matrix with soft, dry cloth
- Check cable connections periodically
- Monitor system temperature
- Update software regularly

### Power Cycling
Safe shutdown procedure:
```bash
sudo systemctl stop fft-visualizer.service
sudo shutdown -h now
```

---

## Advanced Features

### Custom Frequency Ranges

For specific applications, adjust frequency range:

**Bass monitoring (20-200Hz):**
```yaml
freq_min: 20
freq_max: 200
```

**Vocal range (85-1100Hz):**
```yaml
freq_min: 85
freq_max: 1100
```

**Ultrasonic detection (16-20kHz):**
```yaml
freq_min: 16000
freq_max: 20000
```

### Multiple Instances
Run different configurations simultaneously (requires multiple LED matrices):
```bash
# Instance 1: Bass
sudo python3 fft_visualizer.py --config config_bass.yaml

# Instance 2: Treble
sudo python3 fft_visualizer.py --config config_treble.yaml
```

---

## Tips and Tricks

1. **Best Visual Effect**: Use `freq_scale: 'logarithmic'` with `color_scheme: 'rainbow'`

2. **Lab Testing**: Use `freq_scale: 'linear'` for accurate frequency measurement

3. **Low Light**: Reduce brightness to 25-50% for comfortable viewing

4. **Battery Power**: Reduce brightness to extend battery life

5. **Recording**: Use screen recording software to capture visualizations

6. **Synchronization**: Adjust `buffer_size` to match audio latency

---

## Getting Help

If you encounter issues:
1. Check the logs: `tail -f /var/log/fft_visualizer.log`
2. Verify hardware connections (see HARDWARE.md)
3. Review configuration settings
4. Test with known good audio source
5. Check GitHub issues for similar problems

## Further Customization

The code is designed to be modular and extensible:
- Add new color schemes in `fft_processor.py`
- Modify visualization in `led_display.py`
- Create custom menu items in `menu_system.py`
- Adjust FFT algorithm in `fft_processor.py`

Enjoy your FFT Audio Visualizer!
