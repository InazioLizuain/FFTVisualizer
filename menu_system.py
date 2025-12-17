#!/usr/bin/env python3
"""
Menu System Module
Handles LCD display and button navigation for system control
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
        self._init_lcd()
        self._init_buttons()
        
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
    
    def _init_lcd(self):
        """Initialize LCD display"""
        self.lcd = None
        
        display_type = self.config['display_type']
        
        if display_type == 'character' and CharLCD is not None:
            try:
                # Initialize character LCD
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
        
        # TODO: Add OLED display support if needed
    
    def _init_buttons(self):
        """Initialize navigation buttons"""
        if GPIO is None:
            self.logger.warning("GPIO not available, buttons disabled")
            return
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup button pins with pull-up resistors
            self.button_pins = {
                'up': self.config['button_up'],
                'down': self.config['button_down'],
                'select': self.config['button_select'],
                'back': self.config['button_back']
            }
            
            for pin in self.button_pins.values():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Add event detection for buttons
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
            
            self.logger.info("Navigation buttons initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize buttons: {e}")
    
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
        
        if self.lcd:
            self.lcd.clear()
            self.lcd.write_string('Shutting down...')
        
        if GPIO:
            GPIO.cleanup()
        
        self.logger.info("Menu system stopped")
    
    def _menu_loop(self):
        """Main menu loop - updates display"""
        while self.running:
            self._update_display()
            time.sleep(0.1)  # Update display at 10Hz
    
    def _update_display(self):
        """Update LCD display with current menu"""
        if self.lcd is None:
            return
        
        menu = self.menus[self.current_menu]
        items = menu['items']
        
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
        if self.lcd:
            self.lcd.clear()
            self.lcd.write_string('Mode: Low Level\n10mV-1V input')
            time.sleep(2)
    
    def _set_high_power_mode(self):
        """Set input mode to high power"""
        self.visualizer.change_input_mode('high_power')
        if self.lcd:
            self.lcd.clear()
            self.lcd.write_string('Mode: High Power\n40W audio input')
            time.sleep(2)
    
    def _show_system_info(self):
        """Display system information"""
        if self.lcd is None:
            return
        
        status = self.visualizer.get_status()
        
        self.lcd.clear()
        self.lcd.write_string(f"Mode:{status['input_mode'][:8]}\n")
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(f"Bright:{status['brightness']}%\n")
        
        if self.config['lcd_rows'] >= 3:
            self.lcd.cursor_pos = (2, 0)
            self.lcd.write_string(f"Scheme:{status['color_scheme'][:8]}")
        
        time.sleep(3)
