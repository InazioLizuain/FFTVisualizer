# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FFT Audio Visualizer System                   │
│                         (fft_visualizer.py)                      │
└──────────────┬──────────────────────────┬─────────────┬─────────┘
               │                          │             │
               ▼                          ▼             ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│   Audio Input        │  │   FFT Processor      │  │   Menu System        │
│  (audio_input.py)    │  │ (fft_processor.py)   │  │  (menu_system.py)    │
└──────────┬───────────┘  └──────────┬───────────┘  └──────────┬───────────┘
           │                         │                         │
           │                         │                         │
           ▼                         ▼                         ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│  Audio Data Queue    │  │   LED Display        │  │  OLED + Encoder      │
│   (Threading)        │  │  (led_display.py)    │  │      (I2C)           │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘


```

## Component Details

### 1. Main Application (fft_visualizer.py)

**Responsibilities:**
- System initialization and configuration
- Component orchestration
- Main visualization loop
- Signal handling (graceful shutdown)
- Status management

**Key Methods:**
- `__init__()`: Initialize all components
- `start()`: Start the system
- `stop()`: Graceful shutdown
- `_run_visualization_loop()`: Main processing loop
- `change_input_mode()`: Switch audio input modes

**Data Flow:**
```
Config File → Load Config → Initialize Components → Start Threads → Main Loop
                                                                        ↓
                                                      Get Audio → Process FFT → Update Display
```

---

### 2. Audio Input Module (audio_input.py)

**Architecture:**
```
┌─────────────────────────────────────────────┐
│         Audio Input Manager                 │
├─────────────────────────────────────────────┤
│  Mode Selection:                            │
│  • Low-Level Mode  (I2S Mic)                │
│  • High-Power Mode (USB Audio)              │
└────────────┬────────────────────────────────┘
             │
             ├── Low-Level Input Path ──────────┐
             │   ┌────────────────────────┐     │
             │   │  I2S Mic (SPH0645)     │     │
             │   │  • 48kHz typical       │     │
             │   │  • PCM/I2S interface   │     │
             │   │  • Channel select      │     │
             │   └────────────────────────┘     │
             │            ↓                      │
             │   ┌────────────────────────┐     │
             │   │  Audio Callback        │     │
             │   │  Buffer Management     │     │
             │   └────────────────────────┘     │
             │                                   ↓
             └── High-Power Input Path ────────┐│
                 ┌────────────────────────┐    ││
                 │ USB Audio Interface    │    ││
                 │ • sounddevice library  │    ││
                 │ • 44.1kHz sampling     │    ││
                 │ • Attenuated input     │    ││
                 └────────────────────────┘    ││
                          ↓                     ││
                 ┌────────────────────────┐    ││
                 │  Audio Callback        │    ││
                 │  Buffer Management     │    ││
                 └────────────────────────┘    ││
                                                ││
                          ↓                     ││
             ┌────────────────────────────┐    ││
             │   Audio Data Queue         │←───┘│
             │   • Thread-safe            │←────┘
             │   • Max size: 10 frames    │
             │   • Drop if full           │
             └────────────────────────────┘
                          ↓
             [To FFT Processor]
```

**Threading Model:**
- Main thread: Queue management
- Input thread: Continuous audio capture
- Thread-safe queue for data passing

---

### 3. FFT Processor (fft_processor.py)

**Processing Pipeline:**
```
Audio Input (time domain)
    ↓
┌────────────────────────┐
│  Apply Window Function │ ← Hann Window
│  (Reduce spectral      │
│   leakage)             │
└────────────────────────┘
    ↓
┌────────────────────────┐
│  Compute FFT           │ ← numpy.fft.rfft
│  (Real FFT)            │
└────────────────────────┘
    ↓
┌────────────────────────┐
│  Calculate Magnitude   │ ← abs(fft_result)
│  Convert to dB scale   │   20*log10(mag)
└────────────────────────┘
    ↓
