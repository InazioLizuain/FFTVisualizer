# Installation Guide

## Prerequisites

- Raspberry Pi 4 with Raspberry Pi OS (32-bit or 64-bit)
- Internet connection for downloading dependencies
- SSH access or direct terminal access
- Hardware assembled according to HARDWARE.md

---

## Step 1: System Preparation

### Update System
```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get dist-upgrade -y
```

### Enable I2C
```bash
sudo raspi-config
# Navigate to: Interface Options -> I2C -> Enable
# Reboot when prompted
```

### Install System Dependencies
```bash
# Development tools
sudo apt-get install -y git python3-pip python3-dev python3-setuptools

# Audio libraries
sudo apt-get install -y portaudio19-dev python3-pyaudio libasound2-dev

# I2C and GPIO tools
sudo apt-get install -y i2c-tools python3-smbus

# Image processing (for Pillow)
sudo apt-get install -y libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev

# Build tools for RGB matrix library
sudo apt-get install -y build-essential autoconf libtool pkg-config
```

---

## Step 2: Install RGB Matrix Library


The rpi-rgb-led-matrix library (which provides the `rgbmatrix` Python module) is **not installed via pip**. You must compile and install it from source as shown below. If you see errors about `rgbmatrix` when installing Python dependencies, ignore them, as this step handles its installation.

**Tip:** You can comment out or remove the `rgbmatrix` line in `requirements.txt` to avoid pip errors.

The rpi-rgb-led-matrix library needs to be compiled from source:

```bash
# Clone the library
cd ~
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix

# Compile the library
make build-python PYTHON=$(which python3)

# Install Python bindings
sudo make install-python PYTHON=$(which python3)

# Verify installation
python3 -c "from rgbmatrix import RGBMatrix; print('RGB Matrix library installed successfully')"
```

