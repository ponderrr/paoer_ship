import pygame
import sys
import time
import numpy as np
import random
from src.board.game_board import GameBoard, CellState
from ship_placement_screen import ShipPlacementScreen
from src.game.ai_opponent import AIOpponent, AIDifficulty
from src.utils.image_display import ImageDisplay

# Try to import GPIO support
try:
    import gpiod
    IS_RASPBERRY_PI = True
except ImportError:
    IS_RASPBERRY_PI = False

# Initialize Pygame
pygame.init()

# Screen settings - smaller for better performance
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pao'er Ship")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
LIGHT_BLUE = (80, 170, 255)
LIGHT_GRAY = (180, 180, 180)

# Load fonts
pygame.font.init()
title_font = pygame.font.Font(None, 50)
button_font = pygame.font.Font(None, 30)

class GPIOHandler:
    def __init__(self):
        self.chip = None
        self.lines = {}
        self.last_states = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'fire': False,
            'mode': False,
            'rotate': False  # Add rotate button state
        }
        
        # Define GPIO pins for buttons (BCM numbering)
        self.PIN_UP = 17    # Pin 11
        self.PIN_DOWN = 27  # Pin 13
        self.PIN_LEFT = 22  # Pin 15
        self.PIN_RIGHT = 23 # Pin 16
        self.PIN_FIRE = 24  # Pin 18
        self.PIN_MODE = 25  # Pin 22
        self.PIN_ROTATE = 26  # Pin 37 (TODO: Update this when the hardware is connected)
        
        if IS_RASPBERRY_PI:
            self.setup()
    
    def setup(self):
        try:
            # Try to open the GPIO chip for Pi 5
            self.chip = gpiod.Chip("gpiochip4")
            
            # Pin to button name mapping
            pin_button_map = {
                self.PIN_UP: 'up',
                self.PIN_DOWN: 'down',
                self.PIN_LEFT: 'left',
                self.PIN_RIGHT: 'right',
                self.PIN_FIRE: 'fire',
                self.PIN_MODE: 'mode',
                self.PIN_ROTATE: 'rotate'  # Add the new rotate button
            }
            
            # Set up all the lines using the older API (which we know works)
            for pin, button_name in pin_button_map.items():
                line = self.chip.get_line(pin)
                line.request(consumer=f"paoer-ship-{button_name}", type=gpiod.LINE_REQ_DIR_IN)
                self.lines[pin] = line
                
        except Exception as e:
            print(f"Error setting up GPIO: {e}")
            if self.chip:
                self.chip.close()
                self.chip = None
    
    def cleanup(self):
        if self.chip:
            self.chip.close()
            self.chip = None
    
    def get_button_states(self):
        actions = {
            'up': False,
            'down': False, 
            'left': False,
            'right': False,
            'fire': False,
            'mode': False,
            'rotate': False  # Include rotate in actions
        }
        
        if not IS_RASPBERRY_PI or not self.chip:
            return actions
        
        try:
            # Pin to button name mapping
            pin_button_map = {
                self.PIN_UP: 'up',
                self.PIN_DOWN: 'down',
                self.PIN_LEFT: 'left',
                self.PIN_RIGHT: 'right',
                self.PIN_FIRE: 'fire',
                self.PIN_MODE: 'mode',
                self.PIN_ROTATE: 'rotate'  # Add the new rotate button
            }
            
            for pin, button_name in pin_button_map.items():
                if pin not in self.lines:
                    continue
                
                # Read line value (active LOW with pull-up)
                line = self.lines[pin]
                # For buttons with pull-up resistors, 0 means pressed (active low)
                current_state = (line.get_value() == 0)
                
                # Only register a press when the state changes from released to pressed
                if current_state and not self.last_states[button_name]:
                    actions[button_name] = True
                
                # Update last state
                self.last_states[button_name] = current_state
                
        except Exception as e:
            print(f"Error reading GPIO: {e}")
        
        return actions