┌────────────────────────┐
│  Map to Display Bins   │ ← Logarithmic/Linear
│  (Frequency → X axis)  │   20Hz-20kHz → 64 bins
└────────────────────────┘
    ↓
┌────────────────────────┐
│  Normalize Spectrum    │ ← Scale to 0-1 range
│  (dB → normalized)     │
└────────────────────────┘
    ↓
┌────────────────────────┐
│  Apply Smoothing       │ ← Exponential moving avg
│  (Temporal filter)     │   smooth = α*prev + (1-α)*curr
└────────────────────────┘
    ↓
┌────────────────────────┐
│  Update Peak Levels    │ ← Peak hold & decay
│  (Peak indicators)     │
└────────────────────────┘
    ↓
┌────────────────────────┐
│  Generate Colors       │ ← Based on color scheme
│  (Spectrum → RGB)      │   4 schemes available
└────────────────────────┘
    ↓
Output: {spectrum, peaks, colors}
    ↓
[To LED Display]
```

**Frequency Bin Mapping:**
```
Logarithmic Scale (Default):
Low frequencies get more bins (better bass resolution)
Example for 64 bins:
Bins 1-16:   20Hz  - 150Hz   (Bass)
Bins 17-32:  150Hz - 800Hz   (Low-Mid)
Bins 33-48:  800Hz - 4kHz    (Mid-High)
Bins 49-64:  4kHz  - 20kHz   (Treble)

Linear Scale:
Equal frequency per bin
Each bin = (20000-20)/64 ≈ 312Hz
```

---

### 4. LED Display (led_display.py)

**Display Pipeline:**
```
FFT Data {spectrum, peaks, colors}
    ↓
┌─────────────────────────────────┐
│  Clear Offscreen Canvas         │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  For each frequency bin (0-63): │
│  ┌─────────────────────────┐    │
│  │ Calculate bar height    │    │
│  │ height = spectrum[i]*64 │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │ Get color RGB values    │    │
│  │ r,g,b = colors[i]       │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │ Draw vertical bar       │    │
│  │ From bottom to height   │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │ Draw peak indicator     │    │
│  │ At peaks[i] position    │    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  Swap Buffers (VSync)           │ ← Double buffering
│  Show canvas on LED matrix      │   Prevents tearing
└─────────────────────────────────┘
```

**Matrix Layout:**
```
   0  1  2  3  ...  61 62 63  (X - Frequency bins)
  ┌──┬──┬──┬──┬───┬──┬──┬──┐
0 │  │  │  │  │...│  │  │  │  ← Top (Max amplitude)
1 │  │  │██│  │   │  │  │  │
2 │  │  │██│  │   │  │██│  │
3 │  │██│██│  │   │  │██│  │
  │  │  │  │  │   │  │  │  │
  │  │  │  │  │   │  │  │  │
63│██│██│██│██│...│██│██│  │  ← Bottom (No signal)
  └──┴──┴──┴──┴───┴──┴──┴──┘
   ^                       ^
  Bass                 Treble
  (20Hz)              (20kHz)
```

---

### 5. Menu System (menu_system.py)

**Menu Architecture:**
```
┌───────────────────────────────────────────┐
│            Menu System                     │
├───────────────────────────────────────────┤
│  Hardware:                                │
│  • 128x64 OLED Display (I2C)              │
│  • I2C Rotary Encoder (rotate + press)    │
├───────────────────────────────────────────┤
│  Menu Structure:                          │
│  Main Menu                                │
│  ├── Input Mode                           │
│  │   ├── Low Level                        │
│  │   ├── High Power                       │
│  │   └── Back                             │
│  ├── Brightness                           │
│  │   ├── 25%                              │
│  │   ├── 50%                              │
│  │   ├── 75%                              │
│  │   ├── 100%                             │
│  │   └── Back                             │
│  ├── Color Scheme                         │
│  │   ├── Rainbow                          │
│  │   ├── Fire                             │
│  │   ├── Ocean                            │
│  │   ├── Matrix                           │
│  │   └── Back                             │
│  └── System Info                          │
└───────────────────────────────────────────┘
```

**Encoder Handling:**
```
I2C Encoder (Seesaw)
    ↓
