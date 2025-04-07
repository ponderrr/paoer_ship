import pygame
import sys
import time
import numpy as np
import random
import os
from src.board.game_board import GameBoard, CellState
from ship_placement_screen import ShipPlacementScreen
from src.game.ai_opponent import AIOpponent, AIDifficulty
from src.utils.image_display import ImageDisplay
from turn_transition_screen import TurnTransitionScreen
from exit_confirmation import ExitConfirmation
from src.hardware.dual_display_handler import DualDisplayHandler

# Try to import GPIO support
try:
    import gpiod
    IS_RASPBERRY_PI = True
except ImportError:
    IS_RASPBERRY_PI = False

# Initialize Pygame
pygame.init()

def initialize_dual_screens():
    """Initialize both the main and portable screens"""
    # Initialize main display (HDMI)
    os.environ["SDL_VIDEODRIVER"] = "x11"
    os.environ["DISPLAY"] = ":0.0"  # Main display
    
    # Screen settings
    WIDTH, HEIGHT = 640, 480
    main_screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pao'er Ship")
    
    # Try to initialize portable display
    portable_screen = None
    try:
        # Save current display value
        current_display = os.environ.get("DISPLAY")
        
        # Attempt to connect to second display
        os.environ["DISPLAY"] = ":0.1"  # Second display
        
        # Create a second Pygame window on the portable monitor
        # Use a smaller resolution appropriate for the portable screen
        portable_screen = pygame.Surface((480, 320))  # Create a virtual surface as fallback
        
        try:
            # Try to create actual second window
            portable_screen = pygame.display.set_mode((480, 320))
            pygame.display.set_caption("Pao'er Ship - Player View")
            print("Successfully initialized portable monitor!")
        except Exception as e:
            print(f"Could not create second window: {e}")
            print("Using virtual surface for portable display")
        
        # Restore original display setting
        if current_display:
            os.environ["DISPLAY"] = current_display
    except Exception as e:
        print(f"Error setting up portable display: {e}")
        # Create a dummy surface as fallback
        portable_screen = pygame.Surface((480, 320))
        print("Using virtual surface for portable display")
    
    return main_screen, portable_screen, WIDTH, HEIGHT

# Initialize screens
screen, PORTABLE_SCREEN, WIDTH, HEIGHT = initialize_dual_screens()

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

# Create dual display handler
display_handler = DualDisplayHandler(screen, PORTABLE_SCREEN)

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

def handle_portable_display_transition(display_handler, current_player, player1_board, player2_board, player1_shots, player2_shots):
    """
    Handle the transition of the portable display when the ROTATE button is pressed
    
    Args:
        display_handler: The dual display handler
        current_player: Current player (1 or 2)
        player1_board: Player 1's game board
        player2_board: Player 2's game board
        player1_shots: Set of shots fired by player 1
        player2_shots: Set of shots fired by player 2
    """
    # Determine which player's ships to show based on whose turn it is
    if current_player == 1:
        # Show player 1's board (it's their turn)
        player_board = player1_board
        opponent_shots = player2_shots
        board_title = "Your Ships - Player 1"
        next_player = 2
    else:
        # Show player 2's board (it's their turn)
        player_board = player2_board
        opponent_shots = player1_shots
        board_title = "Your Ships - Player 2"
        next_player = 1
    
    # Calculate hits on player's ships
    hits = set()
    for x, y in opponent_shots:
        # Check if this shot hit any of the player's ships
        for ship in player_board.ships:
            ship_coords = []
            ship_x, ship_y = ship.position
            for i in range(ship.length):
                if ship.orientation == "horizontal":
                    ship_coords.append((ship_x, ship_y + i))
                else:
                    ship_coords.append((ship_x + i, ship_y))
            
            if (x, y) in ship_coords:
                hits.add((x, y))
                break
    
    # Show player's board with shots on portable display
    display_handler.draw_board_on_portable(
        player_board.get_display_state(),
        opponent_shots,
        hits,
        board_title
    )
    
    # Wait for ROTATE button to continue
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Check for ROTATE button press (or any key for debugging)
        keys = pygame.key.get_pressed()
        button_states = gpio_handler.get_button_states()
        
        if button_states['rotate'] or keys[pygame.K_r]:
            waiting = False
        
        # Small delay to prevent CPU hogging
        pygame.time.delay(100)
    
    # Clear portable display and show waiting screen for next player
    display_handler.clear_portable_screen()
    display_handler.draw_waiting_screen(next_player)

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

