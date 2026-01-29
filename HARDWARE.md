# Hardware Requirements and Setup

## Bill of Materials (BOM)

### Core Components
1. **Raspberry Pi 4 Model B** (2GB or 4GB RAM recommended)
   - For running the main application and processing FFT

2. **Adafruit RGB Matrix HAT + RTC for Raspberry Pi**
   - Product ID: 2345
   - Provides clean 5V power to LED matrix and level-shifted outputs
   - Includes Real-Time Clock (bonus feature)

3. **64x64 RGB LED Matrix Panel - 3mm Pitch**
   - Product ID: 3649 (Adafruit) or compatible
   - 3mm pitch recommended for better resolution
   - 5V power supply (see below)

4. **5V 4A (4000mA) Power Supply**
   - For powering the LED matrix
   - Minimum 4A for full brightness on 64x64 matrix
   - Barrel jack: 5.5mm OD, 2.1mm ID, center-positive

### Audio Input Hardware

#### For Low-Level Audio (Digital I2S Microphone)
5. **Digital MEMS I2S Microphone (SPH0645)**
   - I2S/PCM digital audio output (no analog biasing/ADC required)
   - 3.3V power (do not use 5V)
   - Typical use: ambient/music pickup near the system
   - Note: many I2S mic drivers expose **2 channels** even for a single mic; the project supports selecting `channel_index` in config.

#### For High-Power Audio (40W Output)
7. **USB Audio Interface**
   - Any USB audio interface compatible with Raspberry Pi
   - Recommended: Behringer UCA202 or similar
   - Line-level input capability

8. **Voltage Divider/Attenuator Circuit:**
   - Resistors: 100kΩ and 10kΩ (10:1 attenuation)
   - Capacitor: 100µF (power supply decoupling)
   - Heat-shrink tubing or enclosure
   - Speaker wire connectors

### Menu/Display Components
9. **0.96" OLED Display (128x64, I2C)**
   - For menu system and settings display
   - Midas passive OLED, 128x64 pixels, yellow
   - Typical I2C address: 0x3C (sometimes 0x3D)
   - Note: some 0.96" I2C OLED modules use SH1106 instead of SSD1306; if your display does not respond with the SSD1306 driver, you may need an SH1106-compatible driver.

10. **I2C Rotary Encoder + Breakout Board (Adafruit, Seesaw-based)**
   - Used for menu navigation
   - I2C address: 0x49
   - Provides rotation + push button

### Miscellaneous
11. **MicroSD Card** (16GB or larger, Class 10)
    - For Raspberry Pi OS and application

12. **Cooling** (recommended)
    - Heatsinks for Raspberry Pi
    - Small fan (optional, 5V)

13. **Enclosure/Case**
    - Custom or off-the-shelf enclosure
    - Must accommodate Pi, HAT, and LED matrix mounting

14. **Cables and Connectors**
    - Ribbon cable (comes with RGB Matrix HAT)
    - Jumper wires (male-to-female, female-to-female)
    - USB cables

---

## Circuit Diagrams

### Low-Level Audio Input (I2S Microphone: SPH0645)

The SPH0645 is a **digital I2S microphone**, so you wire it to the Raspberry Pi PCM/I2S pins. No analog protection/bias/ADC circuitry is required.

Typical wiring (Raspberry Pi 40-pin header):

```
SPH0645  -> Raspberry Pi
3V3/VDD  -> 3.3V (Pin 1)
GND      -> GND  (Pin 6)
BCLK/SCK -> GPIO18 / PCM_CLK  (Pin 12)
LRCLK/WS -> GPIO19 / PCM_FS   (Pin 35)
DOUT/SD  -> GPIO20 / PCM_DIN  (Pin 38)

# Some breakout boards also expose SEL/LR.
# If present, it selects which stereo slot the mic transmits on.
```

**Notes:**
- Enable I2S/PCM on Raspberry Pi OS and install the correct device-tree overlay for your SPH0645 breakout.
- Many I2S mic drivers expose **2 channels**; if you only see audio on one side, set `audio.low_level.channel_index` (0 or 1) and keep `channels: 2`.

### High-Power Audio Input Circuit (40W Output)

```
Speaker Output (from amplifier)
    |
    +--- [100kΩ] ---+--- To USB Audio Interface Line-In
    |               |
    |           [10kΩ] (10:1 attenuation)
    |               |
    +-------------GND

WARNING: Never connect speaker output directly to audio interface!
The attenuator reduces 40W (approx 20V RMS) to safe line level (~2V RMS)
```

**Alternative:** Use a commercial speaker-to-line-level converter

**Notes:**
- 10:1 attenuation ratio for safety
- Use high wattage resistors (1W or higher)
- Add heatsinking if needed
- Consider using a transformer isolation for better safety

### I2C Rotary Encoder Connections (Recommended)

The I2C rotary encoder breakout shares the same I2C bus as the OLED and the RTC on the RGB Matrix HAT:

```
Encoder Board -> Raspberry Pi
VCC (3V/3.3V) -> 3.3V
GND           -> GND
SDA           -> GPIO 2 (SDA)
SCL           -> GPIO 3 (SCL)

I2C address: 0x49
```

Verify on the Pi:
```bash
i2cdetect -y 1
```

You should typically see:
- OLED: 0x3C (or 0x3D)
- Encoder: 0x49
- RTC on RGB Matrix HAT: 0x68

### Buttons (Not used)

This build uses an **I2C rotary encoder** for menu navigation; no additional button wiring is required.

### LCD Display Connections (20x4 Character LCD)