Poll rotation + switch state
    ↓
Debounce / long-press detection
    ↓
┌─────────────────────────────────┐
│  Encoder Action:                │
│  • Rotate → Prev/Next item      │
│  • Press  → Execute action      │
│  • Long   → Back                │
└─────────────────────────────────┘
    ↓
Update OLED Display
```

**Threading Model:**
```
Main Thread ─────► Menu Update Loop (10Hz)
                   ↓
                   OLED Display Updates

Menu Thread ─────► I2C Encoder Polling
                   ↓
                   Update Menu State
```

---

## Data Flow Diagram

```
┌──────────────┐
│ Audio Source │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│        Audio Input Module            │
│  ┌────────────┐  ┌────────────┐     │
│  │ I2S Mic    │  │ USB Audio  │     │
│  │ (Low-Level)│  │(High-Power)│     │
│  └────────────┘  └────────────┘     │
└──────────┬───────────────────────────┘
           │
           │ Audio Buffer (Queue)
           ▼
┌──────────────────────────────────────┐
│        FFT Processor                 │
│  Window → FFT → dB → Bins → Colors  │
└──────────┬───────────────────────────┘
           │
           │ {spectrum, peaks, colors}
           ▼
┌──────────────────────────────────────┐
│        LED Display Driver            │
│  Canvas → Draw Bars → Swap Buffers  │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│     64x64 RGB LED Matrix             │
│     (Visual Output)                  │
└──────────────────────────────────────┘

         ┌──────────────────────┐
         │   Menu System        │◄─── User Input
         │ (OLED/LCD + Encoder) │     (I2C)
         └──────────┬───────────┘
                    │
                    │ Configuration Changes
                    ▼
         ┌──────────────────────┐
         │  Main Application    │
         │  (Orchestrator)      │
         └──────────────────────┘
```

---

## Threading Model

```
┌────────────────────────────────────────────────────────────┐
│                     Main Thread                             │
│  • Configuration loading                                    │
│  • Component initialization                                 │
│  • Main visualization loop:                                 │
│    - Get audio data from queue                             │
│    - Process FFT                                           │
│    - Update LED display                                    │
│  • Signal handling (shutdown)                              │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│              Audio Input Thread (Daemon)                    │
│  • Continuous audio capture                                │
│  • Mode-specific input (I2S mic or USB)                    │
│  • Buffer to queue                                         │
│  • Non-blocking queue put                                  │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│              Menu System Thread (Daemon)                    │
│  • OLED display updates (10Hz)                             │
│  • Menu rendering                                          │
│  • Status display                                          │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│              Menu Input Polling                             │
│  • I2C rotary encoder rotation/press                         │
│  • Debouncing / long-press handling                          │
└────────────────────────────────────────────────────────────┘

Synchronization:
• Audio Queue: Thread-safe queue.Queue (maxsize=10)
• Menu State: Protected by threading and atomic operations
• Configuration: Read-only after initialization (safe)
```

---

## Hardware Interface Map

```
Raspberry Pi 4 GPIO Connections:
┌─────────────────────────────────────────┐
│  GPIO 2  (SDA)  → I2C Data             │ ← OLED + Encoder + RTC
│  GPIO 3  (SCL)  → I2C Clock            │
│                                         │
│  GPIO 18        → PCM/I2S BCLK          │ ← I2S Mic
│  GPIO 19        → PCM/I2S LRCLK (FS)    │
│  GPIO 20        → PCM/I2S DIN           │
│                                         │
│  GPIO 17-27     → RGB Matrix HAT       │ ← LED Matrix
│  (Multiple)       (via HAT)            │
└─────────────────────────────────────────┘

Power:
• 5V 4A → RGB Matrix HAT → LED Matrix
• 5V    → Raspberry Pi (from HAT or separate)
• 3.3V  → OLED, Encoder (from Pi)

