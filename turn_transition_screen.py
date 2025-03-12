import pygame
import time
from src.board.game_board import CellState

class TurnTransitionScreen:
    def __init__(self, screen, gpio_handler):
        """
        Initialize the transition screen between player turns
        
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
    
    def show_turn_result(self, player, x, y, hit, ship_sunk=False):
        """
        Show the result of a player's turn
        
        Args:
            player (int): The player who just took their turn (1 or 2)
            x (int): Row coordinate of the shot
            y (int): Column coordinate of the shot
            hit (bool): Whether the shot hit a ship
            ship_sunk (bool): Whether a ship was sunk by this shot
        """
        # Display the result for 5 seconds
        start_time = time.time()
        
        while time.time() - start_time < 5:
            # Fill background
            self.screen.fill(self.BLACK)
            
            # Draw title
            title = self.title_font.render(f"Player {player}'s Shot Result", True, self.WHITE)
            title_rect = title.get_rect(center=(self.width // 2, self.height // 3 - 40))
            self.screen.blit(title, title_rect)
            
            # Draw coordinates of shot
            shot_text = self.info_font.render(f"Shot at coordinate: {chr(65 + y)}{x + 1}", True, self.LIGHT_BLUE)
            shot_rect = shot_text.get_rect(center=(self.width // 2, self.height // 2 - 30))
            self.screen.blit(shot_text, shot_rect)
            
            # Draw result
            if hit:
                result_color = (255, 0, 0)  # Red for hit
                result_text = "HIT!"
                if ship_sunk:
                    result_text = "HIT - SHIP SUNK!"
            else:
                result_color = (0, 0, 255)  # Blue for miss
                result_text = "MISS!"
            
            result = self.title_font.render(result_text, True, result_color)
            result_rect = result.get_rect(center=(self.width // 2, self.height // 2 + 10))
            self.screen.blit(result, result_rect)
            
            # Draw time remaining
            time_left = 5 - (time.time() - start_time)
            time_text = self.info_font.render(f"Next player in {time_left:.1f} seconds...", True, self.LIGHT_GRAY)
            time_rect = time_text.get_rect(center=(self.width // 2, self.height // 2 + 50))
            self.screen.blit(time_text, time_rect)
            
            # Update display
            pygame.display.flip()
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
            
            # Short delay to prevent CPU hogging
            pygame.time.delay(100)
    
    def show_player_ready_screen(self, player):
        """
        Show a screen for the next player to get ready
        
        Args:
            player (int): The next player's number (1 or 2)
        """
        # Fill background
        self.screen.fill(self.BLACK)
        
        # Draw title
        title = self.title_font.render(f"PLAYER {player}'S TURN", True, self.WHITE)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 3 - 40))
        self.screen.blit(title, title_rect)
        
        # Draw message
        message = self.info_font.render(f"Player {player}, get ready for your turn!", True, self.LIGHT_BLUE)
        message_rect = message.get_rect(center=(self.width // 2, self.height // 2 - 30))
        self.screen.blit(message, message_rect)
        
        # Draw privacy notice
        privacy = self.info_font.render("Please make sure the other player isn't looking", True, self.LIGHT_GRAY)
        privacy_rect = privacy.get_rect(center=(self.width // 2, self.height // 2 + 10))
        self.screen.blit(privacy, privacy_rect)
        
        # Draw continue prompt
        prompt = self.info_font.render("Press FIRE button when ready", True, self.LIGHT_GRAY)
        prompt_rect = prompt.get_rect(center=(self.width // 2, self.height // 2 + 80))
        self.screen.blit(prompt, prompt_rect)
        
        # Update display
        pygame.display.flip()
        
        # Wait for fire button press
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False
            
            # Check GPIO buttons
            button_states = self.get_button_states()
            if button_states['fire']:
                waiting = False
                
            # Small delay to prevent CPU hogging
            pygame.time.delay(100)

    def show_ai_not_implemented(self):
        """Show a screen indicating that AI mode is not yet implemented"""
        # Fill background
        self.screen.fill(self.BLACK)
        
        # Draw title
        title = self.title_font.render("AI MODE NOT IMPLEMENTED", True, self.WHITE)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 3 - 40))
        self.screen.blit(title, title_rect)
        
        # Draw message
        message = self.info_font.render("The AI opponent is not yet implemented in this version.", True, self.LIGHT_BLUE)
        message_rect = message.get_rect(center=(self.width // 2, self.height // 2 - 30))
        self.screen.blit(message, message_rect)
        
        # Draw continue prompt
        prompt = self.info_font.render("Press any button to return to the menu", True, self.LIGHT_GRAY)
        prompt_rect = prompt.get_rect(center=(self.width // 2, self.height // 2 + 50))
        self.screen.blit(prompt, prompt_rect)
        
        # Update display
        pygame.display.flip()
        
        # Wait for any button press
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False
            
            # Check GPIO buttons
            button_states = self.get_button_states()
            if any(button_states.values()):
                waiting = False
                
            # Small delay to prevent CPU hogging
            pygame.time.delay(100)