def get_ship_coordinates(ship):
    """Get all coordinates occupied by a ship"""
    x, y = ship.position
    coordinates = []
    
    for i in range(ship.length):
        if ship.orientation == "horizontal":
            coordinates.append((x, y + i))
        else:
            coordinates.append((x + i, y))
    
    return coordinates

def game_screen(ai_mode=True, difficulty="Medium", player1_board=None, player2_board=None):
    """
    Game screen where the actual gameplay happens after ship placement
    
    Args:
        ai_mode (bool): Whether playing against AI (True) or another player (False)
        difficulty (str): AI difficulty level if ai_mode is True
        player1_board: Game board for player 1
        player2_board: Game board for player 2 (or AI)
    """
    # Import necessary modules
    import numpy as np
    import random
    from turn_transition_screen import TurnTransitionScreen
    from exit_confirmation import ExitConfirmation
    from src.game.ai_opponent import AIOpponent, AIDifficulty
    from src.utils.image_display import ImageDisplay
    
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
    
    # Initialize dual display handler for this game session
    display_handler = DualDisplayHandler(screen, PORTABLE_SCREEN)
    
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
    
    # Firing handling functions
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
                
        return hit, ship_sunk
    
    def check_game_over():
        """Check if the game is over (all ships sunk)"""
        player1_lost = all(ship.is_sunk() for ship in player1_board.ships)
        player2_lost = all(ship.is_sunk() for ship in player2_board.ships)
        
        if player1_lost:
            return 2  # Player 2 (or AI) wins
        elif player2_lost:
            return 1  # Player 1 wins
        return None  # No winner yet
    
    # Show initial player screen
    if not ai_mode:
        transition_screen.show_player_ready_screen(current_player)
        if PORTABLE_SCREEN:
            display_handler.draw_waiting_screen(1)
    
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
                                    pao_missed = True
                                    winner = 2  # AI wins
                                    # Show miss before ending
                                    pygame.display.flip()
                                    time.sleep(1)
                                    # Display Pao image
                                    image_display.display_pao_image(5.0)
                                    continue
                            
                            # For Player vs Player mode, update the portable display
                            if not ai_mode and PORTABLE_SCREEN:
                                # Show shot result first
                                pygame.display.flip()
                                time.sleep(1)  # Brief delay to show shot result
                                
                                # Calculate hits for display
                                player1_hits = set()
                                for shot_x, shot_y in player1_shots:
                                    for ship in player2_board.ships:
                                        ship_coords = get_ship_coordinates(ship)
                                        if (shot_x, shot_y) in ship_coords:
                                            player1_hits.add((shot_x, shot_y))
                                
                                # Show result before transitioning
                                pygame.display.flip()
                                transition_screen.show_turn_result(current_player, cursor_x, cursor_y, hit, ship_sunk)
                                
                                # Show the opponent's board with hit on portable display
                                display_handler.draw_board_on_portable(
                                    player2_board.get_display_state(),
                                    player1_shots,
                                    player1_hits,
                                    "Opponent's Board"
                                )
                                
                                # Clear portable display after brief delay
                                time.sleep(2)
                                display_handler.clear_portable_screen()
                                
                                # Show waiting screen for next player
                                display_handler.draw_waiting_screen(2)
                                
                                # Show player transition on main screen
                                transition_screen.show_player_ready_screen(2)
                                
                                # Show player 2's ships on portable display
                                handle_portable_display_transition(
                                    display_handler,
                                    2,  # Next player is 2
                                    player1_board,
                                    player2_board,
                                    player1_shots,
                                    player2_shots
                                )
                            else:
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
                                        transition_screen.show_turn_result(current_player, cursor_x, cursor_y, hit, ship_sunk)
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
                                pao_missed = True
                                winner = 2  # AI wins
                                # Show miss before ending
                                pygame.display.flip()
                                time.sleep(1)
                                # Display Pao image
                                image_display.display_pao_image(5.0)
                                continue
                        
                        # For Player vs Player mode, update the portable display
                        if not ai_mode and PORTABLE_SCREEN:
                            # Show shot result first
                            pygame.display.flip()
                            time.sleep(1)  # Brief delay to show shot result
                            
                            # Calculate hits for display
                            player1_hits = set()
                            for shot_x, shot_y in player1_shots:
                                for ship in player2_board.ships:
                                    ship_coords = get_ship_coordinates(ship)
                                    if (shot_x, shot_y) in ship_coords:
                                        player1_hits.add((shot_x, shot_y))
                            
                            # Show transition screen with result
                            transition_screen.show_turn_result(current_player, cursor_x, cursor_y, hit, ship_sunk)
                            
                            # Show the opponent's board with hit on portable display
                            display_handler.draw_board_on_portable(
                                player2_board.get_display_state(),
                                player1_shots,
                                player1_hits,
                                "Opponent's Board"
                            )
                            
                            # Clear portable display after brief delay
                            time.sleep(2)
                            display_handler.clear_portable_screen()
                            
                            # Show waiting screen for next player
                            display_handler.draw_waiting_screen(2)
                            
                            # Show player transition on main screen
                            transition_screen.show_player_ready_screen(2)
                            
                            # Show player 2's ships on portable display
                            handle_portable_display_transition(
                                display_handler,
                                2,  # Next player is 2
                                player1_board,
                                player2_board,
                                player1_shots,
                                player2_shots
                            )
                        else:
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
                                    transition_screen.show_turn_result(current_player, cursor_x, cursor_y, hit, ship_sunk)
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
            # Add slight delay for AI "thinking"
            if ai_opponent.difficulty == AIDifficulty.EASY:
                thinking_time = random.uniform(0.5, 1.0)
            elif ai_opponent.difficulty == AIDifficulty.MEDIUM:
                thinking_time = random.uniform(1.0, 1.5)
            elif ai_opponent.difficulty == AIDifficulty.HARD:
                thinking_time = random.uniform(1.5, 2.0)
            else:  # PAO mode
                thinking_time = random.uniform(0.5, 1.0)  # Faster in Pao mode
            
            time.sleep(thinking_time)
            
            # Get AI's shot from the AI opponent
            x, y = ai_opponent.get_shot()
            
            # Process the shot
            hit, ship_sunk = process_shot(x, y, None, player1_board, player2_shots)
            
            # Update the view
            if hit:
                player2_view[x][y] = CellState.HIT.value
                player1_own_view[x][y] = CellState.HIT.value  # Mark hit on player's view of their board
            else:
                player2_view[x][y] = CellState.MISS.value
                player1_own_view[x][y] = CellState.MISS.value  # Mark miss on player's view of their board
            
            # Update AI's knowledge of the shot
            ai_opponent.process_shot_result(x, y, hit, ship_sunk)
            
            # Update the display to show the AI's shot
            # Temporarily show cursor at AI's shot position
            cursor_backup = (cursor_x, cursor_y)
            cursor_x, cursor_y = x, y
            
            # Redraw to show the AI's shot position and result
            screen.fill(BLACK)
            
            # Make the coordinate display human-readable (A-J for columns, 1-10 for rows)
            human_coords = f"{chr(65 + y)}{x + 1}"
            
            # Draw the main board (player's) showing where AI fired
            draw_board(screen, font, player1_own_view, 150, 80, 30, x, y, True, "Your Board")
            
            # Draw AI's board (showing player shots)
            draw_board(screen, font, player1_view, 400, 80, 25, -1, -1, False, "AI's Board")
            
            # Draw status text with human-readable coordinates
            if hit:
                status_text = small_font.render(f"AI fired at {human_coords}: HIT!", True, (255, 0, 0))
            else:
                status_text = small_font.render(f"AI fired at {human_coords}: MISS", True, WHITE)
            
            screen.blit(status_text, (WIDTH // 2 - 80, HEIGHT - 40))
            
            # Update display to show shot
            pygame.display.flip()
            
            # Delay to show the AI's move
            time.sleep(2)
            
            # Restore cursor
            cursor_x, cursor_y = cursor_backup[0], cursor_backup[1]
            
            # Check if game over
            new_winner = check_game_over()
            if new_winner:
                winner = new_winner
                if pao_mode and winner == 2:
                    # Show Pao image on AI victory
                    image_display.display_pao_image(5.0)
            else:
                # Switch back to player's turn
                current_player = 1