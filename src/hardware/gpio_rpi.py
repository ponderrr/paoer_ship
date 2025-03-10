# import gpiod
# import time
# from .gpio_interface import GPIOInterface

# class GPIORPI(GPIOInterface):
#     def __init__(self):
#         # Define GPIO pins for buttons (BCM numbering)
#         self.PIN_UP = 17    # Pin 11
#         self.PIN_DOWN = 27  # Pin 13
#         self.PIN_LEFT = 22  # Pin 15
#         self.PIN_RIGHT = 23 # Pin 16
#         self.PIN_FIRE = 24  # Pin 18
#         self.PIN_MODE = 25  # Pin 22
        
#         # Button state variables with debounce protection
#         self.button_states = {
#             'up': False,
#             'down': False,
#             'left': False,
#             'right': False,
#             'fire': False,
#             'mode': False
#         }
        
#         # Last button state to detect changes
#         self.last_button_raw_states = {
#             'up': False,
#             'down': False,
#             'left': False,
#             'right': False,
#             'fire': False,
#             'mode': False
#         }
        
#         # Debounce time in seconds
#         self.debounce_time = 0.15
#         self.last_press_time = {
#             'up': 0,
#             'down': 0,
#             'left': 0,
#             'right': 0,
#             'fire': 0,
#             'mode': 0
#         }
        
#         # GPIO objects
#         self.chip = None
#         self.lines = {}

#     def setup(self):
#         """Initialize GPIO pins for button input"""
#         try:
#             # Try to open the GPIO chip for Pi 5 or fall back to Pi 4 and earlier
#             try:
#                 self.chip = gpiod.Chip("gpiochip4")  # Raspberry Pi 5
#                 print("Using gpiochip4 for Raspberry Pi 5")
#             except:
#                 self.chip = gpiod.Chip("gpiochip0")  # Earlier Raspberry Pi models
#                 print("Using gpiochip0 for Raspberry Pi")
            
#             # Pin to button name mapping
#             pin_button_map = {
#                 self.PIN_UP: 'up',
#                 self.PIN_DOWN: 'down',
#                 self.PIN_LEFT: 'left',
#                 self.PIN_RIGHT: 'right',
#                 self.PIN_FIRE: 'fire',
#                 self.PIN_MODE: 'mode'
#             }
            
#             # Set up all the lines
#             for pin, button_name in pin_button_map.items():
#                 try:
#                     # Try the newer API first
#                     line = self.chip.get_line(pin)
#                     config = gpiod.line_request()
#                     config.consumer = f"paoer-ship-{button_name}"
#                     config.request_type = gpiod.line_request.DIRECTION_INPUT
#                     line.request(config)
#                     self.lines[pin] = line
#                 except AttributeError:
#                     # Fall back to older API
#                     line = self.chip.get_line(pin)
#                     line.request(consumer=f"paoer-ship-{button_name}", type=gpiod.LINE_REQ_DIR_IN)
#                     self.lines[pin] = line
                
#             print("GPIO pins initialized for button input using gpiod")
#         except Exception as e:
#             print(f"Error setting up GPIO: {e}")
#             if self.chip:
#                 self.chip.close()
#                 self.chip = None

#     def cleanup(self):
#         """Clean up GPIO resources when no longer needed"""
#         if self.chip:
#             self.chip.close()
#             self.chip = None
#         print("GPIO resources cleaned up")
    
#     def get_button_states(self):
#         """
#         Reads the current state of all buttons with debounce protection
        
#         Returns:
#             dict: Dictionary with debounced button states
#         """
#         if not self.chip:
#             return self.button_states.copy()
            
#         current_time = time.time()
        
#         # Check each button and update states with debounce
#         pin_button_map = {
#             self.PIN_UP: 'up',
#             self.PIN_DOWN: 'down',
#             self.PIN_LEFT: 'left',
#             self.PIN_RIGHT: 'right',
#             self.PIN_FIRE: 'fire',
#             self.PIN_MODE: 'mode'
#         }
        
#         for pin, button_name in pin_button_map.items():
#             if pin not in self.lines:
#                 continue
                
#             # Read line value (active LOW with pull-up)
#             line = self.lines[pin]
#             # For buttons with pull-up resistors, 0 means pressed (active low)
#             button_raw_state = (line.get_value() == 0)
            
