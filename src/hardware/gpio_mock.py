# import pygame
# from .gpio_interface import GPIOInterface

# class GPIOMock(GPIOInterface):
#     def __init__(self):
#         """Mock implementation that uses keyboard input as a substitute for GPIO buttons"""
#         self.button_states = {
#             'up': False,
#             'down': False,
#             'left': False,
#             'right': False,
#             'fire': False,
#             'mode': False
#         }
        
#         # Store last key states to detect changes (key press events)
#         self.last_key_states = {
#             'up': False,
#             'down': False,
#             'left': False,
#             'right': False,
#             'fire': False,
#             'mode': False
#         }

#     def setup(self):
#         """No physical setup needed for the mock"""
#         print("Mock GPIO initialized. Using keyboard input.")
#         pass

#     def cleanup(self):
#         """No physical cleanup needed for the mock"""
#         pass
    
#     def get_button_states(self):
#         """
#         Maps keyboard keys to button states for testing
        
#         Returns:
#             dict: Dictionary with button states
#         """
#         keys = pygame.key.get_pressed()
        
#         # Get raw key states
#         current_key_states = {
#             'up': keys[pygame.K_UP],
#             'down': keys[pygame.K_DOWN],
#             'left': keys[pygame.K_LEFT],
#             'right': keys[pygame.K_RIGHT],
#             'fire': keys[pygame.K_SPACE],
#             'mode': keys[pygame.K_TAB]
#         }
        
#         # Only register a press when the state changes from released to pressed
#         for button in self.button_states:
#             if current_key_states[button] and not self.last_key_states[button]:
#                 self.button_states[button] = True
#             elif not current_key_states[button]:
#                 self.button_states[button] = False
                
#         # Update last key states
#         self.last_key_states = current_key_states.copy()
        
#         return self.button_states.copy()

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
            'mode': False,
            'rotate': False  # Add rotate button state
        }
        
        # Store last key states to detect changes (key press events)
        self.last_key_states = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'fire': False,
            'mode': False,
            'rotate': False  # Add rotate button state
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
        
        # Get raw key states
        current_key_states = {
            'up': keys[pygame.K_UP],
            'down': keys[pygame.K_DOWN],
            'left': keys[pygame.K_LEFT],
            'right': keys[pygame.K_RIGHT],
            'fire': keys[pygame.K_SPACE],
            'mode': keys[pygame.K_TAB],
            'rotate': keys[pygame.K_r]  # Map 'r' key to rotate function
        }
        
        # Only register a press when the state changes from released to pressed
        for button in self.button_states:
            if current_key_states[button] and not self.last_key_states[button]:
                self.button_states[button] = True
            elif not current_key_states[button]:
                self.button_states[button] = False
                
        # Update last key states
        self.last_key_states = current_key_states.copy()
        
        return self.button_states.copy()