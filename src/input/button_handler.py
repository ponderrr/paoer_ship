import pygame
import time

class ButtonHandler:
    def __init__(self, gpio_interface=None):
        self.cursor_x = 0
        self.cursor_y = 0
        self.max_grid = 9  # 10x10 grid (0-9)
        self.move_delay = 0  # Add delay to prevent too rapid movement
        
        # Flag to determine if using GPIO or keyboard
        self.using_gpio = gpio_interface is not None
        
        # GPIO interface if available
        self.gpio = gpio_interface
        
        # Menu navigation
        self.active_button_index = 0
    
    def update(self, keys=None):
        """
        Handle input (GPIO or keyboard) and return actions
        
        Args:
            keys: Keyboard state (only used if not using GPIO)
            
        Returns:
            dict: Actions triggered by input
        """
        current_time = pygame.time.get_ticks()
        
        actions = {
            'moved': False,
            'fired': False,
            'mode_changed': False,
            'position': (self.cursor_y, self.cursor_x),  # Swap x,y to match board coordinates
            'menu_up': False,
            'menu_down': False,
            'menu_select': False,
            'menu_back': False
        }

        # Get button states from GPIO
        if self.using_gpio:
            button_states = self.gpio.get_button_states()
        else:
            # Use keyboard as fallback
            button_states = {
                'up': False,
                'down': False,
                'left': False,
                'right': False,
                'fire': False,
                'mode': False
            }
            if keys:
                if keys[pygame.K_UP]:
                    button_states['up'] = True
                if keys[pygame.K_DOWN]:
                    button_states['down'] = True
                if keys[pygame.K_LEFT]:
                    button_states['left'] = True
                if keys[pygame.K_RIGHT]:
                    button_states['right'] = True
                if keys[pygame.K_SPACE]:
                    button_states['fire'] = True
                if keys[pygame.K_TAB]:
                    button_states['mode'] = True
        
        # Only process movement if enough time has passed
        if current_time > self.move_delay:
            # Up button pressed
            if button_states['up']:
                if self.cursor_y > 0:
                    self.cursor_y -= 1
                    actions['moved'] = True
                actions['menu_up'] = True
                self.move_delay = current_time + 150  # Add delay between moves
                
            # Down button pressed
            if button_states['down']:
                if self.cursor_y < self.max_grid:
                    self.cursor_y += 1
                    actions['moved'] = True
                actions['menu_down'] = True
                self.move_delay = current_time + 150
                
            # Left button pressed
            if button_states['left']:
                if self.cursor_x > 0:
                    self.cursor_x -= 1
                    actions['moved'] = True
                self.move_delay = current_time + 150
                
            # Right button pressed
            if button_states['right']:
                if self.cursor_x < self.max_grid:
                    self.cursor_x += 1
                    actions['moved'] = True
                self.move_delay = current_time + 150

        # Fire action (select in menu)
        if button_states['fire']:
            actions['fired'] = True
            actions['menu_select'] = True
            
        # Mode switch (back in menu)
        if button_states['mode']:
            actions['mode_changed'] = True
            actions['menu_back'] = True
            
        return actions