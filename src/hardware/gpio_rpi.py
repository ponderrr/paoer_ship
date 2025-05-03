import gpiod
import time
from .gpio_interface import GPIOInterface

class GPIORPI(GPIOInterface):
    def __init__(self):
        self.PIN_UP = 17    # Pin 11
        self.PIN_DOWN = 27  # Pin 13
        self.PIN_LEFT = 22  # Pin 15
        self.PIN_RIGHT = 23 # Pin 16
        self.PIN_FIRE = 24  # Pin 18
        self.PIN_MODE = 25  # Pin 22
        self.PIN_ROTATE = 26  # Pin 37 
        
        self.button_states = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'fire': False,
            'mode': False,
            'rotate': False  
        }
        
        self.last_button_raw_states = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'fire': False,
            'mode': False,
            'rotate': False  
        }
        
        self.debounce_time = 0.15
        self.last_press_time = {
            'up': 0,
            'down': 0,
            'left': 0,
            'right': 0,
            'fire': 0,
            'mode': 0,
            'rotate': 0  
        }
        
        self.chip = None
        self.lines = {}

    def setup(self):
        """Initialize GPIO pins for button input"""
        try:
            try:
                self.chip = gpiod.Chip("gpiochip4")  
                print("Using gpiochip4 for Raspberry Pi 5")
            except:
                self.chip = gpiod.Chip("gpiochip0")  
                print("Using gpiochip0 for Raspberry Pi")
            
            pin_button_map = {
                self.PIN_UP: 'up',
                self.PIN_DOWN: 'down',
                self.PIN_LEFT: 'left',
                self.PIN_RIGHT: 'right',
                self.PIN_FIRE: 'fire',
                self.PIN_MODE: 'mode',
                self.PIN_ROTATE: 'rotate'  
            }
            
            for pin, button_name in pin_button_map.items():
                try:
                    line = self.chip.get_line(pin)
                    config = gpiod.line_request()
                    config.consumer = f"paoer-ship-{button_name}"
                    config.request_type = gpiod.line_request.DIRECTION_INPUT
                    line.request(config)
                    self.lines[pin] = line
                except AttributeError:
                    line = self.chip.get_line(pin)
                    line.request(consumer=f"paoer-ship-{button_name}", type=gpiod.LINE_REQ_DIR_IN)
                    self.lines[pin] = line
                
            print("GPIO pins initialized for button input using gpiod")
        except Exception as e:
            print(f"Error setting up GPIO: {e}")
            if self.chip:
                self.chip.close()
                self.chip = None

    def cleanup(self):
        """Clean up GPIO resources when no longer needed"""
        if self.chip:
            self.chip.close()
            self.chip = None
        print("GPIO resources cleaned up")
    
    def get_button_states(self):
        """
        Reads the current state of all buttons with debounce protection
        
        Returns:
            dict: Dictionary with debounced button states
        """
        if not self.chip:
            return self.button_states.copy()
            
        current_time = time.time()
        
        pin_button_map = {
            self.PIN_UP: 'up',
            self.PIN_DOWN: 'down',
            self.PIN_LEFT: 'left',
            self.PIN_RIGHT: 'right',
            self.PIN_FIRE: 'fire',
            self.PIN_MODE: 'mode',
            self.PIN_ROTATE: 'rotate' 
        }
        
        for pin, button_name in pin_button_map.items():
            if pin not in self.lines:
                continue
                
            line = self.lines[pin]
            button_raw_state = (line.get_value() == 0)
            
            if button_raw_state and not self.last_button_raw_states[button_name]:
                if current_time - self.last_press_time[button_name] > self.debounce_time:
                    self.button_states[button_name] = True
                    self.last_press_time[button_name] = current_time
            elif not button_raw_state:
                self.button_states[button_name] = False
            
            self.last_button_raw_states[button_name] = button_raw_state
        
        return self.button_states.copy()