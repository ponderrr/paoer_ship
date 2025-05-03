import pygame
import time

class ButtonHandler:
    def __init__(self, gpio_interface=None):
        self.cursor_x = 0
        self.cursor_y = 0
        self.max_grid = 9  
        self.move_delay = 0  
        
        self.using_gpio = gpio_interface is not None
        
        self.gpio = gpio_interface
        
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
            'position': (self.cursor_y, self.cursor_x),  
            'menu_up': False,
            'menu_down': False,
            'menu_select': False,
            'menu_back': False
        }

        if self.using_gpio:
            button_states = self.gpio.get_button_states()
        else:
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
        
        if current_time > self.move_delay:
            if button_states['up']:
                if self.cursor_y > 0:
                    self.cursor_y -= 1
                    actions['moved'] = True
                actions['menu_up'] = True
                self.move_delay = current_time + 150  
                
            if button_states['down']:
                if self.cursor_y < self.max_grid:
                    self.cursor_y += 1
                    actions['moved'] = True
                actions['menu_down'] = True
                self.move_delay = current_time + 150
                
            if button_states['left']:
                if self.cursor_x > 0:
                    self.cursor_x -= 1
                    actions['moved'] = True
                self.move_delay = current_time + 150
                
            if button_states['right']:
                if self.cursor_x < self.max_grid:
                    self.cursor_x += 1
                    actions['moved'] = True
                self.move_delay = current_time + 150

        if button_states['fire']:
            actions['fired'] = True
            actions['menu_select'] = True
            
        if button_states['mode']:
            actions['mode_changed'] = True
            actions['menu_back'] = True
            
        return actions