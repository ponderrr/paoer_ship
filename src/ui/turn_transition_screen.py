import pygame
import time
import config
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
        
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.title_font_size = config.get_font_size(self.height, 36)
        self.info_font_size = config.get_font_size(self.height, 24)
        self.title_font = pygame.font.Font(None, self.title_font_size)
        self.info_font = pygame.font.Font(None, self.info_font_size)
        
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
            keys = pygame.key.get_pressed()
            current_states = {
                'up': keys[config.INPUT_MOVE_UP],
                'down': keys[config.INPUT_MOVE_DOWN],
                'left': keys[config.INPUT_MOVE_LEFT],
                'right': keys[config.INPUT_MOVE_RIGHT],
                'fire': keys[config.INPUT_FIRE],
                'mode': keys[config.INPUT_MODE],
                'rotate': keys[config.INPUT_ROTATE]
            }
        
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
        start_time = time.time()
        
        while time.time() - start_time < 4:
            self.screen.fill(config.selected_background_color)
            
            player_name = f"Player {player}" if player == 1 or not is_ai_mode else "AI"
            title = self.title_font.render(f"{player_name}'s Shot Result", True, config.WHITE)
            title_rect = title.get_rect(center=(self.width // 2, self.height // 5))
            self.screen.blit(title, title_rect)
            
            shot_text = self.info_font.render(f"Shot at coordinate: {chr(65 + col)}{row + 1}", True, config.LIGHT_BLUE)
            shot_rect = shot_text.get_rect(center=(self.width // 2, self.height // 3))
            self.screen.blit(shot_text, shot_rect)
            
            if hit:
                result_color = config.RED
                result_text = "HIT!"
                if ship_sunk:
                    result_text = "HIT - SHIP SUNK!"
            else:
                result_color = config.BLUE 
                result_text = "MISS!"
            
            result = self.title_font.render(result_text, True, result_color)
            result_rect = result.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(result, result_rect)
            
            if is_ai_mode and player_board is not None and player == 1: 
                board_cell_size = max(12, int(min(self.width, self.height) * 0.012))
                self._draw_mini_board(player_board, self.width // 2, int(self.height * 0.6), board_cell_size)
                board_title = self.info_font.render("Your Board", True, config.WHITE)
                board_title_rect = board_title.get_rect(center=(self.width // 2, int(self.height * 0.53)))
                self.screen.blit(board_title, board_title_rect)
            
            time_left = 4 - (time.time() - start_time)
            time_text = self.info_font.render(f"Continue in {time_left:.1f} seconds...", True, config.LIGHT_GRAY)
            time_rect = time_text.get_rect(center=(self.width // 2, self.height - 30))
            self.screen.blit(time_text, time_rect)
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN and event.key == config.INPUT_FIRE:
                    return 
            
            button_states = self.get_button_states()
            if button_states['fire']:
                return  
            
            pygame.time.delay(50)
    
    def show_player_ready_screen(self, player, is_ai_mode=False, player_board=None):
        """
        Show a screen for the next player to get ready
        
        Args:
            player (int): The next player's number (1 or 2)
            is_ai_mode (bool): Whether playing against AI
            player_board: Player's own board to display (for AI mode)
        """
        self.screen.fill(config.selected_background_color)
        
        player_name = f"PLAYER {player}" if player == 1 or not is_ai_mode else "AI"
        title = self.title_font.render(f"{player_name}'S TURN", True, config.WHITE)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 5))
        self.screen.blit(title, title_rect)
        
        if player == 1 or not is_ai_mode:
            message = self.info_font.render(f"Player {player}, get ready for your turn!", True, config.LIGHT_BLUE)
        else:
            message = self.info_font.render("AI is preparing to take its turn...", True, config.LIGHT_BLUE)
        
        message_rect = message.get_rect(center=(self.width // 2, self.height // 3))
        self.screen.blit(message, message_rect)
        
        if is_ai_mode and player_board is not None:
            board_cell_size = max(12, int(min(self.width, self.height) * 0.012))
            self._draw_mini_board(player_board, self.width // 2, int(self.height * 0.6), board_cell_size)
            board_title = self.info_font.render("Your Board", True, config.WHITE)
            board_title_rect = board_title.get_rect(center=(self.width // 2, int(self.height * 0.53)))
            self.screen.blit(board_title, board_title_rect)
        
        if not is_ai_mode:
            privacy = self.info_font.render("Please make sure the other player isn't looking", True, config.LIGHT_GRAY)
            privacy_rect = privacy.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(privacy, privacy_rect)
        
        if player == 1 or not is_ai_mode:
            prompt = self.info_font.render("Press FIRE button when ready", True, config.LIGHT_GRAY)
            prompt_rect = prompt.get_rect(center=(self.width // 2, self.height - 60))
            self.screen.blit(prompt, prompt_rect)
        else:
            prompt = self.info_font.render("AI will play in a moment...", True, config.LIGHT_GRAY)
            prompt_rect = prompt.get_rect(center=(self.width // 2, self.height - 60))
            self.screen.blit(prompt, prompt_rect)
        
        pygame.display.flip()
        
        if player == 2 and is_ai_mode:
            pygame.time.delay(1500)  
            return
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == config.INPUT_FIRE:
                        waiting = False
            
            button_states = self.get_button_states()
            if button_states['fire']:
                waiting = False
                
            pygame.time.delay(50)
            
    def _draw_mini_board(self, board, center_x, center_y, cell_size):
        """Draw a mini version of the game board"""
        board_width = cell_size * config.BOARD_SIZE
        board_height = cell_size * config.BOARD_SIZE
        
        top_x = center_x - (board_width // 2)
        top_y = center_y - (board_height // 2)
        
        for y in range(config.BOARD_SIZE):
            for x in range(config.BOARD_SIZE):
                cell_rect = pygame.Rect(
                    top_x + x * cell_size,
                    top_y + y * cell_size,
                    cell_size - 1,
                    cell_size - 1
                )
                
                cell_value = board[y][x]
                
                if cell_value == CellState.EMPTY.value:
                    color = config.COLOR_EMPTY
                elif cell_value == CellState.SHIP.value:
                    color = config.COLOR_SHIP
                elif cell_value == CellState.HIT.value:
                    color = config.COLOR_HIT
                else:
                    color = config.COLOR_MISS
                
                pygame.draw.rect(self.screen, color, cell_rect)
                pygame.draw.rect(self.screen, config.COLOR_GRID, cell_rect, 1)