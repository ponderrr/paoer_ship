# src/hardware/gpio_rpi.py
import RPi.GPIO as GPIO
import time
from .gpio_interface import GPIOInterface

class GPIORPI(GPIOInterface):
    def __init__(self):
        # Define GPIO pins for buttons
        self.PIN_UP = 17    # Pin 11
        self.PIN_DOWN = 27  # Pin 13
        self.PIN_LEFT = 22  # Pin 15
        self.PIN_RIGHT = 23 # Pin 16
        self.PIN_FIRE = 24  # Pin 18
        self.PIN_MODE = 25  # Pin 22
        
        # Button state variables with debounce protection
        self.button_states = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'fire': False,
            'mode': False
        }
        
        # Debounce time in seconds
        self.debounce_time = 0.15
        self.last_press_time = {
            'up': 0,
            'down': 0,
            'left': 0,
            'right': 0,
            'fire': 0,
            'mode': 0
        }

    def setup(self):
        """Initialize GPIO pins for button input"""
        # Set GPIO mode
        GPIO.setmode(GPIO.BCM)
        
        # Set up input pins with pull-up resistors
        GPIO.setup(self.PIN_UP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.PIN_DOWN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.PIN_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.PIN_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.PIN_FIRE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.PIN_MODE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        print("GPIO pins initialized for button input")

    def cleanup(self):
        """Clean up GPIO resources when no longer needed"""
        GPIO.cleanup()
        print("GPIO resources cleaned up")
    
    def get_button_states(self):
        """
        Reads the current state of all buttons with debounce protection
        
        Returns:
            dict: Dictionary with debounced button states
        """
        current_time = time.time()
        
        # Check each button and update states with debounce
        pin_button_map = {
            self.PIN_UP: 'up',
            self.PIN_DOWN: 'down',
            self.PIN_LEFT: 'left',
            self.PIN_RIGHT: 'right',
            self.PIN_FIRE: 'fire',
            self.PIN_MODE: 'mode'
        }
        
        for pin, button_name in pin_button_map.items():
            # Input is active LOW (when button pressed, input is LOW/0)
            button_pressed = not GPIO.input(pin)
            
            if button_pressed and not self.button_states[button_name]:
                # Button was just pressed
                if current_time - self.last_press_time[button_name] > self.debounce_time:
                    self.button_states[button_name] = True
                    self.last_press_time[button_name] = current_time
            
            elif not button_pressed:
                # Button was released
                self.button_states[button_name] = False
        
        return self.button_states.copy()