If using raw LCD (without I2C backpack):
```
LCD Pin -> Raspberry Pi
RS  -> GPIO 25
E   -> GPIO 24
D4  -> GPIO 23
D5  -> GPIO 17
D6  -> GPIO 18
D7  -> GPIO 22
VSS -> GND
VDD -> 5V
V0  -> 10kΩ pot (contrast adjustment)
A   -> 5V (backlight anode)
K   -> GND (backlight cathode)
```

If using I2C backpack:
```
VCC -> 5V
GND -> GND
SDA -> GPIO 2 (SDA)
SCL -> GPIO 3 (SCL)
```

---

## Physical Assembly

### Step 1: Prepare Raspberry Pi
1. Install heatsinks on Raspberry Pi CPU and RAM chips
2. Flash Raspberry Pi OS Lite (64-bit) to microSD card
3. Enable SSH and configure WiFi (optional) via raspi-config

### Step 2: Install RGB Matrix HAT
1. Mount Adafruit RGB Matrix HAT onto Raspberry Pi GPIO header
2. Ensure HAT is firmly seated on all 40 pins
3. Connect 5V power supply to HAT's barrel jack

### Step 3: Connect LED Matrix
1. Connect ribbon cable from HAT to LED matrix input connector
2. Connect 5V power from HAT to LED matrix power input
3. Ensure polarity is correct (red = 5V, black = GND)

### Step 4: Build Audio Input Circuits
1. Connect the I2S microphone to the Raspberry Pi PCM/I2S pins
2. Build the high-power attenuator circuit (use proper insulation!)
3. Verify wiring before powering on

### Step 5: Connect I2S Microphone (for low-level input)
1. Connect SPH0645 to GPIO18/19/20 + 3.3V + GND
2. Enable I2S/PCM and configure the correct overlay (see INSTALL.md)
3. Verify the capture device appears in `arecord -l`

### Step 6: Connect USB Audio (for high-power input)
1. Connect USB audio interface to Raspberry Pi
2. Connect attenuator circuit to audio interface line input
3. Verify device: `arecord -l`

### Step 7: Connect OLED Display
1. Connect OLED via I2C: SDA (GPIO2) and SCL (GPIO3)
2. Power the OLED from 3.3V and GND
3. Verify it appears in `i2cdetect -y 1` (typically 0x3C)

### Step 8: Connect I2C Rotary Encoder
1. Connect encoder board via I2C: SDA (GPIO2) and SCL (GPIO3)
2. Power the encoder from 3.3V and GND
3. Verify it appears in `i2cdetect -y 1` (0x49)

### Step 9: Final Assembly
1. Mount all components in enclosure
2. Ensure adequate ventilation for Raspberry Pi
3. Route cables neatly to avoid interference
4. Add strain relief for external cables

---

## Power Considerations

### Power Budget
- Raspberry Pi 4: ~3W (600mA @ 5V)
- RGB Matrix HAT: ~0.5W (100mA @ 5V)
- 64x64 LED Matrix (full white): ~20W (4000mA @ 5V)
- 64x64 LED Matrix (typical usage): ~10W (2000mA @ 5V)
- LCD Display: ~0.5W (100mA @ 5V)
- USB Audio Interface: ~0.5W (100mA @ 5V)

**Total: ~15W typical, ~25W maximum**

### Power Supply Recommendations
- Use separate 5V 4A supply for LED matrix (via RGB Matrix HAT)
- Raspberry Pi can be powered from HAT's barrel jack
- Or use official Raspberry Pi 15W USB-C power supply

### Safety Notes
- Never exceed voltage ratings
- Use fuses on all power inputs
- Ensure proper grounding
- Keep high-power audio circuit isolated
- Use insulated connectors and enclosures

---

## Testing and Calibration

### 1. LED Matrix Test
Run the test pattern:
```bash
cd /home/pi/FFTVisualizer
python3 -c "from led_display import LEDDisplay; import yaml; cfg = yaml.safe_load(open('config.yaml')); d = LEDDisplay(cfg['display']); d.test_pattern(); import time; time.sleep(5)"
```

### 2. Audio Input Test (Low-Level)
Verify the I2S mic capture path is working:
```bash
python3 -c "from audio_input import AudioInput; import yaml; cfg = yaml.safe_load(open('config.yaml')); a = AudioInput(cfg['audio']); a.start(); import time; time.sleep(2); print(f'Level: {a.get_input_level()}')"
```

### 3. Audio Input Test (High-Power)
Connect audio source and check levels:
```bash
# Record and check audio level
arecord -D plughw:1,0 -d 5 -f cd test.wav
aplay test.wav
```

### 4. Full System Test
Run the complete visualizer:
```bash
sudo python3 fft_visualizer.py
```

---

## Troubleshooting

### LED Matrix not lighting up
- Check 5V power supply connection
- Verify ribbon cable orientation
- Check GPIO mapping in config.yaml
- Ensure HAT is properly seated on GPIO pins

### No audio input
- Verify I2C devices: `i2cdetect -y 1` (OLED/encoder/RTC)
- Check capture devices: `arecord -l`
- For I2S mic: verify I2S/PCM is enabled and the correct overlay is loaded
- Verify `audio.low_level.device`, `channels`, and `channel_index` in config.yaml

### Menu not responding
- Verify encoder wiring (3.3V/GND/SDA/SCL)
- Confirm the encoder appears in `i2cdetect -y 1` at 0x49
- Verify `menu.input_type: 'i2c_encoder'` and `menu.encoder_i2c_address` in config.yaml

### Poor FFT resolution
- Adjust FFT size in config.yaml (increase for better resolution)
- Check sample rate matches audio input
- Verify audio input signal quality

### Display flickering
- Increase gpio_slowdown in config.yaml
- Check power supply capacity
- Reduce brightness
- Verify all connections are secure