#             # Only register a press when the state changes from released to pressed
#             if button_raw_state and not self.last_button_raw_states[button_name]:
#                 # Button was just pressed
#                 if current_time - self.last_press_time[button_name] > self.debounce_time:
#                     self.button_states[button_name] = True
#                     self.last_press_time[button_name] = current_time
#             elif not button_raw_state:
#                 # Button was released
#                 self.button_states[button_name] = False
            
#             # Update the last raw state
#             self.last_button_raw_states[button_name] = button_raw_state
        
#         return self.button_states.copy()




import gpiod
import time
from .gpio_interface import GPIOInterface

class GPIORPI(GPIOInterface):
    def __init__(self):
        # Define GPIO pins for buttons (BCM numbering)
        self.PIN_UP = 17    # Pin 11
        self.PIN_DOWN = 27  # Pin 13
        self.PIN_LEFT = 22  # Pin 15
        self.PIN_RIGHT = 23 # Pin 16
        self.PIN_FIRE = 24  # Pin 18
        self.PIN_MODE = 25  # Pin 22
        self.PIN_ROTATE = 26  # Pin 37 (TODO: Update this when hardware is connected)
        
        # Button state variables with debounce protection
        self.button_states = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'fire': False,
            'mode': False,
            'rotate': False  # Add rotate button state
        }
        
        # Last button state to detect changes
        self.last_button_raw_states = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'fire': False,
            'mode': False,
            'rotate': False  # Add rotate button state
        }
        
        # Debounce time in seconds
        self.debounce_time = 0.15
        self.last_press_time = {
            'up': 0,
            'down': 0,
            'left': 0,
            'right': 0,
            'fire': 0,
            'mode': 0,
            'rotate': 0  # Add rotate button debounce time
        }
        
        # GPIO objects
        self.chip = None
        self.lines = {}

    def setup(self):
        """Initialize GPIO pins for button input"""
        try:
            # Try to open the GPIO chip for Pi 5 or fall back to Pi 4 and earlier
            try:
                self.chip = gpiod.Chip("gpiochip4")  # Raspberry Pi 5
                print("Using gpiochip4 for Raspberry Pi 5")
            except:
                self.chip = gpiod.Chip("gpiochip0")  # Earlier Raspberry Pi models
                print("Using gpiochip0 for Raspberry Pi")
            
            # Pin to button name mapping
            pin_button_map = {
                self.PIN_UP: 'up',
                self.PIN_DOWN: 'down',
                self.PIN_LEFT: 'left',
                self.PIN_RIGHT: 'right',
                self.PIN_FIRE: 'fire',
                self.PIN_MODE: 'mode',
                self.PIN_ROTATE: 'rotate'  # Add rotate button mapping
            }
            
            # Set up all the lines
            for pin, button_name in pin_button_map.items():
                try:
                    # Try the newer API first
                    line = self.chip.get_line(pin)
                    config = gpiod.line_request()
                    config.consumer = f"paoer-ship-{button_name}"
                    config.request_type = gpiod.line_request.DIRECTION_INPUT
                    line.request(config)
                    self.lines[pin] = line
                except AttributeError:
                    # Fall back to older API
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
        
        # Check each button and update states with debounce
        pin_button_map = {
            self.PIN_UP: 'up',
            self.PIN_DOWN: 'down',
            self.PIN_LEFT: 'left',
            self.PIN_RIGHT: 'right',
            self.PIN_FIRE: 'fire',
            self.PIN_MODE: 'mode',
            self.PIN_ROTATE: 'rotate'  # Add rotate button mapping
        }
        
        for pin, button_name in pin_button_map.items():
            if pin not in self.lines:
                continue
                
            # Read line value (active LOW with pull-up)
            line = self.lines[pin]
            # For buttons with pull-up resistors, 0 means pressed (active low)
            button_raw_state = (line.get_value() == 0)
            
            # Only register a press when the state changes from released to pressed
            if button_raw_state and not self.last_button_raw_states[button_name]:
                # Button was just pressed
                if current_time - self.last_press_time[button_name] > self.debounce_time:
                    self.button_states[button_name] = True
                    self.last_press_time[button_name] = current_time
            elif not button_raw_state:
                # Button was released
                self.button_states[button_name] = False
            
            # Update the last raw state
            self.last_button_raw_states[button_name] = button_raw_state
        
        return self.button_states.copy()