"""
Input handler for Pyglet implementation of the game.
This replaces the Pygame-based button handling with Pyglet's event system.
"""
import pyglet
from pyglet.window import key
import time

class PygletInputHandler:
    def __init__(self, window, gpio_interface=None):
        """
        Initialize the input handler.
        
        Args:
            window: The Pyglet window to attach key event handlers to
            gpio_interface: Optional GPIO interface for hardware buttons
        """
        self.window = window
        self.gpio = gpio_interface
        self.cursor_x = 0
        self.cursor_y = 0
        self.max_grid = 9  # 10x10 grid (0-9)
        self.move_delay = 0  # Add delay to prevent too rapid movement
        
        # Track key states
        self.key_states = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'fire': False,
            'mode': False,
            'rotate': False
        }
        
        # Last key states for edge detection
        self.last_key_states = self.key_states.copy()
        
        # Menu navigation
        self.active_button_index = 0
        
        # Set up key press and release handlers
        self._setup_key_handlers()
    
    def _setup_key_handlers(self):
        """Set up key press and release handlers"""
        @self.window.event
        def on_key_press(symbol, modifiers):
            if symbol == key.UP:
                self.key_states['up'] = True
            elif symbol == key.DOWN:
                self.key_states['down'] = True
            elif symbol == key.LEFT:
                self.key_states['left'] = True
            elif symbol == key.RIGHT:
                self.key_states['right'] = True
            elif symbol == key.SPACE:
                self.key_states['fire'] = True
            elif symbol == key.TAB:
                self.key_states['mode'] = True
            elif symbol == key.R:
                self.key_states['rotate'] = True
        
        @self.window.event
        def on_key_release(symbol, modifiers):
            if symbol == key.UP:
                self.key_states['up'] = False
            elif symbol == key.DOWN:
                self.key_states['down'] = False
            elif symbol == key.LEFT:
                self.key_states['left'] = False
            elif symbol == key.RIGHT:
                self.key_states['right'] = False
            elif symbol == key.SPACE:
                self.key_states['fire'] = False
            elif symbol == key.TAB:
                self.key_states['mode'] = False
            elif symbol == key.R:
                self.key_states['rotate'] = False
    
    def update(self):
        """
        Update input state (to be called once per frame).
        Returns dictionary of button states.
        """
        current_time = time.time() * 1000  # Convert to milliseconds
        
        # Get button states from GPIO if available
        gpio_states = {}
        if self.gpio:
            gpio_states = self.gpio.get_button_states()
            # Merge GPIO states with keyboard states (GPIO takes precedence)
            for key in self.key_states:
                if gpio_states.get(key, False):
                    self.key_states[key] = True
        
        # Determine actions based on key/button states
        actions = {
            'moved': False,
            'fired': False,
            'mode_changed': False,
            'position': (self.cursor_y, self.cursor_x),  # Swap x,y to match board coordinates
            'menu_up': False,
            'menu_down': False,
            'menu_select': False,
            'menu_back': False,
            'rotate': False
        }
        
        # Only process movement if enough time has passed
        if current_time > self.move_delay:
            # Up button pressed
            if self.key_states['up'] and not self.last_key_states['up']:
                if self.cursor_y > 0:
                    self.cursor_y -= 1
                    actions['moved'] = True
                actions['menu_up'] = True
                self.move_delay = current_time + 150  # Add delay
                
            # Down button pressed
            if self.key_states['down'] and not self.last_key_states['down']:
                if self.cursor_y < self.max_grid:
                    self.cursor_y += 1
                    actions['moved'] = True
                actions['menu_down'] = True
                self.move_delay = current_time + 150
                
            # Left button pressed
            if self.key_states['left'] and not self.last_key_states['left']:
                if self.cursor_x > 0:
                    self.cursor_x -= 1
                    actions['moved'] = True
                self.move_delay = current_time + 150
                
            # Right button pressed
            if self.key_states['right'] and not self.last_key_states['right']:
                if self.cursor_x < self.max_grid:
                    self.cursor_x += 1
                    actions['moved'] = True
                self.move_delay = current_time + 150
                
            # Rotate button pressed
            if self.key_states['rotate'] and not self.last_key_states['rotate']:
                actions['rotate'] = True
                self.move_delay = current_time + 150
        
        # Fire action (select in menu)
        if self.key_states['fire'] and not self.last_key_states['fire']:
            actions['fired'] = True
            actions['menu_select'] = True
            
        # Mode switch (back in menu)
        if self.key_states['mode'] and not self.last_key_states['mode']:
            actions['mode_changed'] = True
            actions['menu_back'] = True
        
        # Store current states for next frame
        self.last_key_states = self.key_states.copy()
        
        return actions
    
    def set_cursor_position(self, x, y):
        """Set the cursor position directly"""
        if 0 <= x <= self.max_grid and 0 <= y <= self.max_grid:
            self.cursor_x = x
            self.cursor_y = y
    
    def get_position(self):
        """Get the current cursor position"""
        return (self.cursor_x, self.cursor_y)