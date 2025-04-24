import pygame
import random
import time
import sys
from src.utils.constants import SHIP_TYPES
from src.board.game_board import GameBoard, CellState

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
        
        # Screen dimensions
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Grid settings
        self.cell_size = 30
        self.grid_offset_x = 150
        self.grid_offset_y = 100
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BLUE = (50, 150, 255)
        self.LIGHT_BLUE = (80, 170, 255)
        self.LIGHT_GRAY = (180, 180, 180)
        self.SHIP_COLOR = (0, 255, 0)
        self.INVALID_COLOR = (255, 100, 100)
        self.HIGHLIGHT_COLOR = (255, 255, 0)
        
        # Fonts
        self.title_font = pygame.font.Font(None, 36)
        self.info_font = pygame.font.Font(None, 24)
        
        # Game boards
        self.player1_board = GameBoard()
        self.player2_board = GameBoard()
        
        # Current ship being placed
        self.ship_types = list(SHIP_TYPES.items())
        self.current_ship_index = 0
        self.current_ship_horizontal = True
        
        # Current player (1 or 2)
        self.current_player = 1
        
        # Cursor position for ship placement
        self.cursor_x = 0
        self.cursor_y = 0
        
        # Movement delay for cursor
        self.move_delay = 0
        
        # Placement state
        self.placement_complete = False
        # Check initial placement validity right away
        self.placement_valid = True  # Start with True
        
        # Confirmation dialog state
        self.showing_confirmation = False
        self.confirmation_option = 0  # 0 = Continue, 1 = Reset
        
        # GPIO button press handling
        self.last_button_states = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'fire': False,
            'mode': False,
            'rotate': False  # New button for rotation
        }
    
    def play_invalid_sound(self):
        """Play the invalid action sound"""
        if self.sound_manager:
            self.sound_manager.play_sound("back")  # Use back sound for invalid actions
    
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
        # Check board limits
        if horizontal:
            if y + length > board.size:
                return False
        else:
            if x + length > board.size:
                return False
                
        # Check for overlap with existing ships
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
    
# Fix for the place_current_ship method - correct indentation
# Replace the existing method with this properly indented version

    def place_current_ship(self, board):
        """Place the current ship on the board"""
        ship_name, ship_length = self.ship_types[self.current_ship_index]
        
        # Double-check validity before placement
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
            # Play success sound
            if self.sound_manager:
                self.sound_manager.play_sound("hit")  # Using hit sound for successful placement
                
            self.current_ship_index += 1
            
            # Reset position for next ship
            self.cursor_x = 0
            self.cursor_y = 0
            
            # Check validity for next ship immediately
            self.check_placement_validity()
            
            # Check if all ships have been placed
            if self.current_ship_index >= len(self.ship_types):
                if self.ai_mode or self.current_player == 2:
                    self.placement_complete = True
                    # Play completion sound
                    if self.sound_manager:
                        self.sound_manager.play_sound("ship_sunk")  # Using ship_sunk for completion
                else:
                    # Show player transition screen before moving to player 2
                    self.show_player_transition_screen()
                    # Show player 2 setup screen
                    self.show_player_setup_screen(2)
                    # Move to player 2 setup
                    self.current_player = 2
                    self.current_ship_index = 0
                    self.current_ship_horizontal = True
                    # Check validity for the first ship of player 2
                    self.check_placement_validity()
        else:
            # This should rarely happen since we check validity before placement,
            # but play error sound just in case
            self.play_invalid_sound()
        
        return success
    
    def place_ai_ships(self):
        """Randomly place ships for AI opponent"""
        self.player2_board.reset_board()
        
        for ship_name, ship_length in self.ship_types:
            placed = False
            attempt_count = 0
            max_attempts = 100  # Prevent infinite loop
            
            while not placed and attempt_count < max_attempts:
                x = random.randint(0, 9)
                y = random.randint(0, 9)
                horizontal = random.choice([True, False])
                
                placed = self.player2_board.place_ship(x, y, ship_length, horizontal)
                attempt_count += 1
                
            if not placed:
                # If we failed to place a ship after max attempts, reset and try again
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
        
        # Check validity for the first ship after reset
        self.check_placement_validity()
    
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
                'rotate': keys[pygame.K_r]  # Use 'r' key for rotation in keyboard mode
            }
        
        # Edge detection (only trigger on button press, not hold)
        button_states = {}
        for key in current_states:
            button_states[key] = current_states[key] and not self.last_button_states[key]
            self.last_button_states[key] = current_states[key]
            
        return button_states
    
   # Update to the handle_input method in ShipPlacementScreen

