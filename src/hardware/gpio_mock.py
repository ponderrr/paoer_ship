# src/hardware/gpio_mock.py
import pygame
from .gpio_interface import GPIOInterface

class GPIOMock(GPIOInterface):
    def __init__(self):
        """Mock implementation that uses keyboard input as a substitute for GPIO buttons"""
        self.button_states = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'fire': False,
            'mode': False
        }

    def setup(self):
        """No physical setup needed for the mock"""
        print("Mock GPIO initialized. Using keyboard input.")
        pass

    def cleanup(self):
        """No physical cleanup needed for the mock"""
        pass
    
    def get_button_states(self):
        """
        Maps keyboard keys to button states for testing
        
        Returns:
            dict: Dictionary with button states
        """
        keys = pygame.key.get_pressed()
        
        # Map keyboard keys to buttons
        self.button_states['up'] = keys[pygame.K_UP]
        self.button_states['down'] = keys[pygame.K_DOWN]
        self.button_states['left'] = keys[pygame.K_LEFT]
        self.button_states['right'] = keys[pygame.K_RIGHT]
        self.button_states['fire'] = keys[pygame.K_SPACE]
        self.button_states['mode'] = keys[pygame.K_TAB]
        
        return self.button_states.copy()