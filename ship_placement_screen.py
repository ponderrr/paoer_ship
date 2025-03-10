import pygame
import random
import time
from src.utils.constants import SHIP_TYPES
from src.board.game_board import GameBoard, CellState

class ShipPlacementScreen:
    def __init__(self, screen, gpio_handler=None, ai_mode=True, difficulty="Medium"):
        """
        Initialize the ship placement screen
        
        Args:
            screen: Pygame screen surface
            gpio_handler: GPIO interface for button inputs
            ai_mode: Whether playing against AI (True) or another player (False)
            difficulty: AI difficulty level if ai_mode is True
        """
        self.screen = screen
        self.gpio_handler = gpio_handler
        self.ai_mode = ai_mode
        self.difficulty = difficulty
        
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
        self.placement_valid = True
        
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
    
    def place_current_ship(self, board):
        """Place the current ship on the board"""
        ship_name, ship_length = self.ship_types[self.current_ship_index]
        
        success = board.place_ship(
            self.cursor_x, 
            self.cursor_y, 
            ship_length, 
            self.current_ship_horizontal
        )
        
        if success:
            self.current_ship_index += 1
            
            # Reset position for next ship
            self.cursor_x = 0
            self.cursor_y = 0
            
            # Check if all ships have been placed
            if self.current_ship_index >= len(self.ship_types):
                if self.ai_mode or self.current_player == 2:
                    self.placement_complete = True
                else:
                    # Move to player 2 setup
                    self.current_player = 2
                    self.current_ship_index = 0
                    self.current_ship_horizontal = True
        
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
                    self.move_delay = current_time + 200
                
                elif button_states['fire']:
                    if self.confirmation_option == 0:  # Continue
                        self.showing_confirmation = False
                        return {'action': 'continue_game'}
                    else:  # Reset
                        self.showing_confirmation = False
                        self.reset_placement()
                
                return {'action': 'none'}
            
            # Handle regular ship placement
            board = self.player1_board if self.current_player == 1 else self.player2_board
            ship_name, ship_length = self.ship_types[self.current_ship_index]
            
            moved = False
            
            # Up button pressed
            if button_states['up'] and self.cursor_y > 0:
                self.cursor_y -= 1
                moved = True
                
            # Down button pressed
            if button_states['down'] and self.cursor_y < 9:
                self.cursor_y += 1
                moved = True
                
            # Left button pressed
            if button_states['left'] and self.cursor_x > 0:
                self.cursor_x -= 1
                moved = True
                
            # Right button pressed
            if button_states['right'] and self.cursor_x < 9:
                self.cursor_x += 1
                moved = True
                
            # Rotate button pressed
            if button_states['rotate']:
                self.current_ship_horizontal = not self.current_ship_horizontal
                moved = True
                
            # Check if the current placement is valid after movement
            if moved:
                self.placement_valid = self.can_place_ship(
                    board, 
                    self.cursor_x, 
                    self.cursor_y, 
                    ship_length, 
                    self.current_ship_horizontal
                )
                self.move_delay = current_time + 150
                
            # Fire button pressed (place ship)
            if button_states['fire'] and self.placement_valid:
                self.place_current_ship(board)
                
            # Mode button pressed (reset placement)
            if button_states['mode']:
                self.showing_confirmation = True
                self.confirmation_option = 0
        
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
        cursor_rect = pygame.Rect(
            offset_x + self.cursor_y * self.cell_size - 2,
            offset_y + self.cursor_x * self.cell_size - 2,
            self.cell_size + 2,
            self.cell_size + 2
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
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
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