# Simple button class
class Button:
    def __init__(self, x, y, width, height, text, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.base_color = BLUE
        self.hover_color = LIGHT_BLUE
        self.current_color = self.base_color
        self.hovered = False
        self.selected = False

    def update(self):
        self.current_color = self.hover_color if (self.selected or self.hovered) else self.base_color

    def draw(self, screen):
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=5)
        text_surface = button_font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.action()

# Forward declarations for functions that reference each other
def quit_game():
    gpio_handler.cleanup()
    pygame.quit()
    sys.exit()

def settings_screen():
    """Simplified settings screen"""
    screen.fill(BLACK)
    font = pygame.font.Font(None, 36)
    text = font.render("Settings Screen (Placeholder)", True, WHITE)
    screen.blit(text, (WIDTH//2 - 180, HEIGHT//2))
    
    back_text = font.render("Press any key to return to menu", True, WHITE)
    screen.blit(back_text, (WIDTH//2 - 180, HEIGHT//2 + 50))
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False
            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Check for GPIO button presses
        button_states = gpio_handler.get_button_states()
        if any(button_states.values()):
            waiting = False
        
        # Small delay to prevent CPU hogging
        time.sleep(0.01)

def process_shot(x, y, shooter_board, target_board, shots_set):
    """Process a shot from one player to another's board"""
    if (x, y) in shots_set:
        return False, False  # Shot already taken, no ship sunk
        
    shots_set.add((x, y))
    
    # Check if hit and if ship was sunk
    hit = False
    ship_sunk = False
    
    for ship in target_board.ships:
        if ship.receive_hit(x, y):
            hit = True
            ship_sunk = ship.is_sunk()
            break
            
    # Update the board state at the target location
    if hit:
        target_board.board[x, y] = CellState.HIT.value
    else:
        target_board.board[x, y] = CellState.MISS.value
            
    return hit, ship_sunk

def game_screen(ai_mode=True, difficulty="Medium", player1_board=None, player2_board=None):
    """
    Game screen where the actual gameplay happens after ship placement
    
    Args:
        ai_mode (bool): Whether playing against AI (True) or another player (False)
        difficulty (str): AI difficulty level if ai_mode is True
        player1_board: Game board for player 1
        player2_board: Game board for player 2 (or AI)
    """
    try:
    
        
        # Import necessary modules
        import numpy as np
        import random
        from turn_transition_screen import TurnTransitionScreen
        from exit_confirmation import ExitConfirmation
        from src.game.ai_opponent import AIOpponent, AIDifficulty
        from src.utils.image_display import ImageDisplay
        
        # Initialize game components
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)
        
        # Create empty boards if none were provided
        if player1_board is None:
            player1_board = GameBoard()
        if player2_board is None:
            player2_board = GameBoard()
        
        # Initialize transition screen and exit confirmation dialogs
        transition_screen = TurnTransitionScreen(screen, gpio_handler)
        exit_dialog = ExitConfirmation(screen, gpio_handler)
        image_display = ImageDisplay(screen)
        
        # Define helper function for game over check
        def check_game_over():
            """Check if the game is over (all ships sunk)"""
            player1_lost = all(ship.is_sunk() for ship in player1_board.ships)
            player2_lost = all(ship.is_sunk() for ship in player2_board.ships)
            
            if player1_lost:
                return 2  # Player 2 (or AI) wins
            elif player2_lost:
                return 1  # Player 1 wins
            return None  # No winner yet
        
        # Set up AI opponent if in AI mode
        ai_opponent = None
        if ai_mode:
            # Map difficulty string to enum
            difficulty_map = {
                "Easy": AIDifficulty.EASY,
                "Medium": AIDifficulty.MEDIUM,
                "Hard": AIDifficulty.HARD,
                "Pao": AIDifficulty.PAO
            }
            
            ai_difficulty = difficulty_map.get(difficulty, AIDifficulty.MEDIUM)
            ai_opponent = AIOpponent(ai_difficulty, player1_board)
            
            # Use the AI's board as player 2's board
            player2_board = ai_opponent.board
        
        # Set up game mode specific variables
        game_mode_text = "VS AI" if ai_mode else "VS Player"
        if ai_mode and difficulty:
            game_mode_text += f" ({difficulty})"
        pao_mode = ai_mode and difficulty == "Pao"
        
        # Game state variables
        current_player = 1  # 1 for player 1, 2 for player 2 (or AI)
        cursor_x, cursor_y = 0, 0
        player1_shots = set()  # Track player 1's shots (x, y)
        player2_shots = set()  # Track player 2's shots (x, y)
        winner = None  # None, 1, or 2
        move_delay = 0  # Delay for cursor movement
        
        # Display boards for each player (what they can see)
        player1_view = np.zeros((10, 10), dtype=int)
        player2_view = np.zeros((10, 10), dtype=int)
        
        # Get player's board state to display their own ships
        player1_own_view = player1_board.get_display_state()
        player2_own_view = player2_board.get_display_state()
        
        # Show initial player screen if in player vs player mode
        if not ai_mode:
            transition_screen.show_player_ready_screen(current_player)
        
        # Wait for next player message if two-player mode
        current_message = ""
        showing_message = False
        message_timer = 0
        showing_exit_dialog = False
        pao_missed = False  # Track if player missed in Pao mode
        
        # Main game loop
        running = True
        while running:
            current_time = pygame.time.get_ticks()
            
            # Fill background
            screen.fill(BLACK)
            
            # Draw game mode
            mode_text = font.render(game_mode_text, True, WHITE)
            screen.blit(mode_text, (WIDTH - 200, 20))
            
            # Draw exit option
            exit_text = small_font.render("Press MODE to exit", True, LIGHT_GRAY)
            screen.blit(exit_text, (20, HEIGHT - 30))
            
            # Handle exit confirmation dialog
            if showing_exit_dialog:
                if exit_dialog.show():
                    running = False  # Exit to main menu
                showing_exit_dialog = False
                continue  # Skip the rest of the loop iteration after dialog
            
            # Determine whose turn it is and which board to display
            if current_player == 1:
                # Player 1's turn - show player 2's board with player 1's shots
                active_board = player2_board
                view_board = player1_view
                shots = player1_shots
                
                # Also show player 1's board with their ships
                own_board = player1_own_view
            else:
                # Player 2's turn - show player 1's board with player 2's shots
                active_board = player1_board
                view_board = player2_view
                shots = player2_shots
                
                # Also show player 2's board with their ships
                own_board = player2_own_view
            
            # Draw opponent board (with shots but not ships)
            # This is the board the current player is firing at
            draw_board(
                screen, 
                font, 
                view_board, 
                150, 
                80, 
                30, 
                cursor_x if current_player == 1 else -1,  # Only show cursor for human player
                cursor_y if current_player == 1 else -1,
                current_player == 1,  # Show cursor only for player 1
                "Opponent's Board"
            )
            
            # Draw player's own board (with ships)
            # This is to see the status of their own ships
            if not winner:
                draw_board(
                    screen,
                    font,
                    own_board,
                    400,
                    80,
                    25,  # Smaller cell size for own board
                    -1,  # No cursor on own board
                    -1,
                    False,
                    "Your Board"
                )
            
            # Draw current player
            if not winner:
                if current_player == 1 or not ai_mode:
                    player_text = font.render(f"Player {current_player}'s Turn", True, WHITE)
                else:
                    player_text = font.render("AI's Turn", True, WHITE)
                screen.blit(player_text, (20, 20))
            
            # Draw status message
            if winner:
                if winner == 1:
                    winner_text = font.render("You Win!", True, (255, 215, 0))
                elif ai_mode:
                    winner_text = font.render("AI Wins!", True, (255, 0, 0))
                else:
                    winner_text = font.render(f"Player {winner} Wins!", True, (255, 215, 0))
                
                screen.blit(winner_text, (WIDTH // 2 - 100, HEIGHT - 100))
                
                restart_text = small_font.render("Press MODE to return to menu", True, WHITE)
                screen.blit(restart_text, (WIDTH // 2 - 120, HEIGHT - 60))
            else:
                if current_player == 1:
                    status_text = small_font.render("Press FIRE to shoot", True, WHITE)
                    screen.blit(status_text, (WIDTH // 2 - 80, HEIGHT - 40))
                else:
                    status_text = small_font.render("AI is thinking...", True, WHITE)
                    screen.blit(status_text, (WIDTH // 2 - 70, HEIGHT - 40))
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                    
                elif event.type == pygame.KEYDOWN and not showing_message:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_TAB:
                        showing_exit_dialog = True
                    
                    if not winner and current_player == 1:  # Only process player 1 input during their turn
                        if event.key == pygame.K_UP and cursor_y > 0:
                            cursor_y -= 1
                        elif event.key == pygame.K_DOWN and cursor_y < 9:
                            cursor_y += 1
                        elif event.key == pygame.K_LEFT and cursor_x > 0:
                            cursor_x -= 1
                        elif event.key == pygame.K_RIGHT and cursor_x < 9:
                            cursor_x += 1
                        elif event.key == pygame.K_SPACE:
                            # Player 1 fires
                            if (cursor_x, cursor_y) not in player1_shots:
                                hit, ship_sunk = process_shot(cursor_x, cursor_y, None, player2_board, player1_shots)
                                
                                # Update the view
                                if hit:
                                    player1_view[cursor_x][cursor_y] = CellState.HIT.value
                                else:
                                    player1_view[cursor_x][cursor_y] = CellState.MISS.value
                                    
                                    # For Pao mode, player immediately loses if they miss
                                    if pao_mode:
                                        # Show miss before ending
                                        screen.fill(BLACK)
                                        draw_board(screen, font, player1_view, 150, 80, 30, cursor_x, cursor_y, True, "Your Shot")
                                        draw_board(screen, font, player1_own_view, 400, 80, 25, -1, -1, False, "Your Board")
                                        
                                        miss_text = small_font.render(f"You fired at {chr(65 + cursor_y)}{cursor_x + 1}: MISS!", True, (0, 0, 255))
                                        screen.blit(miss_text, (WIDTH // 2 - 100, HEIGHT - 70))
                                        
                                        pao_warning = font.render("PAO MODE ACTIVATED - YOU LOSE!", True, (255, 0, 0))
                                        screen.blit(pao_warning, (WIDTH // 2 - 200, HEIGHT - 40))
                                        
                                        pygame.display.flip()
                                        pygame.time.delay(3000)
                                        
                                        # Display Pao image
                                        pao_missed = True
                                        winner = 2  # AI wins
                                        image_display.display_pao_image()
                                        continue
                                
                                # Draw the updated board to show shot result before transition
                                pygame.display.flip()
                                
                                # Check if game over
                                new_winner = check_game_over()
                                if new_winner:
                                    winner = new_winner
                                    # Show the final shot before ending
                                    pygame.display.flip()
                                    # Wait a moment to show the winning shot
                                    time.sleep(1)
                                else:
                                    # Show the shot result
                                    if not ai_mode:
                                        # Show transition screens in player vs player mode
                                        transition_screen.show_turn_result(current_player, cursor_y, cursor_x, hit, ship_sunk)
                                        transition_screen.show_player_ready_screen(2)
                                    else:
                                        # Just show result briefly in AI mode
                                        pygame.display.flip()
                                        time.sleep(1)
                                    
                                    # Switch to next player's turn
                                    current_player = 2
            
            # Check GPIO buttons if not showing message
            if not showing_message:
                button_states = gpio_handler.get_button_states()
                
                # Check for exit button
                if button_states['mode']:
                    showing_exit_dialog = True
                
                # Only process gameplay if no win condition yet and it's player 1's turn
                if not winner and current_player == 1:
                    if button_states['up'] and cursor_y > 0:
                        cursor_y -= 1
                    if button_states['down'] and cursor_y < 9:
                        cursor_y += 1
                    if button_states['left'] and cursor_x > 0:
                        cursor_x -= 1
                    if button_states['right'] and cursor_x < 9:
                        cursor_x += 1
                        
                    if button_states['fire']:
                        # Player 1 fires
                        if (cursor_x, cursor_y) not in player1_shots:
                            hit, ship_sunk = process_shot(cursor_x, cursor_y, None, player2_board, player1_shots)
                            
                            # Update the view
                            if hit:
                                player1_view[cursor_x][cursor_y] = CellState.HIT.value
                            else:
                                player1_view[cursor_x][cursor_y] = CellState.MISS.value
                                
                                # For Pao mode, player immediately loses if they miss
                                if pao_mode:
                                    # Show miss before ending
                                    screen.fill(BLACK)
                                    draw_board(screen, font, player1_view, 150, 80, 30, cursor_x, cursor_y, True, "Your Shot")
                                    draw_board(screen, font, player1_own_view, 400, 80, 25, -1, -1, False, "Your Board")
                                    
                                    miss_text = small_font.render(f"You fired at {chr(65 + cursor_y)}{cursor_x + 1}: MISS!", True, (0, 0, 255))
                                    screen.blit(miss_text, (WIDTH // 2 - 100, HEIGHT - 70))
                                    
                                    pao_warning = font.render("PAO MODE ACTIVATED - YOU LOSE!", True, (255, 0, 0))
                                    screen.blit(pao_warning, (WIDTH // 2 - 200, HEIGHT - 40))
                                    
                                    pygame.display.flip()
                                    pygame.time.delay(3000)
                                    
                                    # Display Pao image
                                    pao_missed = True
                                    winner = 2  # AI wins
                                    image_display.display_pao_image()
                                    continue
                            
                            # Draw the updated board to show shot result before transition
                            pygame.display.flip()
                            
                            # Check if game over
                            new_winner = check_game_over()
                            if new_winner:
                                winner = new_winner
                                # Show the final shot before ending
                                pygame.display.flip()
                                # Wait a moment to show the winning shot
                                time.sleep(1)
                            else:
                                # Show the shot result
                                if not ai_mode:
                                    # Show transition screens in player vs player mode
                                    transition_screen.show_turn_result(current_player, cursor_y, cursor_x, hit, ship_sunk)
                                    transition_screen.show_player_ready_screen(2)
                                else:
                                    # Just show result briefly in AI mode
                                    pygame.display.flip()
                                    time.sleep(1)
                                
                                # Switch to next player's turn
                                current_player = 2
                elif winner:
                    # If there's a winner, pressing any button will return to menu
                    if any(button_states.values()):
                        running = False  # Return to main menu
            
            # AI logic - if it's the AI's turn
            if ai_mode and current_player == 2 and not winner:
                # Add a delay to make the AI feel more human-like
                if difficulty == "Easy":
                    thinking_time = random.uniform(0.5, 1.0)
                elif difficulty == "Medium": 
                    thinking_time = random.uniform(1.0, 1.5)
                else:  # Hard or Pao
                    thinking_time = random.uniform(1.5, 2.0)
                
                # Show thinking message
                screen.fill(BLACK)
                draw_board(screen, font, player2_view, 150, 80, 30, -1, -1, False, "AI's Shot")
                draw_board(screen, font, player1_own_view, 400, 80, 25, -1, -1, False, "Your Board")
                thinking_text = small_font.render("AI is thinking...", True, WHITE)
                thinking_rect = thinking_text.get_rect(center=(WIDTH // 2, HEIGHT - 40))
                screen.blit(thinking_text, thinking_rect)
                pygame.display.flip()
                
                # Wait for the AI to "think"
                pygame.time.delay(int(thinking_time * 1000))
                
                try:
                    # Get AI's shot
                    x, y = ai_opponent.get_shot()
                    
                    # Make sure the coordinates are valid (defensive programming)
                    if not (0 <= x < 10 and 0 <= y < 10):
                        # Fallback to a random valid shot if coordinates are invalid
                      
                        valid_shots = [(i, j) for i in range(10) for j in range(10) if (i, j) not in player2_shots]
                        if valid_shots:
                            x, y = random.choice(valid_shots)
                        else:
                            x, y = 0, 0  # Shouldn't happen but is a safe fallback
                    
                    # Process the shot
                    hit, ship_sunk = process_shot(x, y, None, player1_board, player2_shots)
                    
                    # Update the views
                    if hit:
                        player2_view[x][y] = CellState.HIT.value
                        player1_own_view[x][y] = CellState.HIT.value  # Update player's board to show hit
                    else:
                        player2_view[x][y] = CellState.MISS.value
                        player1_own_view[x][y] = CellState.MISS.value  # Update player's board to show miss
                    
                    # Update AI's knowledge of the shot
                    ai_opponent.process_shot_result(x, y, hit, ship_sunk)
                    
                    # Draw the updated boards to show the AI's shot
                    screen.fill(BLACK)
                    draw_board(screen, font, player2_view, 150, 80, 30, x, y, True, "AI's Shot")
                    draw_board(screen, font, player1_own_view, 400, 80, 25, -1, -1, False, "Your Board")
                    
                    # Draw status
                    hit_text = "HIT!" if hit else "MISS"
                    ship_text = " Ship sunk!" if ship_sunk else ""
                    status_text = small_font.render(f"AI fired at {chr(65 + y)}{x + 1}: {hit_text}{ship_text}", True, 
                                                (255, 0, 0) if hit else (255, 255, 255))
                    screen.blit(status_text, (WIDTH // 2 - 120, HEIGHT - 40))
                    
                    # Update display to show shot
                    pygame.display.flip()
                    
                    # Delay to show the AI's move result
                    pygame.time.delay(2000)
                    
                    # Check if game over
                    new_winner = check_game_over()
                    if new_winner:
                        winner = new_winner
                    else:
                        # Switch back to player's turn
                        current_player = 1
                except Exception as e:
             
                    # Show error message and continue
                    error_text = small_font.render("AI error - returning to your turn", True, (255, 0, 0))
                    screen.blit(error_text, (WIDTH // 2 - 120, HEIGHT - 70))
                    pygame.display.flip()
                    pygame.time.delay(2000)
                    current_player = 1
            
            # Update display
            pygame.display.flip()
            clock.tick(30)
            
        return winner
        
    except Exception as e:
        logger.error(f"Error in game_screen: {e}")
        logger.error(traceback.format_exc())
        return None

def draw_board(screen, font, board, offset_x, offset_y, cell_size, cursor_x, cursor_y, show_cursor, title=None):
    """Helper function to draw a game board"""
    # Draw title if provided
    if title:
        title_text = font.render(title, True, WHITE)
        title_rect = title_text.get_rect(center=(offset_x + (10 * cell_size) // 2, offset_y - 30))
        screen.blit(title_text, title_rect)
    
    # Draw column labels (A-J)
    for i in range(10):
        letter = chr(65 + i)
        text = pygame.font.Font(None, 20).render(letter, True, WHITE)
        screen.blit(text, (offset_x + i * cell_size + cell_size // 3, offset_y - 20))
    
    # Draw row labels (1-10)
    for i in range(10):
        number = str(i + 1)
        text = pygame.font.Font(None, 20).render(number, True, WHITE)
        screen.blit(text, (offset_x - 20, offset_y + i * cell_size + cell_size // 3))
    
    # Draw grid cells
    for y in range(10):
        for x in range(10):
            cell_rect = pygame.Rect(
                offset_x + x * cell_size,
                offset_y + y * cell_size,
                cell_size - 2,
                cell_size - 2
            )
            
            # Access board using [row][col]
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
            pygame.draw.rect(screen, color, cell_rect)
            pygame.draw.rect(screen, (100, 100, 100), cell_rect, 1)
    
    # Draw cursor if needed
    if show_cursor and cursor_x >= 0 and cursor_y >= 0:
        cursor_rect = pygame.Rect(
            offset_x + cursor_x * cell_size - 2,
            offset_y + cursor_y * cell_size - 2,
            cell_size + 2,
            cell_size + 2
        )
        pygame.draw.rect(screen, (255, 255, 0), cursor_rect, 2)

def game_mode_select():
    """Screen to select game mode (AI or Player) and AI difficulty"""
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 28)
    
    # Menu options
    options = ["VS AI", "VS Player"]
    ai_difficulties = ["Easy", "Medium", "Hard", "Pao"]  # Added Pao mode
    
    # Selection state
    current_option = 0  # 0 for VS AI, 1 for VS Player
    current_difficulty = 0  # 0 for Easy, 1 for Medium, 2 for Hard, 3 for Pao
    show_difficulty = False  # Only show difficulty options if AI is selected
    
    running = True
    while running:
        # Fill background
        screen.fill(BLACK)
        
        # Draw title
        title_text = font.render("Select Game Mode", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 100))
        screen.blit(title_text, title_rect)
        
        # Draw options
        for i, option in enumerate(options):
            color = LIGHT_BLUE if i == current_option else WHITE
            option_text = font.render(option, True, color)
            option_rect = option_text.get_rect(center=(WIDTH // 2, 200 + i * 60))
            screen.blit(option_text, option_rect)
            
            # Draw highlight box around selected option
            if i == current_option:
                rect = pygame.Rect(option_rect.left - 10, option_rect.top - 5, 
                                  option_rect.width + 20, option_rect.height + 10)
                pygame.draw.rect(screen, color, rect, 2, border_radius=5)
        
        # Draw difficulty options if VS AI is selected
        if current_option == 0:
            difficulty_title = small_font.render("Select Difficulty:", True, WHITE)
            screen.blit(difficulty_title, (WIDTH // 2 - 100, 320))
            
            for i, difficulty in enumerate(ai_difficulties):
                # Special color for Pao mode
                if difficulty == "Pao":
                    color = (255, 0, 0) if i == current_difficulty else (255, 100, 100)
                else:
                    color = LIGHT_BLUE if i == current_difficulty else WHITE
                
                diff_text = small_font.render(difficulty, True, color)
                diff_rect = diff_text.get_rect(center=(WIDTH // 2, 360 + i * 40))
                screen.blit(diff_text, diff_rect)
                
                # Draw highlight box around selected difficulty
                if i == current_difficulty:
                    rect = pygame.Rect(diff_rect.left - 10, diff_rect.top - 5, 
                                      diff_rect.width + 20, diff_rect.height + 10)
                    pygame.draw.rect(screen, color, rect, 2, border_radius=5)
            
            # Add warning for Pao mode
            if current_difficulty == 3:
                warning_text = small_font.render("WARNING: Impossible difficulty!", True, (255, 0, 0))
                warning_rect = warning_text.get_rect(center=(WIDTH // 2, 520))
                screen.blit(warning_text, warning_rect)
        
        # Draw controls help
        help_text = small_font.render("Up/Down: Navigate | Fire: Select | Mode: Back", True, LIGHT_GRAY)
        screen.blit(help_text, (WIDTH // 2 - 190, HEIGHT - 40))
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_TAB:
                    # Return to main menu
                    running = False
                elif event.key == pygame.K_UP:
                    if current_option == 0 and current_difficulty > 0:
                        # Navigate difficulty options
                        current_difficulty -= 1
                    else:
                        # Navigate main options
                        current_option = (current_option - 1) % len(options)
                        current_difficulty = 0  # Reset difficulty selection
                elif event.key == pygame.K_DOWN:
                    if current_option == 0 and current_difficulty < len(ai_difficulties) - 1:
                        # Navigate difficulty options
                        current_difficulty += 1
                    else:
                        # Navigate main options
                        current_option = (current_option + 1) % len(options)
                        current_difficulty = 0  # Reset difficulty selection
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # Launch ship placement screen with selected options
                    ai_mode = (current_option == 0)
                    difficulty = ai_difficulties[current_difficulty] if ai_mode else None
                    
                    # Create and run the ship placement screen
                    placement_screen = ShipPlacementScreen(screen, gpio_handler, ai_mode, difficulty)
                    player1_board, player2_board = placement_screen.run()
                    
                    # Start the game with the configured boards
                    game_screen(ai_mode, difficulty, player1_board, player2_board)
                    running = False  # Exit mode selection after game ends
        
        # Check GPIO buttons
        button_states = gpio_handler.get_button_states()
        
        if button_states['up']:
            if current_option == 0 and current_difficulty > 0:
                # Navigate difficulty options
                current_difficulty -= 1
            else:
                # Navigate main options
                current_option = (current_option - 1) % len(options)
                current_difficulty = 0  # Reset difficulty selection
        
        if button_states['down']:
            if current_option == 0 and current_difficulty < len(ai_difficulties) - 1:
                # Navigate difficulty options
                current_difficulty += 1
            else:
                # Navigate main options
                current_option = (current_option + 1) % len(options)
                current_difficulty = 0  # Reset difficulty selection
        
        if button_states['fire']:
            # Launch ship placement screen with selected options
            ai_mode = (current_option == 0)
            difficulty = ai_difficulties[current_difficulty] if ai_mode else None
            
            # Create and run the ship placement screen
            placement_screen = ShipPlacementScreen(screen, gpio_handler, ai_mode, difficulty)
            player1_board, player2_board = placement_screen.run()
            
            # Start the game with the configured boards
            game_screen(ai_mode, difficulty, player1_board, player2_board)
            running = False  # Exit mode selection after game ends
        
        if button_states['mode']:
            running = False  # Return to main menu
        
        # Update display
        pygame.display.flip()
        clock.tick(30)

def main_menu():
    # Set up menu buttons
    button_width = 200
    button_height = 50
    center_x = (WIDTH - button_width) // 2
    start_y = 200
    spacing = 70

    buttons = [
        Button(center_x, start_y, button_width, button_height, "Start Game", game_mode_select),
        Button(center_x, start_y + spacing, button_width, button_height, "Settings", settings_screen),
        Button(center_x, start_y + spacing * 2, button_width, button_height, "Quit", quit_game)
    ]
    
    # Default selection
    current_selection = 0
    buttons[current_selection].selected = True

    clock = pygame.time.Clock()
    
    # Main menu loop
    running = True
    while running:
        # Fill background
        screen.fill(BLACK)
        
        # Draw title
        title_text = title_font.render("Pao'er Ship", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 100))
        screen.blit(title_text, title_rect)
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Mouse events
            elif event.type == pygame.MOUSEMOTION:
                for button in buttons:
                    button.check_hover(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    button.check_click(event.pos)
            
            # Keyboard navigation
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    # Clear selections
                    for button in buttons:
                        button.selected = False
                    # Move selection up
                    current_selection = (current_selection - 1) % len(buttons)
                    buttons[current_selection].selected = True
                
                elif event.key == pygame.K_DOWN:
                    # Clear selections
                    for button in buttons:
                        button.selected = False
                    # Move selection down
                    current_selection = (current_selection + 1) % len(buttons)
                    buttons[current_selection].selected = True
                
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # Activate selected button
                    buttons[current_selection].action()
                
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        # Check for GPIO button presses
        button_states = gpio_handler.get_button_states()
        
        if button_states['up']:
            # Clear selections
            for button in buttons:
                button.selected = False
            # Move selection up
            current_selection = (current_selection - 1) % len(buttons)
            buttons[current_selection].selected = True
        
        if button_states['down']:
            # Clear selections
            for button in buttons:
                button.selected = False
            # Move selection down
            current_selection = (current_selection + 1) % len(buttons)
            buttons[current_selection].selected = True
        
        if button_states['fire']:
            # Activate selected button
            buttons[current_selection].action()
        
        # Update and draw buttons
        for button in buttons:
            button.update()
            button.draw(screen)
        
        # Display controls help
        help_font = pygame.font.Font(None, 24)
        help_text = help_font.render("Up/Down: Navigate | Fire: Select | Mode: Back", True, LIGHT_GRAY)
        screen.blit(help_text, (WIDTH // 2 - 150, HEIGHT - 40))
        
        # Update display
        pygame.display.flip()
        
        # Limit framerate
        clock.tick(30)

# Initialize GPIO handler
gpio_handler = GPIOHandler()

def main():
    try:
        main_menu()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        gpio_handler.cleanup()
        pygame.quit()

if __name__ == "__main__":
    main()