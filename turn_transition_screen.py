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
    
    def draw_board_preview(self, board, offset_x, offset_y, cell_size=20):
        """
        Draw a preview of the game board
        
        Args:
            board: 2D array representing the board state
            offset_x: X offset for the board
            offset_y: Y offset for the board
            cell_size: Size of each cell in pixels
        """
        # Draw grid cells
        for y in range(10):
            for x in range(10):
                cell_rect = pygame.Rect(
                    offset_x + x * cell_size,
                    offset_y + y * cell_size,
                    cell_size - 2,
                    cell_size - 2
                )
                
                # Get cell value from board
                cell_value = board[y][x]
                
                if cell_value == CellState.EMPTY.value:
                    color = (50, 50, 50)  # Empty cell
                elif cell_value == CellState.SHIP.value:
                    color = (0, 255, 0)   # Ship
                elif cell_value == CellState.HIT.value:
                    color = (255, 0, 0)   # Hit
                else:
                    color = (0, 0, 255)   # Miss
                
                # Draw cell
                pygame.draw.rect(self.screen, color, cell_rect)
                pygame.draw.rect(self.screen, (100, 100, 100), cell_rect, 1)
                
        # Draw column labels (A-J)
        for i in range(10):
            letter = chr(65 + i)
            text = pygame.font.Font(None, 16).render(letter, True, self.WHITE)
            self.screen.blit(text, (offset_x + i * cell_size + 5, offset_y - 20))
        
        # Draw row labels (1-10)
        for i in range(10):
            number = str(i + 1)
            text = pygame.font.Font(None, 16).render(number, True, self.WHITE)
            self.screen.blit(text, (offset_x - 20, offset_y + i * cell_size + 5))
    
    def show_turn_result(self, player, row, col, hit, ship_sunk=False, is_ai_mode=False, player_board=None):
        """
        Show the result of a player's turn
        
        Args:
            player (int): The player who just took their turn (1 or 2)
            row (int): Row coordinate of the shot (0-9)
            col (int): Column coordinate of the shot (0-9)
            hit (bool): Whether the shot hit a ship
            ship_sunk (bool): Whether a ship was sunk by this shot
            is_ai_mode (bool): Whether the game is in AI mode
            player_board: The player's board for preview in AI mode
        """
        # Display the result for 5 seconds
        start_time = time.time()
        
        while time.time() - start_time < 5:
            # Fill background
            self.screen.fill(self.BLACK)
            
            # Draw title
            player_text = "Player" if player == 1 or not is_ai_mode else "AI"
            title = self.title_font.render(f"{player_text}'s Shot Result", True, self.WHITE)
            title_rect = title.get_rect(center=(self.width // 2, self.height // 4 - 20))
            self.screen.blit(title, title_rect)
            
            # Convert internal (row, col) coordinates to user-friendly display
            # Column is letter (A-J), Row is number (1-10)
            shot_text = self.info_font.render(f"Shot at coordinate: {chr(65 + col)}{row + 1}", True, self.LIGHT_BLUE)
            shot_rect = shot_text.get_rect(center=(self.width // 2, self.height // 4 + 20))
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
            result_rect = result.get_rect(center=(self.width // 2, self.height // 4 + 60))
            self.screen.blit(result, result_rect)
            
            # If in AI mode and we have a player board, show the board preview
            if is_ai_mode and player_board is not None:
                preview_title = self.info_font.render("Your Board", True, self.WHITE)
                preview_rect = preview_title.get_rect(center=(self.width // 2, self.height // 2 + 20))
                self.screen.blit(preview_title, preview_rect)
                
                # Draw the board preview centered on screen
                board_width = 10 * 20  # 10 cells of 20px each
                self.draw_board_preview(
                    player_board,
                    (self.width - board_width) // 2,
                    self.height // 2 + 40
                )
            
            # Draw time remaining
            time_left = 5 - (time.time() - start_time)
            time_text = self.info_font.render(f"Next player in {time_left:.1f} seconds...", True, self.LIGHT_GRAY)
            time_rect = time_text.get_rect(center=(self.width // 2, self.height - 100))
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
    
    def show_player_ready_screen(self, player, is_ai_mode=False, player_board=None):
        """
        Show a screen for the next player to get ready
        
        Args:
            player (int): The next player's number (1 or 2)
            is_ai_mode (bool): Whether the game is in AI mode
            player_board: The player's board for preview in AI mode
        """
        # Fill background
        self.screen.fill(self.BLACK)
        
        # Draw title
        if player == 2 and is_ai_mode:
            title = self.title_font.render("AI'S TURN", True, self.WHITE)
        else:
            title = self.title_font.render(f"PLAYER {player}'S TURN", True, self.WHITE)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 4 - 20))
        self.screen.blit(title, title_rect)
        
        # Draw message
        if player == 2 and is_ai_mode:
            message = self.info_font.render("AI is about to take its turn!", True, self.LIGHT_BLUE)
        else:
            message = self.info_font.render(f"Player {player}, get ready for your turn!", True, self.LIGHT_BLUE)
        message_rect = message.get_rect(center=(self.width // 2, self.height // 4 + 20))
        self.screen.blit(message, message_rect)
        
        # If playing against another human, show privacy notice
        if not is_ai_mode:
            privacy = self.info_font.render("Please make sure the other player isn't looking", True, self.LIGHT_GRAY)
            privacy_rect = privacy.get_rect(center=(self.width // 2, self.height // 4 + 50))
            self.screen.blit(privacy, privacy_rect)
        
        # If in AI mode and we have a player board, show the board preview
        if is_ai_mode and player_board is not None and player == 1:
            preview_title = self.info_font.render("Your Board", True, self.WHITE)
            preview_rect = preview_title.get_rect(center=(self.width // 2, self.height // 2 + 20))
            self.screen.blit(preview_title, preview_rect)
            
            # Draw the board preview centered on screen
            board_width = 10 * 20  # 10 cells of 20px each
            self.draw_board_preview(
                player_board,
                (self.width - board_width) // 2,
                self.height // 2 + 40
            )
        
        # Draw continue prompt
        prompt = self.info_font.render("Press FIRE button when ready", True, self.LIGHT_GRAY)
        prompt_rect = prompt.get_rect(center=(self.width // 2, self.height - 100))
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