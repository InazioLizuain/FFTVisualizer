#!/usr/bin/env python3
"""
Menu System Module
Handles menu display (character LCD or OLED) and navigation (GPIO buttons or I2C encoder)
"""

import logging
import threading
import time
from typing import Optional

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None
    logging.warning("RPi.GPIO not available, menu buttons disabled")

try:
    from RPLCD.gpio import CharLCD
except ImportError:
    CharLCD = None
    logging.warning("RPLCD not available, character LCD disabled")

try:
    import board
    import busio
except ImportError:
    board = None
    busio = None

try:
    import adafruit_ssd1306
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    adafruit_ssd1306 = None
    Image = None
    ImageDraw = None
    ImageFont = None

try:
    from adafruit_seesaw.seesaw import Seesaw
    from adafruit_seesaw.rotaryio import IncrementalEncoder
    from adafruit_seesaw.digitalio import DigitalIO
except ImportError:
    Seesaw = None
    IncrementalEncoder = None
    DigitalIO = None


class MenuSystem:
    """Menu system with LCD display and button navigation"""
    
    def __init__(self, config: dict, visualizer):
        """Initialize menu system"""
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.visualizer = visualizer
        
        self.running = False
        self.menu_thread = None
        
        # Menu state
        self.current_menu = 'main'
        self.current_item = 0
        self.in_submenu = False
        
        # Define menu structure
        self._define_menus()
        
        # Initialize hardware
        self._init_display()
        self._init_input()
        
        self.logger.info("Menu system initialized")
    
    def _define_menus(self):
        """Define menu structure"""
        self.menus = {
            'main': {
                'title': 'FFT Visualizer',
                'items': [
                    {'label': 'Input Mode', 'action': 'input_mode_menu'},
                    {'label': 'Brightness', 'action': 'brightness_menu'},
                    {'label': 'Color Scheme', 'action': 'color_menu'},
                    {'label': 'System Info', 'action': 'system_info'},
                ]
            },
            'input_mode_menu': {
                'title': 'Input Mode',
                'items': [
                    {'label': 'Low Level', 'action': self._set_low_level_mode},
                    {'label': 'High Power', 'action': self._set_high_power_mode},
                    {'label': 'Back', 'action': 'main'},
                ]
            },
            'brightness_menu': {
                'title': 'Brightness',
                'items': [
                    {'label': '25%', 'action': lambda: self.visualizer.set_brightness(25)},
                    {'label': '50%', 'action': lambda: self.visualizer.set_brightness(50)},
                    {'label': '75%', 'action': lambda: self.visualizer.set_brightness(75)},
                    {'label': '100%', 'action': lambda: self.visualizer.set_brightness(100)},
                    {'label': 'Back', 'action': 'main'},
                ]
            },
            'color_menu': {
                'title': 'Color Scheme',
                'items': [
                    {'label': 'Rainbow', 'action': lambda: self.visualizer.set_color_scheme('rainbow')},
                    {'label': 'Fire', 'action': lambda: self.visualizer.set_color_scheme('fire')},
                    {'label': 'Ocean', 'action': lambda: self.visualizer.set_color_scheme('ocean')},
                    {'label': 'Matrix', 'action': lambda: self.visualizer.set_color_scheme('matrix')},
                    {'label': 'Back', 'action': 'main'},
                ]
            },
        }
    
    def _init_display(self):
        """Initialize menu display (character LCD or OLED)."""
        self.display_type = self.config.get('display_type', 'character')

        self.lcd = None
        self.oled = None
        self._oled_image = None
        self._oled_draw = None
        self._oled_font = None
        self._i2c = None

        def get_i2c():
            if self._i2c is None:
                self._i2c = busio.I2C(board.SCL, board.SDA)
            return self._i2c

        if self.display_type == 'character':
            if CharLCD is None or GPIO is None:
                self.logger.warning("Character LCD requested but dependencies are missing")
                return

            try:
                self.lcd = CharLCD(
                    pin_rs=self.config['lcd_rs'],
                    pin_e=self.config['lcd_en'],
                    pins_data=[
                        self.config['lcd_d4'],
                        self.config['lcd_d5'],
                        self.config['lcd_d6'],
                        self.config['lcd_d7']
                    ],
                    numbering_mode=GPIO.BCM,
                    cols=self.config['lcd_columns'],
                    rows=self.config['lcd_rows'],
                    dotsize=8
                )

                self.lcd.clear()
                self.lcd.write_string('FFT Visualizer\nInitializing...')
                self.logger.info("Character LCD initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize character LCD: {e}")
                self.lcd = None

        elif self.display_type == 'oled':
            if adafruit_ssd1306 is None or Image is None or board is None or busio is None:
                self.logger.warning("OLED requested but dependencies are missing")
                return

            try:
                width = int(self.config.get('oled_width', 128))
                height = int(self.config.get('oled_height', 64))
                addr = int(self.config.get('oled_i2c_address', 0x3C))

                i2c = get_i2c()
                self.oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=addr)

                self._oled_image = Image.new('1', (width, height))
                self._oled_draw = ImageDraw.Draw(self._oled_image)
                self._oled_font = ImageFont.load_default()

                self._oled_clear()
                self._oled_write_lines(["FFT Visualizer", "Initializing..."])
                self.logger.info("OLED display initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize OLED display: {e}")
                self.oled = None

        else:
            self.logger.warning(f"Unknown menu display_type: {self.display_type}")

    def _init_input(self):
        """Initialize menu input (GPIO buttons or I2C encoder)."""
        self.input_type = self.config.get('input_type', 'buttons')

        self._encoder = None
        self._encoder_button = None
        self._encoder_last_pos = 0
        self._encoder_pressed_at = None
        self._encoder_last_button_state = True

        if self.input_type == 'buttons':
            self._init_buttons_gpio()
        elif self.input_type == 'i2c_encoder':
            self._init_encoder_i2c()
        else:
            self.logger.warning(f"Unknown menu input_type: {self.input_type}")

    def _init_buttons_gpio(self):
        """Initialize navigation buttons using GPIO."""
        if GPIO is None:
            self.logger.warning("GPIO not available, buttons disabled")
            return

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            self.button_pins = {
                'up': self.config['button_up'],
                'down': self.config['button_down'],
                'select': self.config['button_select'],
                'back': self.config['button_back']
            }

            for pin in self.button_pins.values():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            GPIO.add_event_detect(
                self.button_pins['up'],
                GPIO.FALLING,
                callback=self._on_button_up,
                bouncetime=200
            )
            GPIO.add_event_detect(
                self.button_pins['down'],
                GPIO.FALLING,
                callback=self._on_button_down,
                bouncetime=200
            )
            GPIO.add_event_detect(
                self.button_pins['select'],
                GPIO.FALLING,
                callback=self._on_button_select,
                bouncetime=200
            )
            GPIO.add_event_detect(
                self.button_pins['back'],
                GPIO.FALLING,
                callback=self._on_button_back,
                bouncetime=200
            )

            self.logger.info("Navigation buttons (GPIO) initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize buttons: {e}")

    def _init_encoder_i2c(self):
        """Initialize I2C rotary encoder (Seesaw-based)."""
        if Seesaw is None or IncrementalEncoder is None or DigitalIO is None:
            self.logger.warning("Seesaw libraries not available, I2C encoder disabled")
            return
        if board is None or busio is None:
            self.logger.warning("board/busio not available, I2C encoder disabled")
            return

        try:
            addr = int(self.config.get('encoder_i2c_address', 0x49))
            a_pin = int(self.config.get('encoder_a_pin', 18))
            b_pin = int(self.config.get('encoder_b_pin', 19))
            sw_pin = int(self.config.get('encoder_switch_pin', 24))

            if getattr(self, '_i2c', None) is None:
                self._i2c = busio.I2C(board.SCL, board.SDA)
            seesaw = Seesaw(self._i2c, addr=addr)
            self._encoder = IncrementalEncoder(seesaw, a_pin, b_pin)

            self._encoder_button = DigitalIO(seesaw, sw_pin)
            self._encoder_button.switch_to_input(pull=True)

            self._encoder_last_pos = self._encoder.position
            self._encoder_last_button_state = self._encoder_button.value

            self.logger.info(f"I2C encoder initialized (addr=0x{addr:02X})")
        except Exception as e:
            self.logger.error(f"Failed to initialize I2C encoder: {e}")
            self._encoder = None
            self._encoder_button = None
    
    def start(self):
        """Start menu system"""
        if self.running:
            return
        
        self.running = True
        self.menu_thread = threading.Thread(target=self._menu_loop, daemon=True)
        self.menu_thread.start()
        self.logger.info("Menu system started")
    
    def stop(self):
        """Stop menu system"""
        self.running = False
        if self.menu_thread:
            self.menu_thread.join(timeout=2.0)
        
        if self.display_type == 'character' and self.lcd:
            self.lcd.clear()
            self.lcd.write_string('Shutting down...')
        elif self.display_type == 'oled' and self.oled:
            self._oled_write_lines(["Shutting down..."])
        
        if self.input_type == 'buttons' and GPIO:
            GPIO.cleanup()
        
        self.logger.info("Menu system stopped")
    
    def _menu_loop(self):
        """Main menu loop - updates display"""
        while self.running:
            self._poll_input()
            self._update_display()
            time.sleep(0.1)  # Update display at 10Hz

    def _poll_input(self):
        """Poll non-interrupt driven inputs (e.g., I2C encoder)."""
        if self.input_type != 'i2c_encoder' or self._encoder is None or self._encoder_button is None:
            return

        # Encoder rotation
        try:
            pos = self._encoder.position
            delta = pos - self._encoder_last_pos
            if delta != 0:
                direction = int(self.config.get('encoder_direction', 1))
                steps = delta * direction
                if steps > 0:
                    for _ in range(abs(steps)):
                        self._on_button_down(None)
                else:
                    for _ in range(abs(steps)):
                        self._on_button_up(None)
                self._encoder_last_pos = pos
        except Exception as e:
            self.logger.debug(f"Encoder read error: {e}")

        # Encoder push button (short press = select, long press = back)
        try:
            is_released = self._encoder_button.value  # pull-up => True means released

            if (self._encoder_last_button_state is True) and (is_released is False):
                # pressed
                self._encoder_pressed_at = time.time()

            if (self._encoder_last_button_state is False) and (is_released is True):
                # released
                pressed_at = self._encoder_pressed_at
                self._encoder_pressed_at = None
                if pressed_at is not None:
                    held_ms = int((time.time() - pressed_at) * 1000)
                    long_press_ms = int(self.config.get('encoder_long_press_ms', 800))
                    if held_ms >= long_press_ms:
                        self._on_button_back(None)
                    else:
                        self._on_button_select(None)

            self._encoder_last_button_state = is_released
        except Exception as e:
            self.logger.debug(f"Encoder button read error: {e}")
    
    def _update_display(self):
        """Update LCD display with current menu"""
        if self.display_type == 'character':
            if self.lcd is None:
                return
        elif self.display_type == 'oled':
            if self.oled is None:
                return
        else:
            return
        
        menu = self.menus[self.current_menu]
        items = menu['items']
        
        if self.display_type == 'character':
            # Clear display
            self.lcd.clear()

            # Display menu title
            self.lcd.write_string(menu['title'])

            # Display current menu item (with indicator)
            if len(items) > 0:
                item = items[self.current_item]
                self.lcd.cursor_pos = (1, 0)  # Second line
                self.lcd.write_string(f"> {item['label']}")

                # Show additional items if LCD has more rows
                if self.config['lcd_rows'] >= 3 and len(items) > 1:
                    next_item = (self.current_item + 1) % len(items)
                    self.lcd.cursor_pos = (2, 0)  # Third line
                    self.lcd.write_string(f"  {items[next_item]['label']}")

                if self.config['lcd_rows'] >= 4 and len(items) > 2:
                    next_next_item = (self.current_item + 2) % len(items)
                    self.lcd.cursor_pos = (3, 0)  # Fourth line
                    self.lcd.write_string(f"  {items[next_next_item]['label']}")

        elif self.display_type == 'oled':
            lines = [menu['title']]
            if len(items) > 0:
                item = items[self.current_item]
                lines.append(f"> {item['label']}")
                # Show a couple of upcoming items
                if len(items) > 1:
                    next_item = (self.current_item + 1) % len(items)
                    lines.append(f"  {items[next_item]['label']}")
                if len(items) > 2:
                    next_next_item = (self.current_item + 2) % len(items)
                    lines.append(f"  {items[next_next_item]['label']}")
            self._oled_write_lines(lines)

    def _oled_clear(self):
        if self.oled is None or self._oled_draw is None:
            return
        self._oled_draw.rectangle((0, 0, self.oled.width, self.oled.height), outline=0, fill=0)
        self.oled.image(self._oled_image)
        self.oled.show()

    def _oled_write_lines(self, lines):
        if self.oled is None or self._oled_draw is None or self._oled_font is None:
            return

        self._oled_draw.rectangle((0, 0, self.oled.width, self.oled.height), outline=0, fill=0)
        y = 0
        line_height = 10
        for line in lines:
            if y + line_height > self.oled.height:
                break
            self._oled_draw.text((0, y), str(line), font=self._oled_font, fill=255)
            y += line_height

        self.oled.image(self._oled_image)
        self.oled.show()
    
    def _on_button_up(self, channel):
        """Handle UP button press"""
        menu = self.menus[self.current_menu]
        items = menu['items']
        
        if len(items) > 0:
            self.current_item = (self.current_item - 1) % len(items)
            self.logger.debug(f"Menu UP: item {self.current_item}")
    
    def _on_button_down(self, channel):
        """Handle DOWN button press"""
        menu = self.menus[self.current_menu]
        items = menu['items']
        
        if len(items) > 0:
            self.current_item = (self.current_item + 1) % len(items)
            self.logger.debug(f"Menu DOWN: item {self.current_item}")
    
    def _on_button_select(self, channel):
        """Handle SELECT button press"""
        menu = self.menus[self.current_menu]
        items = menu['items']
        
        if len(items) > 0:
            action = items[self.current_item]['action']
            self.logger.debug(f"Menu SELECT: {action}")
            
            if isinstance(action, str):
                # Navigate to another menu
                if action in self.menus:
                    self.current_menu = action
                    self.current_item = 0
                elif action == 'system_info':
                    self._show_system_info()
            elif callable(action):
                # Execute action
                action()
                # Show confirmation
                if self.lcd:
                    self.lcd.clear()
                    self.lcd.write_string('Setting changed!')
                    time.sleep(1)
    
    def _on_button_back(self, channel):
        """Handle BACK button press"""
        self.logger.debug("Menu BACK")
        
        # Go back to main menu
        if self.current_menu != 'main':
            self.current_menu = 'main'
            self.current_item = 0
    
    def _set_low_level_mode(self):
        """Set input mode to low level"""
        self.visualizer.change_input_mode('low_level')
        if self.display_type == 'character' and self.lcd:
            self.lcd.clear()
            self.lcd.write_string('Mode: Low Level\nI2S mic input')
            time.sleep(2)
        elif self.display_type == 'oled' and self.oled:
            self._oled_write_lines(["Mode: Low Level", "I2S mic input"])
            time.sleep(2)
    
    def _set_high_power_mode(self):
        """Set input mode to high power"""
        self.visualizer.change_input_mode('high_power')
        if self.display_type == 'character' and self.lcd:
            self.lcd.clear()
            self.lcd.write_string('Mode: High Power\nUSB audio input')
            time.sleep(2)
        elif self.display_type == 'oled' and self.oled:
            self._oled_write_lines(["Mode: High Power", "USB audio input"])
            time.sleep(2)
    
    def _show_system_info(self):
        """Display system information"""
        if self.display_type == 'character' and self.lcd is None:
            return
        if self.display_type == 'oled' and self.oled is None:
            return
        
        status = self.visualizer.get_status()
        
        if self.display_type == 'character':
            self.lcd.clear()
            self.lcd.write_string(f"Mode:{status['input_mode'][:8]}\n")
            self.lcd.cursor_pos = (1, 0)
            self.lcd.write_string(f"Bright:{status['brightness']}%\n")

            if self.config['lcd_rows'] >= 3:
                self.lcd.cursor_pos = (2, 0)
                self.lcd.write_string(f"Scheme:{status['color_scheme'][:8]}")

            time.sleep(3)
        elif self.display_type == 'oled':
            self._oled_write_lines([
                f"Mode: {status['input_mode']}",
                f"Bright: {status['brightness']}%",
                f"Scheme: {status['color_scheme']}",
            ])
            time.sleep(3)
