import pygame
import random
import time
import sys
from src.utils.constants import SHIP_TYPES
from src.board.game_board import GameBoard, CellState

import config

class ShipPlacementScreen:
    def __init__(self, screen, gpio_handler=None, ai_mode=True, difficulty="Medium", sound_manager=None):
        """
        Initialize the ship placement screen
        
        Args:
            screen: Pygame screen surface
            gpio_handler: GPIO interface for button inputs
            ai_mode: Whether playing against AI (True) or another player (False)
            difficulty: AI difficulty level if ai_mode is True
            sound_manager: Sound manager for playing sound effects
        """
        self.screen = screen
        self.gpio_handler = gpio_handler
        self.ai_mode = ai_mode
        self.difficulty = difficulty
        self.sound_manager = sound_manager
        
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.cell_size = int(min(self.width, self.height) * 0.03)  
        board_width = self.cell_size * 10
        board_height = self.cell_size * 10
        
        self.grid_offset_x = (self.width - board_width) // 2
        self.grid_offset_y = (self.height - board_height) // 2
        
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BLUE = (50, 150, 255)
        self.LIGHT_BLUE = (80, 170, 255)
        self.LIGHT_GRAY = (180, 180, 180)
        self.SHIP_COLOR = (0, 255, 0)
        self.INVALID_COLOR = (255, 100, 100)
        self.HIGHLIGHT_COLOR = (255, 255, 0)
        
        self.title_font_size = max(36, int(self.height * 0.033))
        self.info_font_size = max(24, int(self.height * 0.022))
        self.title_font = pygame.font.Font(None, self.title_font_size)
        self.info_font = pygame.font.Font(None, self.info_font_size)
        
        self.player1_board = GameBoard()
        self.player2_board = GameBoard()
        
        self.ship_types = list(SHIP_TYPES.items())
        self.current_ship_index = 0
        self.current_ship_horizontal = True
        
        self.current_player = 1
        
        self.cursor_x = 0
        self.cursor_y = 0
        
        self.move_delay = 0
        
        self.placement_complete = False
        self.placement_valid = True  
        
        self.showing_confirmation = False
        self.confirmation_option = 0  
        
        self.last_button_states = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'fire': False,
            'mode': False,
            'rotate': False  
        }
    
    def play_invalid_sound(self):
        """Play the invalid action sound"""
        if self.sound_manager:
            self.sound_manager.play_sound("back") 
    
    def check_placement_validity(self):
        """Check if the current ship can be placed at the current position"""
        if self.current_ship_index >= len(self.ship_types):
            return True
            
        board = self.player1_board if self.current_player == 1 else self.player2_board
        ship_name, ship_length = self.ship_types[self.current_ship_index]
        
        self.placement_valid = self.can_place_ship(
            board, 
            self.cursor_x, 
            self.cursor_y, 
            ship_length, 
            self.current_ship_horizontal
        )
        return self.placement_valid
    
    def can_place_ship(self, board, x, y, length, horizontal):
        """Check if a ship can be placed at the given position"""
        if horizontal:
            if y + length > board.size:
                return False
        else:
            if x + length > board.size:
                return False
                
        for i in range(length):
            check_x = x
            check_y = y
            
            if horizontal:
                check_y += i
            else:
                check_x += i
                
            if board.board[check_x, check_y] != CellState.EMPTY.value:
                return False
                
        return True
    
    def place_current_ship(self, board):
        """Place the current ship on the board"""
        ship_name, ship_length = self.ship_types[self.current_ship_index]
        
        is_valid = self.can_place_ship(
            board, 
            self.cursor_x, 
            self.cursor_y, 
            ship_length, 
            self.current_ship_horizontal
        )
        
        if not is_valid:
            self.play_invalid_sound()
            return False
        
        success = board.place_ship(
            self.cursor_x, 
            self.cursor_y, 
            ship_length, 
            self.current_ship_horizontal
        )
        
        if success:
            if self.sound_manager:
                self.sound_manager.play_sound("hit")  
                
            self.current_ship_index += 1
            
            self.cursor_x = 0
            self.cursor_y = 0
            
            self.check_placement_validity()
            
            if self.current_ship_index >= len(self.ship_types):
                if self.ai_mode or self.current_player == 2:
                    self.placement_complete = True
                    if self.sound_manager:
                        self.sound_manager.play_sound("ship_sunk") 
                else:
                    self.show_player_transition_screen()
                    self.show_player_setup_screen(2)
                    self.current_player = 2
                    self.current_ship_index = 0
                    self.current_ship_horizontal = True
                    self.check_placement_validity()
        else:
            self.play_invalid_sound()
        
        return success
    
    def place_ai_ships(self):
        """Randomly place ships for AI opponent"""
        self.player2_board.reset_board()
        
        for ship_name, ship_length in self.ship_types:
            placed = False
            attempt_count = 0
            max_attempts = 100  
            
            while not placed and attempt_count < max_attempts:
                x = random.randint(0, 9)
                y = random.randint(0, 9)
                horizontal = random.choice([True, False])
                
                placed = self.player2_board.place_ship(x, y, ship_length, horizontal)
                attempt_count += 1
                
            if not placed:
                self.player2_board.reset_board()
                return self.place_ai_ships()
        
        return True
    
    def reset_placement(self):
        """Reset the current player's ship placement"""
        if self.current_player == 1:
            self.player1_board.reset_board()
        else:
            self.player2_board.reset_board()
            
        self.current_ship_index = 0
        self.current_ship_horizontal = True
        self.cursor_x = 0
        self.cursor_y = 0
        
        self.check_placement_validity()
    
    def get_button_states(self):
        """Get button states with edge detection"""
        if self.gpio_handler:
            current_states = self.gpio_handler.get_button_states()
        else:
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
        
        # only trigger on button press, not hold
        button_states = {}
        for key in current_states:
            button_states[key] = current_states[key] and not self.last_button_states[key]
            self.last_button_states[key] = current_states[key]
            
        return button_states
    
    def handle_input(self):
        """Handle user input for ship placement"""
        button_states = self.get_button_states()
        current_time = pygame.time.get_ticks()
        
        if current_time > self.move_delay:
            if self.showing_confirmation:
                if button_states['up'] or button_states['down']:
                    self.confirmation_option = 1 - self.confirmation_option  
                    if self.sound_manager:
                        self.sound_manager.play_sound("navigate_up" if button_states['up'] else "navigate_down")
                    self.move_delay = current_time + 200
                
                elif button_states['fire']:
                    if self.confirmation_option == 0:  
                        self.showing_confirmation = False
                        if self.sound_manager:
                            self.sound_manager.play_sound("accept")
                        return {'action': 'continue_game'}
                    else:  
                        self.showing_confirmation = False
                        if self.sound_manager:
                            self.sound_manager.play_sound("accept")
                        self.reset_placement()
                
                return {'action': 'none'}
            
            if self.current_ship_index >= len(self.ship_types):
                return {'action': 'none'}
                
            board = self.player1_board if self.current_player == 1 else self.player2_board
            ship_name, ship_length = self.ship_types[self.current_ship_index]
            
            moved = False
            hit_boundary = False
            
            if button_states['up']:
                if self.cursor_x > 0:  
                    self.cursor_x -= 1
                    moved = True
                    if self.sound_manager:
                        self.sound_manager.play_sound("navigate_up")
                else:
                    hit_boundary = True
                    
            if button_states['down']:
                max_row = 9
                if not self.current_ship_horizontal and ship_length > 1:
                    max_row = 10 - ship_length
                
                if self.cursor_x < max_row:
                    self.cursor_x += 1
                    moved = True
                    if self.sound_manager:
                        self.sound_manager.play_sound("navigate_down")
                else:
                    hit_boundary = True
                
            if button_states['left']:
                if self.cursor_y > 0:
                    self.cursor_y -= 1
                    moved = True
                    if self.sound_manager:
                        self.sound_manager.play_sound("navigate_up")  
                else:
                    hit_boundary = True
                
            if button_states['right']:
                max_col = 9
                if self.current_ship_horizontal and ship_length > 1:
                    max_col = 10 - ship_length
                
                if self.cursor_y < max_col:
                    self.cursor_y += 1
                    moved = True
                    if self.sound_manager:
                        self.sound_manager.play_sound("navigate_down") 
                else:
                    hit_boundary = True
                    
            if hit_boundary:
                self.play_invalid_sound()
                self.move_delay = current_time + 150
                
            if button_states['rotate']:
                if self.current_ship_horizontal:
                    if self.cursor_x + ship_length <= 10:
                        self.current_ship_horizontal = False
                        moved = True
                        if self.sound_manager:
                            self.sound_manager.play_sound("accept")  
                    else:
                        hit_boundary = True
                        self.play_invalid_sound()
                else:
                    if self.cursor_y + ship_length <= 10:
                        self.current_ship_horizontal = True
                        moved = True
                        if self.sound_manager:
                            self.sound_manager.play_sound("accept")  
                    else:
                        hit_boundary = True
                        self.play_invalid_sound()
                
            if moved:
                was_valid = self.placement_valid
                self.check_placement_validity()
                if was_valid and not self.placement_valid:
                    self.play_invalid_sound()
                self.move_delay = current_time + 150
                
            if button_states['fire']:
                if self.placement_valid:
                    success = self.place_current_ship(board)
                    if success and self.sound_manager:
                        self.sound_manager.play_sound("accept")
                else:
                    self.play_invalid_sound()
                
            if button_states['mode']:
                self.showing_confirmation = True
                self.confirmation_option = 0
                if self.sound_manager:
                    self.sound_manager.play_sound("back")  
        
        return {'action': 'none'}
    
    def draw_board(self, board, offset_x, offset_y):
        """Draw a game board at the specified position"""
        for i in range(10):
            letter = chr(65 + i)
            text = self.info_font.render(letter, True, self.WHITE)
            self.screen.blit(text, (offset_x + i * self.cell_size + self.cell_size // 3, offset_y - 30))
            
            number = str(i + 1)
            text = self.info_font.render(number, True, self.WHITE)
            self.screen.blit(text, (offset_x - 30, offset_y + i * self.cell_size + self.cell_size // 3))
        
        for y in range(10):
            for x in range(10):
                cell_x = offset_x + x * self.cell_size
                cell_y = offset_y + y * self.cell_size
                
                cell_state = board.board[y, x]
                
                if cell_state == CellState.EMPTY.value:
                    color = (50, 50, 50) 
                elif cell_state == CellState.SHIP.value:
                    color = self.SHIP_COLOR  
                else:
                    color = (100, 100, 100) 
                
                pygame.draw.rect(self.screen, color, (cell_x, cell_y, self.cell_size - 2, self.cell_size - 2))
                
        if board == (self.player1_board if self.current_player == 1 else self.player2_board):
            self.draw_ship_preview(offset_x, offset_y)
    
    def draw_ship_preview(self, offset_x, offset_y):
        """Draw the current ship preview at cursor position"""
        if self.current_ship_index >= len(self.ship_types):
            return
            
        ship_name, ship_length = self.ship_types[self.current_ship_index]
        preview_color = self.SHIP_COLOR if self.placement_valid else self.INVALID_COLOR
        
        for i in range(ship_length):
            preview_x = self.cursor_y
            preview_y = self.cursor_x
            
            if self.current_ship_horizontal:
                preview_x += i
            else:
                preview_y += i
                
            if preview_x >= 10 or preview_y >= 10:
                continue
                
            cell_x = offset_x + preview_x * self.cell_size
            cell_y = offset_y + preview_y * self.cell_size
            
            pygame.draw.rect(self.screen, preview_color, (cell_x, cell_y, self.cell_size - 2, self.cell_size - 2))
            
        cursor_width = self.cell_size + 2
        cursor_height = self.cell_size + 2

        if self.current_ship_horizontal:
            cursor_width = self.ship_types[self.current_ship_index][1] * self.cell_size + 2
        else:
            cursor_height = self.ship_types[self.current_ship_index][1] * self.cell_size + 2

        cursor_rect = pygame.Rect(
            offset_x + self.cursor_y * self.cell_size - 2,
            offset_y + self.cursor_x * self.cell_size - 2,
            cursor_width,
            cursor_height
        )
        pygame.draw.rect(self.screen, self.HIGHLIGHT_COLOR, cursor_rect, 2)
    
    def draw_ship_list(self, x, y):
        """Draw the list of ships to place with their current status"""
        title = self.title_font.render("Ships:", True, self.WHITE)
        self.screen.blit(title, (x, y))
        
        y_offset = 40
        for i, (ship_name, ship_length) in enumerate(self.ship_types):
            if i < self.current_ship_index:
                status = "✓"  
                color = (0, 255, 0)  
            elif i == self.current_ship_index:
                status = "►"  
                color = (255, 255, 0)  
            else:
                status = "○" 
                color = (200, 200, 200)  
                
            text = self.info_font.render(f"{status} {ship_name} ({ship_length})", True, color)
            self.screen.blit(text, (x, y + y_offset))
            y_offset += 30
    
    def draw_controls_help(self):
        """Draw help text for controls"""
        controls = [
            "Up/Down/Left/Right: Move",
            "Fire: Place Ship",
            "Mode: Reset",
            "Rotate: Change Orientation"
        ]
        
        y_offset = self.height - (len(controls) * 25 + 20)
        for control in controls:
            text = self.info_font.render(control, True, self.LIGHT_GRAY)
            self.screen.blit(text, (20, y_offset))
            y_offset += 25
    
    def draw_confirmation_dialog(self):
        """Draw the reset confirmation dialog"""
        dialog_width = 300
        dialog_height = 200
        dialog_rect = pygame.Rect(
            (self.width - dialog_width) // 2,
            (self.height - dialog_height) // 2,
            dialog_width,
            dialog_height
        )
        pygame.draw.rect(self.screen, (50, 50, 50), dialog_rect)
        pygame.draw.rect(self.screen, self.WHITE, dialog_rect, 2)
        
        title = self.title_font.render("Reset Placement?", True, self.WHITE)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 2 - 60))
        self.screen.blit(title, title_rect)
        
        message = self.info_font.render("All ships will be removed.", True, self.LIGHT_GRAY)
        message_rect = message.get_rect(center=(self.width // 2, self.height // 2 - 20))
        self.screen.blit(message, message_rect)
        
        continue_color = self.HIGHLIGHT_COLOR if self.confirmation_option == 0 else self.WHITE
        reset_color = self.HIGHLIGHT_COLOR if self.confirmation_option == 1 else self.WHITE
        
        continue_text = self.info_font.render("Continue Placement", True, continue_color)
        continue_rect = continue_text.get_rect(center=(self.width // 2, self.height // 2 + 20))
        self.screen.blit(continue_text, continue_rect)
        
        reset_text = self.info_font.render("Reset All Ships", True, reset_color)
        reset_rect = reset_text.get_rect(center=(self.width // 2, self.height // 2 + 60))
        self.screen.blit(reset_text, reset_rect)
        
    def show_player_setup_screen(self, player_number):
        """
        Show an introductory screen for a player to prepare for ship placement
        
        Args:
            player_number (int): Player number (1 or 2)
        """
        self.screen.fill(config.selected_background_color)
        
        title = self.title_font.render(f"PLAYER {player_number} SHIP PLACEMENT", True, self.WHITE)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 3 - 40))
        self.screen.blit(title, title_rect)
        
        message1 = self.info_font.render(f"Player {player_number}, get ready to place your ships!", True, self.LIGHT_BLUE)
        message1_rect = message1.get_rect(center=(self.width // 2, self.height // 2 - 30))
        self.screen.blit(message1, message1_rect)
        
        ships_text = self.info_font.render("You will place the following ships:", True, self.LIGHT_GRAY)
        ships_text_rect = ships_text.get_rect(center=(self.width // 2, self.height // 2 + 10))
        self.screen.blit(ships_text, ships_text_rect)
        
        y_offset = self.height // 2 + 40
        y_spacing = int(self.height * 0.025)  
        
        for ship_name, ship_length in self.ship_types:
            ship_info = self.info_font.render(f"{ship_name} ({ship_length} spaces)", True, self.LIGHT_GRAY)
            ship_info_rect = ship_info.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(ship_info, ship_info_rect)
            y_offset += y_spacing
        
        prompt = self.info_font.render("Press FIRE button to start placement", True, self.LIGHT_GRAY)
        prompt_rect = prompt.get_rect(center=(self.width // 2, y_offset + y_spacing))
        self.screen.blit(prompt, prompt_rect)
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False
            
            button_states = self.get_button_states()
            if button_states['fire']:
                waiting = False
                
            pygame.time.delay(50)
    
    def show_player_transition_screen(self):
        """
        Show a transition screen between player 1 and player 2 ship placement
        This prevents player 2 from seeing player 1's ship placements
        """
        self.screen.fill(config.selected_background_color)
        
        title = self.title_font.render("PLAYER 1 SHIPS PLACED", True, self.WHITE)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 3 - 40))
        self.screen.blit(title, title_rect)
        
        message1 = self.info_font.render("Pass the device to Player 2", True, self.LIGHT_BLUE)
        message1_rect = message1.get_rect(center=(self.width // 2, self.height // 2 - 30))
        self.screen.blit(message1, message1_rect)
        
        message2 = self.info_font.render("Player 2 will now place their ships", True, self.LIGHT_GRAY)
        message2_rect = message2.get_rect(center=(self.width // 2, self.height // 2 + 10))
        self.screen.blit(message2, message2_rect)
        
        prompt = self.info_font.render("Press FIRE button to continue", True, self.LIGHT_GRAY)
        prompt_rect = prompt.get_rect(center=(self.width // 2, self.height // 2 + 80))
        self.screen.blit(prompt, prompt_rect)
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False
            
            button_states = self.get_button_states()
            if button_states['fire']:
                waiting = False
                
            pygame.time.delay(50)
    
    def run(self):
        """
        Run the ship placement screen
        
        Returns:
            tuple: (player1_board, player2_board) - The finalized game boards
        """
        clock = pygame.time.Clock()
        
        if self.ai_mode:
            self.place_ai_ships()
        else:
            self.show_player_setup_screen(1)
        
        self.check_placement_validity()
        
        running = True
        while running and not self.placement_complete:
            self.screen.fill(config.selected_background_color)
            
            if self.ai_mode:
                title = self.title_font.render("Place Your Ships", True, self.WHITE)
            else:
                player_text = f"Player {self.current_player}"
                title = self.title_font.render(f"{player_text} - Place Your Ships", True, self.WHITE)
            
            title_rect = title.get_rect(center=(self.width // 2, 40))
            self.screen.blit(title, title_rect)
            
            if self.sound_manager and self.sound_manager.is_playing and pygame.mixer.music.get_busy():
                self.sound_manager.draw_now_playing(self.screen, 20, 20, self.info_font, width=200, height=40)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                
                if self.sound_manager:
                    self.sound_manager.handle_music_end_event(event)
            
            result = self.handle_input()
            if result['action'] == 'continue_game':
                if self.placement_complete:
                    running = False
            
            if self.current_player == 1:
                self.draw_board(self.player1_board, self.grid_offset_x, self.grid_offset_y)
            else:
                self.draw_board(self.player2_board, self.grid_offset_x, self.grid_offset_y)
            
            ship_list_x = self.grid_offset_x + (self.cell_size * 10) + 50
            ship_list_y = self.grid_offset_y
            self.draw_ship_list(ship_list_x, ship_list_y)
            
            self.draw_controls_help()
            
            if self.current_ship_index < len(self.ship_types):
                ship_name, ship_length = self.ship_types[self.current_ship_index]
                orientation = "Horizontal" if self.current_ship_horizontal else "Vertical"
                ship_info = self.info_font.render(
                    f"Placing: {ship_name} ({ship_length}) - {orientation}", 
                    True, 
                    self.WHITE
                )
                ship_info_rect = ship_info.get_rect(center=(self.width // 2, self.grid_offset_y - 30))
                self.screen.blit(ship_info, ship_info_rect)
            
            if self.showing_confirmation:
                self.draw_confirmation_dialog()
            
            pygame.display.flip()
            clock.tick(30)
        
        return self.player1_board, self.player2_board