I2C Bus:
• OLED Display   (Address: 0x3C or 0x3D)
• I2C Encoder    (Address: 0x49)
• RTC on HAT     (Address: 0x68)

USB:
• USB Audio Interface (enumerated device)
```

---

## Performance Characteristics

### Latency Breakdown
```
Audio Input:     ~23ms (1024 samples @ 44.1kHz)
FFT Processing:  ~5ms  (2048-point FFT)
Display Update:  ~15ms (LED matrix refresh)
Menu Update:     ~100ms (10Hz, non-blocking)
────────────────────────────────────────────
Total Latency:   ~50ms (audio to visual)
```

### CPU Utilization (Raspberry Pi 4)
```
Component               CPU Usage
─────────────────────────────────
Audio Input Thread      5-10%
FFT Processing          20-30%
LED Display Update      15-20%
Menu System             1-2%
────────────────────────────────
Total                   40-60%
```

### Memory Usage
```
Component               Memory
─────────────────────────────────
Python Runtime          30 MB
NumPy/SciPy            15 MB
Audio Buffers          5 MB
Display Buffers        2 MB
Menu System            1 MB
────────────────────────────────
Total                  ~50 MB
Peak                   ~100 MB
```

---

## Configuration Flow

```
config.yaml
    ↓
YAML Parser
    ↓
Configuration Dictionary
    ↓
    ├─► Audio Config    → AudioInput
    ├─► Display Config  → LEDDisplay
    ├─► Viz Config      → FFTProcessor
    ├─► Menu Config     → MenuSystem
    └─► System Config   → Logging, etc.
```

---

## Error Handling Strategy

```
┌─────────────────────────────────────────┐
│         Exception Hierarchy              │
├─────────────────────────────────────────┤
│  System Level:                          │
│  • Configuration errors → Exit          │
│  • Hardware init fails  → Log & Disable │
│                                         │
│  Component Level:                       │
│  • Audio input error    → Skip frame    │
│  • FFT processing error → Use previous  │
│  • Display error        → Log & retry   │
│  • Menu error           → Disable menu  │
│                                         │
│  Graceful Degradation:                  │
│  • Missing hardware     → Mock/disable  │
│  • Optional features    → Continue      │
└─────────────────────────────────────────┘
```

---

## Deployment Architecture

```
Raspberry Pi 4 System
    │
    ├─► Operating System: Raspberry Pi OS
    │
    ├─► System Services:
    │   ├─► systemd (init system)
    │   ├─► I2C service (hardware bus)
    │   └─► ALSA (audio system)
    │
    ├─► FFT Visualizer Service
    │   ├─► systemd unit: fft-visualizer.service
    │   ├─► Working Directory: /home/pi/FFTVisualizer
    │   ├─► Log File: /var/log/fft_visualizer.log
    │   └─► Auto-restart on failure
    │
    └─► Configuration
        ├─► config.yaml (application settings)
        └─► /boot/config.txt (hardware settings)
```

---

## Security Considerations

1. **Service Execution**
   - Runs as root (required for GPIO/LED matrix access)
   - Limited by systemd resource constraints
   - NoNewPrivileges=true

2. **Input Validation**
   - Configuration file validation
   - Audio buffer bounds checking
   - GPIO pin validation

3. **Resource Limits**
   - CPU quota: 80%
   - Memory limit: 512MB
   - Private tmp directory

4. **Network Isolation**
   - No network access required
   - No remote API
   - Local-only operation

---

## Extensibility Points

1. **New Input Modes**
   - Add to AudioInput class
   - Implement _init_xxx_input() method
   - Add configuration section

2. **New Color Schemes**
   - Add to FFTProcessor._generate_colors()
   - Update configuration options
   - Add to menu system

3. **Alternative Displays**
   - Implement display interface
   - Inherit from LEDDisplay base
   - Plug into main application

4. **Additional Menu Items**
   - Define in MenuSystem._define_menus()
   - Implement action handlers
   - Update LCD layout if needed

---

This architecture provides a robust, maintainable, and extensible foundation for the FFT Audio Visualizer system.
