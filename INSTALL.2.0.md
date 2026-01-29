# INSTALL 2.0 — Bring-up por módulos (OLED + Encoder + Audio + Matriz)

Este documento está pensado para **hacer pruebas pequeñas e incrementales** y validar el hardware **por módulos**, antes de ejecutar el visualizador completo.

Objetivo: poder decir “el bus I2C funciona”, “la OLED funciona”, “el encoder funciona”, “la captura de audio funciona (USB)”, “la captura I2S funciona”, y finalmente “todo junto funciona”.

---

## Hardware objetivo (según HARDWARE.md)

- Raspberry Pi 4
- Adafruit RGB Matrix HAT + RTC (ID 2345)
- Panel RGB 64x64 (5V)
- OLED I2C 128x64 (SSD1306 compatible, normalmente `0x3C`)
- Encoder I2C Adafruit Seesaw (`0x49`)
- Audio:
  - **High-power**: USB audio interface (line-in)
  - **Low-level**: micrófono I2S SPH0645 (48kHz típico; a veces 2 canales)

---

## Antes de empezar (muy importante)

### 0) Asegura que estás en la rama correcta en la Raspberry

En la Raspberry:

```bash
cd ~/FFTVisualizer
git fetch --prune
git switch WIP || git checkout -b WIP origin/WIP
git pull --ff-only
```

### 1) Estrategia de Python (por qué salían warnings al ejecutar con sudo)

El visualizador se ejecuta con `sudo` (por la matriz RGB). **Si instalas dependencias en un venv o con `--user`, `sudo python3` puede NO verlas**.

Elige UNA estrategia y sé consistente:

- **Estrategia A (recomendada para simplificar): instalar dependencias en el Python del sistema**
  ```bash
  cd ~/FFTVisualizer
  sudo pip3 install -r requirements.txt
  ```

- **Estrategia B (venv):**
  - Creas venv y instalas ahí.
  - Ejecutas el visualizador con el python del venv:
    ```bash
    cd ~/FFTVisualizer
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # Para la matriz necesitas sudo, pero usando el python del venv:
    sudo ./venv/bin/python fft_visualizer.py
    ```

---

## Checklist rápida de “base del sistema” (idempotente)

En la Raspberry:

```bash
sudo apt-get update
sudo apt-get install -y git python3-pip python3-dev python3-setuptools \
  i2c-tools python3-smbus \
  portaudio19-dev libasound2-dev \
  build-essential autoconf libtool pkg-config \
  libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev
```

Activa I2C (si no lo hiciste):

```bash
sudo raspi-config
# Interface Options -> I2C -> Enable
sudo reboot
```

---

## Paso A — Verificar bus I2C (sin depender de Python)

Conecta (solo) lo I2C: OLED + encoder + (el RTC del HAT aparece también). Luego:

```bash
i2cdetect -y 1
```

Esperado:
- OLED: `0x3C` (a veces `0x3D`)
- Encoder: `0x49`
- RTC del HAT: `0x68`

Si no aparece algo:
- Revisa SDA/SCL (GPIO2/GPIO3), masa común y que OLED/encoder vayan a **3.3V**.

---

## Paso B — Probar OLED (SSD1306) con un script mínimo

### 1) Instala (si falta)

Si tu prueba anterior te dio warnings de “OLED dependencies missing”, instala:

```bash
cd ~/FFTVisualizer
# Si usas estrategia A:
sudo pip3 install adafruit-blinka adafruit-circuitpython-ssd1306 pillow

# Si usas venv:
# source venv/bin/activate
# pip install adafruit-blinka adafruit-circuitpython-ssd1306 pillow
```

### 2) Ejecuta el test

En la Raspberry (desde el repo):

```bash
cd ~/FFTVisualizer
python3 tools/test_oled_ssd1306.py
```

Qué valida:
- Inicialización I2C
- Driver SSD1306
- Dibujo de texto y animación simple

Si tu OLED es SH1106 y no SSD1306:
- Normalmente `adafruit-circuitpython-ssd1306` no funcionará. Tendrás que cambiar a un driver SH1106.

---

## Paso C — Probar encoder I2C (Seesaw) con un script mínimo

### 1) Instala (si falta)

```bash
cd ~/FFTVisualizer
# Estrategia A:
sudo pip3 install adafruit-blinka adafruit-circuitpython-seesaw
```

### 2) Ejecuta el test

```bash
cd ~/FFTVisualizer
python3 tools/test_encoder_seesaw.py
```