**Note:** If you encounter issues, refer to the [official documentation](https://github.com/hzeller/rpi-rgb-led-matrix).

---

## Step 3: Clone FFT Visualizer Repository

```bash
cd ~
git clone https://github.com/InazioLizuain/FFTVisualizer.git
cd FFTVisualizer
```

---

## Step 4: Install Python Dependencies

### Create Virtual Environment (Optional but Recommended)
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip3 install --upgrade pip
# If you see an error about 'rgbmatrix', ignore it (see note above)
pip3 install -r requirements.txt
```

### Install Additional Hardware Libraries

#### For ADC (ADS1115)
```bash
pip3 install adafruit-circuitpython-ads1x15
```

#### For Character LCD
```bash
pip3 install RPLCD
```

#### For OLED Display (if using OLED instead of LCD)
```bash
pip3 install luma.oled
```

---

## Step 5: Configure the System

### Edit Configuration File
```bash
nano config.yaml
```

Key settings to adjust:
- **Audio input mode:** Set default_mode to 'low_level' or 'high_power'
- **Display settings:** Adjust brightness, hardware_mapping
- **GPIO pins:** Verify button and LCD pin assignments match your wiring
- **Frequency range:** Default is 20-20000 Hz

### Test Configuration
```bash
# Verify YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

---

## Step 6: Hardware Verification

### Test I2C Devices
```bash
# Should show addresses of ADS1115 (0x48) and LCD (if I2C)
i2cdetect -y 1
```

### Test Audio Input
```bash
# List audio devices
arecord -l

# Test recording (for high-power mode)
arecord -D plughw:1,0 -d 3 -f cd test.wav
aplay test.wav
```

### Test LED Matrix
```bash
# Run matrix test from the rpi-rgb-led-matrix examples
cd ~/rpi-rgb-led-matrix/bindings/python/samples
sudo python3 pulsing-brightness.py
```

---

## Step 7: Run FFT Visualizer

### First Run (Manual)
```bash
cd ~/FFTVisualizer

# Run with sudo (required for LED matrix access)
sudo python3 fft_visualizer.py
```

### Check Logs
```bash
# If running, logs appear in:
tail -f /var/log/fft_visualizer.log
```

---

## Step 8: Setup Autostart (Optional)

### Create systemd Service

```bash
sudo nano /etc/systemd/system/fft-visualizer.service
```

Add the following content:

```ini
[Unit]
Description=FFT Audio Visualizer
After=network.target sound.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/pi/FFTVisualizer
ExecStart=/usr/bin/python3 /home/pi/FFTVisualizer/fft_visualizer.py
Restart=on-failure
RestartSec=10s
StandardOutput=append:/var/log/fft_visualizer.log
StandardError=append:/var/log/fft_visualizer.log

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable fft-visualizer.service

# Start service now
sudo systemctl start fft-visualizer.service

# Check status
sudo systemctl status fft-visualizer.service

# View logs
sudo journalctl -u fft-visualizer.service -f
```

### Service Management Commands

```bash
# Stop service
sudo systemctl stop fft-visualizer.service

# Restart service
sudo systemctl restart fft-visualizer.service

# Disable autostart
sudo systemctl disable fft-visualizer.service
```

---

## Step 9: Performance Optimization

### Disable Desktop Environment (for better performance)
```bash
sudo raspi-config
# System Options -> Boot / Auto Login -> Console
```

### Set CPU Governor to Performance
```bash
echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

To make permanent, add to `/etc/rc.local`:
```bash
sudo nano /etc/rc.local
# Add before "exit 0":
echo "performance" | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Increase GPU Memory (if needed)
```bash
sudo raspi-config
# Performance Options -> GPU Memory -> Set to 256
```

### Disable Unnecessary Services
```bash
# Disable Bluetooth if not needed
sudo systemctl disable bluetooth
sudo systemctl stop bluetooth

# Disable WiFi if using Ethernet
sudo systemctl disable wpa_supplicant
```

---

## Step 10: Verify Installation

### Run System Check
```bash
cd ~/FFTVisualizer
python3 -c "
import sys
try:
    import numpy
    import scipy
    import yaml
    from rgbmatrix import RGBMatrix
    print('✓ All required modules installed')
    print('✓ Installation successful!')
except ImportError as e:
    print(f'✗ Missing module: {e}')
    sys.exit(1)
"
```

---

## Troubleshooting

### Permission Issues
If you get permission errors with GPIO or LED matrix:
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Add user to i2c group
sudo usermod -a -G i2c $USER

# Reboot for changes to take effect
sudo reboot
```

### Audio Input Not Working
```bash
# Check if devices are detected
arecord -l
lsusb  # For USB audio

# Test audio input
arecord -D plughw:1,0 -d 5 -f cd -t wav test.wav
```

### I2C Issues
```bash
# Check I2C is enabled
sudo raspi-config
# Interface Options -> I2C -> Enable

# Check I2C devices
i2cdetect -y 1

# Adjust I2C speed if needed (in /boot/config.txt)
echo "dtparam=i2c_arm_baudrate=100000" | sudo tee -a /boot/config.txt
```

### LED Matrix Issues
```bash
# Check cable connections
# Try different gpio_slowdown values in config.yaml (1-4)

# Test with example programs
cd ~/rpi-rgb-led-matrix/bindings/python/samples
sudo python3 simple-square.py
```

### Memory Issues
```bash
# Increase swap size
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=100 to CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

---

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop fft-visualizer.service
sudo systemctl disable fft-visualizer.service
sudo rm /etc/systemd/system/fft-visualizer.service
sudo systemctl daemon-reload

# Remove files
cd ~
rm -rf FFTVisualizer

# Remove dependencies (optional)
pip3 uninstall -r FFTVisualizer/requirements.txt
```

---

## Next Steps

- Read [USAGE.md](USAGE.md) for operating instructions
- Review [HARDWARE.md](HARDWARE.md) for circuit details
- Adjust settings in config.yaml for your specific setup
- Experiment with different color schemes and frequency ranges

## Support

For issues and questions:
- Check the GitHub issues page
- Review the hardware documentation
- Verify all connections and configuration settings