# Fix for the handle_input method - correct indentation
# Replace the existing method with this properly indented version

    def handle_input(self):
        """Handle user input for ship placement"""
        button_states = self.get_button_states()
        current_time = pygame.time.get_ticks()
        
        # Only process movement if enough time has passed (to prevent too fast movement)
        if current_time > self.move_delay:
            # Handle confirmation dialog if it's showing
            if self.showing_confirmation:
                if button_states['up'] or button_states['down']:
                    self.confirmation_option = 1 - self.confirmation_option  # Toggle between 0 and 1
                    # Play navigation sound if sound manager exists
                    if self.sound_manager:
                        self.sound_manager.play_sound("navigate_up" if button_states['up'] else "navigate_down")
                    self.move_delay = current_time + 200
                
                elif button_states['fire']:
                    if self.confirmation_option == 0:  # Continue
                        self.showing_confirmation = False
                        if self.sound_manager:
                            self.sound_manager.play_sound("accept")
                        return {'action': 'continue_game'}
                    else:  # Reset
                        self.showing_confirmation = False
                        if self.sound_manager:
                            self.sound_manager.play_sound("accept")
                        self.reset_placement()
                
                return {'action': 'none'}
            
            # Handle regular ship placement
            if self.current_ship_index >= len(self.ship_types):
                return {'action': 'none'}
                
            board = self.player1_board if self.current_player == 1 else self.player2_board
            ship_name, ship_length = self.ship_types[self.current_ship_index]
            
            moved = False
            hit_boundary = False
            
            # Up button pressed
            if button_states['up']:
                if self.cursor_x > 0:  # Note: cursor_x is row, cursor_y is column
                    self.cursor_x -= 1
                    moved = True
                    if self.sound_manager:
                        self.sound_manager.play_sound("navigate_up")
                else:
                    hit_boundary = True
                    
            # Down button pressed
            if button_states['down']:
                # Check if moving down would make the ship go off board
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
                
            # Left button pressed
            if button_states['left']:
                if self.cursor_y > 0:
                    self.cursor_y -= 1
                    moved = True
                    if self.sound_manager:
                        self.sound_manager.play_sound("navigate_up")  # Using up sound for left
                else:
                    hit_boundary = True
                
            # Right button pressed
            if button_states['right']:
                # Check if moving right would make the ship go off board
                max_col = 9
                if self.current_ship_horizontal and ship_length > 1:
                    max_col = 10 - ship_length
                
                if self.cursor_y < max_col:
                    self.cursor_y += 1
                    moved = True
                    if self.sound_manager:
                        self.sound_manager.play_sound("navigate_down")  # Using down sound for right
                else:
                    hit_boundary = True
                    
            # Play boundary hit sound
            if hit_boundary:
                self.play_invalid_sound()
                self.move_delay = current_time + 150
                
            # Rotate button pressed
            if button_states['rotate']:
                # Check if rotation would be valid (not off board)
                if self.current_ship_horizontal:
                    # Trying to switch to vertical
                    if self.cursor_x + ship_length <= 10:
                        self.current_ship_horizontal = False
                        moved = True
                        if self.sound_manager:
                            self.sound_manager.play_sound("accept")  # Use accept sound for successful rotation
                    else:
                        hit_boundary = True
                        self.play_invalid_sound()
                else:
                    # Trying to switch to horizontal
                    if self.cursor_y + ship_length <= 10:
                        self.current_ship_horizontal = True
                        moved = True
                        if self.sound_manager:
                            self.sound_manager.play_sound("accept")  # Use accept sound for successful rotation
                    else:
                        hit_boundary = True
                        self.play_invalid_sound()
                
            # Check if the current placement is valid after movement
            if moved:
                was_valid = self.placement_valid
                self.check_placement_validity()
                # Play error sound if movement made placement invalid
                if was_valid and not self.placement_valid:
                    self.play_invalid_sound()
                self.move_delay = current_time + 150
                
            # Fire button pressed (place ship)
            if button_states['fire']:
                if self.placement_valid:
                    success = self.place_current_ship(board)
                    if success and self.sound_manager:
                        self.sound_manager.play_sound("accept")
                else:
                    # Play invalid sound for invalid placement attempt
                    self.play_invalid_sound()
                
            # Mode button pressed (reset placement)
            if button_states['mode']:
                self.showing_confirmation = True
                self.confirmation_option = 0
                if self.sound_manager:
                    self.sound_manager.play_sound("back")  # Use back sound for reset dialog
        
        return {'action': 'none'}
    
    def draw_board(self, board, offset_x, offset_y):
        """Draw a game board at the specified position"""
        # Draw grid labels
        for i in range(10):
            # Column labels (A-J)
            letter = chr(65 + i)
            text = self.info_font.render(letter, True, self.WHITE)
            self.screen.blit(text, (offset_x + i * self.cell_size + 10, offset_y - 30))
            
            # Row labels (1-10)
            number = str(i + 1)
            text = self.info_font.render(number, True, self.WHITE)
            self.screen.blit(text, (offset_x - 30, offset_y + i * self.cell_size + 10))
        
        # Draw grid cells
        for y in range(10):
            for x in range(10):
                cell_x = offset_x + y * self.cell_size
                cell_y = offset_y + x * self.cell_size
                
                # Get cell state
                cell_state = board.board[x, y]
                
                # Determine cell color based on state
                if cell_state == CellState.EMPTY.value:
                    color = (50, 50, 50)  # Empty cell
                elif cell_state == CellState.SHIP.value:
                    color = self.SHIP_COLOR  # Ship
                else:
                    color = (100, 100, 100)  # Other states (shouldn't occur during placement)
                
                # Draw cell
                pygame.draw.rect(self.screen, color, (cell_x, cell_y, self.cell_size - 2, self.cell_size - 2))
                
        # Draw cursor and ship preview for current player's board
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
                
            # Skip if outside the board
            if preview_x >= 10 or preview_y >= 10:
                continue
                
            cell_x = offset_x + preview_x * self.cell_size
            cell_y = offset_y + preview_y * self.cell_size
            
            # Draw ship segment
            pygame.draw.rect(self.screen, preview_color, (cell_x, cell_y, self.cell_size - 2, self.cell_size - 2))
            
        # Draw cursor highlight around the ship's starting position
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
            # Determine status
            if i < self.current_ship_index:
                status = "✓"  # Placed
                color = (0, 255, 0)  # Green
            elif i == self.current_ship_index:
                status = "►"  # Current
                color = (255, 255, 0)  # Yellow
            else:
                status = "○"  # Pending
                color = (200, 200, 200)  # Gray
                
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
        
        y_offset = self.height - 120
        for control in controls:
            text = self.info_font.render(control, True, self.LIGHT_GRAY)
            self.screen.blit(text, (20, y_offset))
            y_offset += 25
    
    def draw_confirmation_dialog(self):
        """Draw the reset confirmation dialog"""
        # Dialog background
        dialog_rect = pygame.Rect(self.width // 2 - 150, self.height // 2 - 100, 300, 200)
        pygame.draw.rect(self.screen, (50, 50, 50), dialog_rect)
        pygame.draw.rect(self.screen, self.WHITE, dialog_rect, 2)
        
        # Dialog title
        title = self.title_font.render("Reset Placement?", True, self.WHITE)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 2 - 60))
        self.screen.blit(title, title_rect)
        
        # Dialog message
        message = self.info_font.render("All ships will be removed.", True, self.LIGHT_GRAY)
        message_rect = message.get_rect(center=(self.width // 2, self.height // 2 - 20))
        self.screen.blit(message, message_rect)
        
        # Dialog options
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
        # Fill screen with a dark background
        self.screen.fill(self.BLACK)
        
        # Draw title
        title = self.title_font.render(f"PLAYER {player_number} SHIP PLACEMENT", True, self.WHITE)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 3 - 40))
        self.screen.blit(title, title_rect)
        
        # Draw messages
        message1 = self.info_font.render(f"Player {player_number}, get ready to place your ships!", True, self.LIGHT_BLUE)
        message1_rect = message1.get_rect(center=(self.width // 2, self.height // 2 - 30))
        self.screen.blit(message1, message1_rect)
        
        # Draw ships info
        ships_text = self.info_font.render("You will place the following ships:", True, self.LIGHT_GRAY)
        ships_text_rect = ships_text.get_rect(center=(self.width // 2, self.height // 2 + 10))
        self.screen.blit(ships_text, ships_text_rect)
        
        y_offset = self.height // 2 + 40
        for ship_name, ship_length in self.ship_types:
            ship_info = self.info_font.render(f"{ship_name} ({ship_length} spaces)", True, self.LIGHT_GRAY)
            ship_info_rect = ship_info.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(ship_info, ship_info_rect)
            y_offset += 25
        
        # Draw continue prompt
        prompt = self.info_font.render("Press FIRE button to start placement", True, self.LIGHT_GRAY)
        prompt_rect = prompt.get_rect(center=(self.width // 2, y_offset + 30))
        self.screen.blit(prompt, prompt_rect)
        
        # Update display
        pygame.display.flip()
        
        # Wait for fire button press
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False
            
            # Check GPIO buttons
            button_states = self.get_button_states()
            if button_states['fire']:
                waiting = False
                
            # Small delay to prevent CPU hogging
            pygame.time.delay(100)
    
    def show_player_transition_screen(self):
        """
        Show a transition screen between player 1 and player 2 ship placement
        This prevents player 2 from seeing player 1's ship placements
        """
        # Fill screen with a dark background
        self.screen.fill(self.BLACK)
        
        # Draw title
        title = self.title_font.render("PLAYER 1 SHIPS PLACED", True, self.WHITE)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 3 - 40))
        self.screen.blit(title, title_rect)
        
        # Draw message
        message1 = self.info_font.render("Pass the device to Player 2", True, self.LIGHT_BLUE)
        message1_rect = message1.get_rect(center=(self.width // 2, self.height // 2 - 30))
        self.screen.blit(message1, message1_rect)
        
        message2 = self.info_font.render("Player 2 will now place their ships", True, self.LIGHT_GRAY)
        message2_rect = message2.get_rect(center=(self.width // 2, self.height // 2 + 10))
        self.screen.blit(message2, message2_rect)
        
        # Draw continue prompt
        prompt = self.info_font.render("Press FIRE button to continue", True, self.LIGHT_GRAY)
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
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False
            
            # Check GPIO buttons
            button_states = self.get_button_states()
            if button_states['fire']:
                waiting = False
                
            # Small delay to prevent CPU hogging
            pygame.time.delay(100)
    
    # Use only one run method with the correct indentation
# Keep only this version and delete any duplicate run methods

    def run(self):
        """
        Run the ship placement screen
        
        Returns:
            tuple: (player1_board, player2_board) - The finalized game boards
        """
        clock = pygame.time.Clock()
        
        # Place AI ships if in AI mode
        if self.ai_mode:
            self.place_ai_ships()
        else:
            # Show player 1 setup screen
            self.show_player_setup_screen(1)
        
        # Check validity of initial position (0,0) with first ship
        self.check_placement_validity()
        
        running = True
        while running and not self.placement_complete:
            # Fill background
            self.screen.fill(self.BLACK)
            
            # Draw title based on current state
            if self.ai_mode:
                title = self.title_font.render("Place Your Ships", True, self.WHITE)
            else:
                player_text = f"Player {self.current_player}"
                title = self.title_font.render(f"{player_text} - Place Your Ships", True, self.WHITE)
            
            title_rect = title.get_rect(center=(self.width // 2, 40))
            self.screen.blit(title, title_rect)
            
            # Display Now Playing information if sound manager exists and music is playing
            if self.sound_manager and self.sound_manager.is_playing and pygame.mixer.music.get_busy():
                self.sound_manager.draw_now_playing(self.screen, 20, 20, self.info_font, width=200, height=40)
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                
                # Handle music end event if sound manager exists
                if self.sound_manager:
                    self.sound_manager.handle_music_end_event(event)
            
            # Handle input
            result = self.handle_input()
            if result['action'] == 'continue_game':
                if self.placement_complete:
                    running = False
            
            # Draw the game board
            if self.current_player == 1:
                self.draw_board(self.player1_board, self.grid_offset_x, self.grid_offset_y)
            else:
                self.draw_board(self.player2_board, self.grid_offset_x, self.grid_offset_y)
            
            # Draw ship list
            self.draw_ship_list(self.width - 200, 100)
            
            # Draw controls help
            self.draw_controls_help()
            
            # Draw current ship info
            if self.current_ship_index < len(self.ship_types):
                ship_name, ship_length = self.ship_types[self.current_ship_index]
                orientation = "Horizontal" if self.current_ship_horizontal else "Vertical"
                ship_info = self.info_font.render(
                    f"Placing: {ship_name} ({ship_length}) - {orientation}", 
                    True, 
                    self.WHITE
                )
                self.screen.blit(ship_info, (self.grid_offset_x, self.grid_offset_y - 60))
            
            # Draw confirmation dialog if showing
            if self.showing_confirmation:
                self.draw_confirmation_dialog()
            
            # Update display
            pygame.display.flip()
            clock.tick(30)
        
        return self.player1_board, self.player2_board