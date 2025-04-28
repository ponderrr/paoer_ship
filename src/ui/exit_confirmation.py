import pygame
from src.main import selected_background_color


class ExitConfirmation:
    def __init__(self, screen, gpio_handler):
        """
        Initialize the exit confirmation dialog
        
        Args:
            screen: Pygame screen surface
            gpio_handler: GPIO interface for button inputs
        """
        self.screen = screen
        self.gpio_handler = gpio_handler
        
        # Screen dimensions
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BLUE = (50, 150, 255)
        self.LIGHT_BLUE = (80, 170, 255)
        self.LIGHT_GRAY = (180, 180, 180)
        self.RED = (255, 80, 80)
        
        # Fonts
        self.title_font = pygame.font.Font(None, 36)
        self.info_font = pygame.font.Font(None, 24)
        
        # Button handling
        self.last_button_states = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'fire': False,
            'mode': False,
            'rotate': False
        }
    
    def get_button_states(self):
        """Get button states with edge detection"""
        if self.gpio_handler:
            current_states = self.gpio_handler.get_button_states()
        else:
            # Handle keyboard input as fallback
            keys = pygame.key.get_pressed()
            current_states = {
                'up': keys[pygame.K_UP],
                'down': keys[pygame.K_DOWN],
                'left': keys[pygame.K_LEFT],
                'right': keys[pygame.K_RIGHT],
                'fire': keys[pygame.K_SPACE],
                'mode': keys[pygame.K_TAB],
                'rotate': keys[pygame.K_r]
            }
        
        # Edge detection (only trigger on button press, not hold)
        button_states = {}
        for key in current_states:
            button_states[key] = current_states[key] and not self.last_button_states[key]
            self.last_button_states[key] = current_states[key]
            
        return button_states
    
    def show(self):
        """
        Show the exit confirmation dialog
        
        Returns:
            bool: True if exit confirmed, False if cancelled
        """
        # Overlay a semi-transparent background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Black with 70% opacity
        self.screen.blit(overlay, (0, 0))
        
        # Create the dialog box
        dialog_width = 400
        dialog_height = 200
        dialog_rect = pygame.Rect(
            (self.width - dialog_width) // 2,
            (self.height - dialog_height) // 2,
            dialog_width,
            dialog_height
        )
        
        # Draw dialog background
        pygame.draw.rect(self.screen, (50, 50, 50), dialog_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.WHITE, dialog_rect, 2, border_radius=10)
        
        # Draw title
        title = self.title_font.render("Exit Game?", True, self.WHITE)
        title_rect = title.get_rect(center=(self.width // 2, dialog_rect.top + 40))
        self.screen.blit(title, title_rect)
        
        # Draw message
        message = self.info_font.render("Are you sure you want to exit the game?", True, self.LIGHT_GRAY)
        message_rect = message.get_rect(center=(self.width // 2, dialog_rect.top + 80))
        self.screen.blit(message, message_rect)
        
        # Draw instruction
        mode_text = self.info_font.render("Press MODE again to confirm exit", True, self.RED)
        mode_rect = mode_text.get_rect(center=(self.width // 2, dialog_rect.top + 120))
        self.screen.blit(mode_text, mode_rect)
        
        any_text = self.info_font.render("Press any other button to continue playing", True, self.LIGHT_BLUE)
        any_rect = any_text.get_rect(center=(self.width // 2, dialog_rect.top + 150))
        self.screen.blit(any_text, any_rect)
        
        # Update display
        pygame.display.flip()
        
        # Wait for button press
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        return True  # Confirm exit
                    else:
                        return False  # Cancel exit
            
            # Check GPIO buttons
            button_states = self.get_button_states()
            if button_states['mode']:
                return True  # Confirm exit
            elif any(value for key, value in button_states.items() if key != 'mode'):
                return False  # Cancel exit
            
            # Small delay to prevent CPU hogging
            pygame.time.delay(100)