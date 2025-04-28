import pygame
import time
from src.board.game_board import CellState
from main import selected_background_color

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
    
    def show_turn_result(self, player, row, col, hit, ship_sunk=False, is_ai_mode=False, player_board=None):
        """
        Show the result of a player's turn
        
        Args:
            player (int): The player who just took their turn (1 or 2)
            row (int): Row coordinate of the shot (0-9)
            col (int): Column coordinate of the shot (0-9)
            hit (bool): Whether the shot hit a ship
            ship_sunk (bool): Whether a ship was sunk by this shot
            is_ai_mode (bool): Whether playing against AI
            player_board: Player's own board to display (for AI mode)
        """
        # Display the result for 4 seconds
        start_time = time.time()
        
        while time.time() - start_time < 4:
            # Fill background
            self.screen.fill(selected_background_color)

            
            # Draw title
            player_name = f"Player {player}" if player == 1 or not is_ai_mode else "AI"
            title = self.title_font.render(f"{player_name}'s Shot Result", True, self.WHITE)
            title_rect = title.get_rect(center=(self.width // 2, self.height // 5))
            self.screen.blit(title, title_rect)
            
            # Draw shot coordinates (convert internal board coords to UI friendly display)
            # Column is letter (A-J), Row is number (1-10)
            shot_text = self.info_font.render(f"Shot at coordinate: {chr(65 + col)}{row + 1}", True, self.LIGHT_BLUE)
            shot_rect = shot_text.get_rect(center=(self.width // 2, self.height // 3))
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
            result_rect = result.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(result, result_rect)
            
            # Draw player's board in AI mode ONLY if human player, not AI
            if is_ai_mode and player_board is not None and player == 1:  # Only show board for human player
                self._draw_mini_board(player_board, self.width // 2, int(self.height * 0.6), 12)
                board_title = self.info_font.render("Your Board", True, self.WHITE)
                board_title_rect = board_title.get_rect(center=(self.width // 2, int(self.height * 0.53)))
                self.screen.blit(board_title, board_title_rect)
            
            # Draw time remaining (removed "Press FIRE to continue" text)
            time_left = 4 - (time.time() - start_time)
            time_text = self.info_font.render(f"Continue in {time_left:.1f} seconds...", True, self.LIGHT_GRAY)
            time_rect = time_text.get_rect(center=(self.width // 2, self.height - 30))
            self.screen.blit(time_text, time_rect)
            
            # Update display
            pygame.display.flip()
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    return  # Skip waiting if space is pressed
            
            # Check GPIO buttons
            button_states = self.get_button_states()
            if button_states['fire']:
                return  # Skip waiting if fire button is pressed
            
            # Short delay to prevent CPU hogging
            pygame.time.delay(50)
    
    def show_player_ready_screen(self, player, is_ai_mode=False, player_board=None):
        """
        Show a screen for the next player to get ready
        
        Args:
            player (int): The next player's number (1 or 2)
            is_ai_mode (bool): Whether playing against AI
            player_board: Player's own board to display (for AI mode)
        """
        # Fill background
        self.screen.fill(selected_background_color)
        
        player_name = f"PLAYER {player}" if player == 1 or not is_ai_mode else "AI"
        # Draw title
        title = self.title_font.render(f"{player_name}'S TURN", True, self.WHITE)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 5))
        self.screen.blit(title, title_rect)
        
        # Different message depending on player
        if player == 1 or not is_ai_mode:
            # Human player message
            message = self.info_font.render(f"Player {player}, get ready for your turn!", True, self.LIGHT_BLUE)
        else:
            # AI message
            message = self.info_font.render("AI is preparing to take its turn...", True, self.LIGHT_BLUE)
        
        message_rect = message.get_rect(center=(self.width // 2, self.height // 3))
        self.screen.blit(message, message_rect)
        
        # Draw player's board in AI mode if provided
        if is_ai_mode and player_board is not None:
            self._draw_mini_board(player_board, self.width // 2, int(self.height * 0.6), 12)
            board_title = self.info_font.render("Your Board", True, self.WHITE)
            board_title_rect = board_title.get_rect(center=(self.width // 2, int(self.height * 0.53)))
            self.screen.blit(board_title, board_title_rect)
        
        # Draw privacy notice for human vs human
        if not is_ai_mode:
            privacy = self.info_font.render("Please make sure the other player isn't looking", True, self.LIGHT_GRAY)
            privacy_rect = privacy.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(privacy, privacy_rect)
        
        # Draw continue prompt
        if player == 1 or not is_ai_mode:
            prompt = self.info_font.render("Press FIRE button when ready", True, self.LIGHT_GRAY)
            prompt_rect = prompt.get_rect(center=(self.width // 2, self.height - 60))
            self.screen.blit(prompt, prompt_rect)
        else:
            # For AI mode, show auto-continue message
            prompt = self.info_font.render("AI will play in a moment...", True, self.LIGHT_GRAY)
            prompt_rect = prompt.get_rect(center=(self.width // 2, self.height - 60))
            self.screen.blit(prompt, prompt_rect)
        
        # Update display
        pygame.display.flip()
        
        # For AI's turn, just wait briefly
        if player == 2 and is_ai_mode:
            pygame.time.delay(1500)  # Wait 1.5 seconds
            return
        
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
            pygame.time.delay(50)
            
    def _draw_mini_board(self, board, center_x, center_y, cell_size):
        """Draw a mini version of the game board"""
        board_width = cell_size * 10
        board_height = cell_size * 10
        
        # Calculate top-left corner from center position
        top_x = center_x - (board_width // 2)
        top_y = center_y - (board_height // 2)
        
        # Draw grid cells
        for y in range(10):
            for x in range(10):
                cell_rect = pygame.Rect(
                    top_x + x * cell_size,
                    top_y + y * cell_size,
                    cell_size - 1,
                    cell_size - 1
                )
                
                # Get cell value
                cell_value = board[y][x]
                
                # Determine cell color
                if cell_value == CellState.EMPTY.value:
                    color = (50, 50, 50)  # Empty
                elif cell_value == CellState.SHIP.value:
                    color = (0, 255, 0)   # Ship
                elif cell_value == CellState.HIT.value:
                    color = (255, 0, 0)   # Hit
                else:
                    color = (0, 0, 255)   # Miss
                
                # Draw cell
                pygame.draw.rect(self.screen, color, cell_rect)
                pygame.draw.rect(self.screen, (100, 100, 100), cell_rect, 1)