Qué valida:
- Lectura de posición al girar
- Lectura del botón al pulsar

---

## Paso D — Probar “Menu UI” (OLED + encoder) sin arrancar audio/matriz

Este test crea un “visualizer fake” (stub) solo para que el menú funcione y puedas navegar:

```bash
cd ~/FFTVisualizer
python3 tools/test_menu_ui_stub.py
```

Qué valida:
- `menu_system.py` + OLED + encoder funcionando conjuntamente
- Navegación por items sin necesidad de audio ni matriz

---

## Paso E — Probar matriz RGB 64x64 (sin audio)

### 1) Verifica que `rpi-rgb-led-matrix` está instalado

```bash
python3 -c "from rgbmatrix import RGBMatrix; print('rgbmatrix OK')"
```

### 2) Ejecuta un demo estable (tu hallazgo)

```bash
cd ~/rpi-rgb-led-matrix/bindings/python/samples
sudo python3 pulsing-brightness.py \
  --led-rows=64 --led-cols=64 --led-chain=1 --led-parallel=1 --led-slowdown-gpio=2
```

Si aparece flicker:
- prueba `--led-slowdown-gpio=3` y reduce `--led-brightness`.

---

## Paso F — Probar audio HIGH-POWER (USB audio interface)

Conecta el USB audio interface. Luego:

### 1) Ver ALSA

```bash
arecord -l
```

### 2) Ver PortAudio (sounddevice)

OJO: el listado puede cambiar entre tu usuario y root.

```bash
cd ~/FFTVisualizer
python3 tools/test_audio_devices.py
sudo python3 tools/test_audio_devices.py
```

### 3) Grabación corta

Elige un índice de entrada válido del listado y prueba:

```bash
cd ~/FFTVisualizer
python3 tools/test_audio_capture_wav.py --seconds 3 --outfile /tmp/test_usb.wav
aplay /tmp/test_usb.wav
```

Si va bien, fija en `config.yaml`:

```yaml
audio:
  high_power:
    device: <indice>
```

---

## Paso G — Probar audio LOW-LEVEL (I2S SPH0645)

### 1) Habilita I2S/PCM

```bash
sudo raspi-config
# Interface Options -> I2S (o Audio) -> Enable
sudo reboot
```

### 2) Asegura overlay del micrófono

Esto depende del breakout y del kernel. El requisito es: **debe aparecer un capture device en `arecord -l`**.

```bash
arecord -l
```

### 3) Grabación ALSA directa (típico 48kHz, 2ch, S32_LE)

Ajusta el `plughw:X,Y` a tu caso:

```bash
arecord -D plughw:2,0 -d 3 -r 48000 -c 2 -f S32_LE /tmp/test_i2s.wav
aplay /tmp/test_i2s.wav
```

### 4) Grabación desde Python (sounddevice)

```bash
cd ~/FFTVisualizer
python3 tools/test_audio_devices.py
python3 tools/test_audio_capture_wav.py --seconds 3 --samplerate 48000 --channels 2 --outfile /tmp/test_i2s_sd.wav
```

Si escuchas audio solo en un canal, en `config.yaml` deja `channels: 2` y cambia:

```yaml
audio:
  low_level:
    channels: 2
    channel_index: 0  # prueba 0 y 1
```

Y fija `audio.low_level.device` al índice correcto (en vez de `default`), especialmente si lo ejecutas con `sudo`.

---

## Paso H — Ejecutar el visualizador completo (cuando TODO esté ok)

Primero asegúrate de que tu `config.yaml` ya tiene los valores de matriz correctos (64x64 + `gpio_slowdown: 2`).

Luego:

```bash
cd ~/FFTVisualizer
sudo python3 fft_visualizer.py
```

Si falla por audio porque aún no está conectado:
- cambia temporalmente `audio.default_mode` al modo que sí tienes disponible, o fija `device` a un índice válido.

---

## Notas rápidas de troubleshooting

- Si `sudo python3 fft_visualizer.py` dice “OLED dependencies missing” pero `python3 ...` no:
  - es el problema de entorno (root vs user). Usa la estrategia A o ejecuta con el python del venv.

- Si el panel parpadea en una fila/columna:
  - asegúrate de `--led-rows/--led-cols` correctos (en tu caso 64/64)
  - sube `gpio_slowdown` a 2–4
  - revisa 5V estable y masa

- Si `sounddevice` falla con `sudo` pero no sin `sudo`:
  - lista devices con `sudo python3 tools/test_audio_devices.py` y fija el índice en `config.yaml`.
