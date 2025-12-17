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

#### For Low-Level Signals (10mV-1V)
5. **ADS1115 16-Bit ADC**
   - 4-channel, 16-bit resolution
   - I2C interface
   - Programmable gain amplifier (PGA)
   - Adafruit Product ID: 1085 or compatible

6. **Input Protection Circuit Components:**
   - 1x Voltage divider resistors (10kΩ and 1kΩ)
   - 1x Capacitor 10µF (DC blocking)
   - 1x Op-amp (optional): TL072 or similar for signal conditioning
   - 2x Zener diodes 3.3V (input protection)
   - BNC or 3.5mm jack connector

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
9. **Character LCD 20x4 with I2C backpack** OR **128x64 OLED Display**
   - For menu system and settings display
   - I2C interface preferred for easy connection
   - Options:
     - HD44780-compatible 20x4 LCD (recommended)
     - SSD1306 128x64 OLED display

10. **Navigation Buttons (4x)**
    - Tactile push buttons
    - 10kΩ pull-up resistors (or use internal pull-ups)
    - Labels: UP, DOWN, SELECT, BACK

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

### Low-Level Audio Input Circuit (10mV-1V)

```
Audio Signal Input (BNC/3.5mm jack)
    |
    +--- [10µF Cap] --- [10kΩ] ---+--- To ADS1115 A0
    |                              |
    |                          [1kΩ] (Voltage divider)
    |                              |
    +--- [3.3V Zener] -----------GND
    |
   GND

ADS1115 Connections:
- VDD  -> Raspberry Pi 3.3V
- GND  -> Raspberry Pi GND
- SCL  -> Raspberry Pi SCL (GPIO 3)
- SDA  -> Raspberry Pi SDA (GPIO 2)
- A0   -> Signal input (as shown above)
```

**Notes:**
- The 10µF capacitor blocks DC component
- Voltage divider scales signal to ADC range
- Zener diodes protect ADC from overvoltage
- ADS1115 has programmable gain for fine-tuning

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

### Button Connections

```
Each button connects between GPIO pin and GND:

Button UP     -> GPIO 5  -> GND (with internal pull-up)
Button DOWN   -> GPIO 6  -> GND (with internal pull-up)
Button SELECT -> GPIO 13 -> GND (with internal pull-up)
Button BACK   -> GPIO 19 -> GND (with internal pull-up)
```

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
1. Build low-level input circuit on breadboard or PCB
2. Build high-power attenuator circuit (use proper insulation!)
3. Test circuits with multimeter before connecting to Pi

### Step 5: Connect ADC (for low-level input)
1. Connect ADS1115 to Raspberry Pi I2C pins
2. Connect audio input circuit to ADS1115 channel A0
3. Verify I2C connection: `i2cdetect -y 1`

### Step 6: Connect USB Audio (for high-power input)
1. Connect USB audio interface to Raspberry Pi
2. Connect attenuator circuit to audio interface line input
3. Verify device: `arecord -l`

### Step 7: Connect LCD Display
1. Connect LCD according to pin diagram above
2. Test display with simple Python script
3. Adjust contrast potentiometer if using raw LCD

### Step 8: Connect Navigation Buttons
1. Solder buttons to wires with appropriate length
2. Connect to GPIO pins as specified
3. Mount buttons in accessible locations on enclosure

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
Use a signal generator to inject 100Hz, 100mV sine wave:
```bash
# Monitor ADC input
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
- Verify I2C devices: `i2cdetect -y 1`
- Check USB audio: `arecord -l`
- Verify ADC connections and configuration
- Test audio input circuit with multimeter

### Menu not responding
- Check button connections
- Verify GPIO pin assignments in config.yaml
- Test buttons individually with GPIO test script

### Poor FFT resolution
- Adjust FFT size in config.yaml (increase for better resolution)
- Check sample rate matches audio input
- Verify audio input signal quality

### Display flickering
- Increase gpio_slowdown in config.yaml
- Check power supply capacity
- Reduce brightness
- Verify all connections are secure
