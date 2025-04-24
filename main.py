import pygame
import sys
import time
import numpy as np
import random
from src.board.game_board import GameBoard, CellState
from src.ui.ship_placement_screen import ShipPlacementScreen
from src.game.ai_opponent import AIOpponent, AIDifficulty
from src.utils.image_display import ImageDisplay
from src.sound.sound_manager import SoundManager

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

# Create a SoundManager instance
sound_manager = SoundManager()
sound_manager.start_background_music()
sound_manager.set_music_volume(0.3)  # 30% for music
sound_manager.set_volume(0.4)        # 40% for sound effects


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
        self.border_color = WHITE
        self.border_width = 2

    def update(self):
        self.current_color = self.hover_color if (self.selected or self.hovered) else self.base_color

    def draw(self, screen):
        # Draw the button background
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=5)
        
        # Draw the border - make it thicker and more visible when selected
        if self.selected:
            # Thicker border when selected for better visibility
            pygame.draw.rect(screen, (255, 255, 0), self.rect, 3, border_radius=5)  # Yellow border when selected
        else:
            # Regular white border
            pygame.draw.rect(screen, self.border_color, self.rect, 2, border_radius=5)
        
        # Draw the text
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
    """Settings screen with volume controls, shuffle and repeat options"""
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    
    # Get current volumes and states
    music_volume = sound_manager.get_music_volume()
    sfx_volume = sound_manager.get_sfx_volume()
    shuffle_state = sound_manager.get_shuffle_state()
    repeat_state = sound_manager.get_repeat_state()
    
    # Settings options
    settings_options = ["Music Volume", "SFX Volume", "Shuffle", "Repeat", "Back to Menu"]
    current_option = 0
    
    running = True
    while running:
        screen.fill(BLACK)
        
        # Draw title
        title_text = font.render("Settings", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 80))
        screen.blit(title_text, title_rect)
        
        # Draw options
        for i, option in enumerate(settings_options):
            color = LIGHT_BLUE if i == current_option else WHITE
            option_text = font.render(option, True, color)
            option_rect = option_text.get_rect(center=(WIDTH // 2, 180 + i * 60))
            screen.blit(option_text, option_rect)
            
            if i == current_option:
                rect = pygame.Rect(option_rect.left - 10, option_rect.top - 5,
                                 option_rect.width + 20, option_rect.height + 10)
                pygame.draw.rect(screen, color, rect, 2, border_radius=5)
        
        # Draw volume bars
        # Music volume bar
        music_bar_x = WIDTH // 2 - 100
        music_bar_y = 180 + 30
        music_bar_width = 200
        music_bar_height = 10
        
        # Background bar
        pygame.draw.rect(screen, LIGHT_GRAY, 
                        (music_bar_x, music_bar_y, music_bar_width, music_bar_height))
        # Filled bar
        pygame.draw.rect(screen, BLUE, 
                        (music_bar_x, music_bar_y, 
                         int(music_bar_width * music_volume), music_bar_height))
        # Border
        pygame.draw.rect(screen, WHITE, 
                        (music_bar_x, music_bar_y, music_bar_width, music_bar_height), 2)
        
        # Music volume text
        volume_text = small_font.render(f"{int(music_volume * 100)}%", True, WHITE)
        volume_rect = volume_text.get_rect(center=(WIDTH // 2 + 150, music_bar_y + music_bar_height // 2))
        screen.blit(volume_text, volume_rect)
        
        # SFX volume bar
        sfx_bar_x = WIDTH // 2 - 100
        sfx_bar_y = 240 + 30
        sfx_bar_width = 200
        sfx_bar_height = 10
        
        # Background bar
        pygame.draw.rect(screen, LIGHT_GRAY, 
                        (sfx_bar_x, sfx_bar_y, sfx_bar_width, sfx_bar_height))
        # Filled bar
        pygame.draw.rect(screen, BLUE, 
                        (sfx_bar_x, sfx_bar_y, 
                         int(sfx_bar_width * sfx_volume), sfx_bar_height))
        # Border
        pygame.draw.rect(screen, WHITE, 
                        (sfx_bar_x, sfx_bar_y, sfx_bar_width, sfx_bar_height), 2)
        
        # SFX volume text
        sfx_volume_text = small_font.render(f"{int(sfx_volume * 100)}%", True, WHITE)
        sfx_volume_rect = sfx_volume_text.get_rect(center=(WIDTH // 2 + 150, sfx_bar_y + sfx_bar_height // 2))
        screen.blit(sfx_volume_text, sfx_volume_rect)
        
        # Shuffle option
        shuffle_color = (0, 255, 0) if shuffle_state else (255, 0, 0)
        shuffle_text = small_font.render(f"{'ON' if shuffle_state else 'OFF'}", True, shuffle_color)
        shuffle_rect = shuffle_text.get_rect(center=(WIDTH // 2 + 150, 300 + 10))
        screen.blit(shuffle_text, shuffle_rect)
        
        # Repeat option
        repeat_color = (0, 255, 0) if repeat_state else (255, 0, 0)
        repeat_text = small_font.render(f"{'ON' if repeat_state else 'OFF'}", True, repeat_color)
        repeat_rect = repeat_text.get_rect(center=(WIDTH // 2 + 150, 360 + 10))
        screen.blit(repeat_text, repeat_rect)
        
        # Help text
        help_text = small_font.render("Up/Down: Navigate | Left/Right: Adjust | Fire: Toggle/Select | Mode: Back", 
                                    True, LIGHT_GRAY)
        help_rect = help_text.get_rect(center=(WIDTH // 2, HEIGHT - 40))
        screen.blit(help_text, help_rect)
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    current_option = (current_option - 1) % len(settings_options)
                    sound_manager.play_sound("navigate_up")
                elif event.key == pygame.K_DOWN:
                    current_option = (current_option + 1) % len(settings_options)
                    sound_manager.play_sound("navigate_down")
                elif event.key == pygame.K_LEFT:
                    if current_option == 0:  # Music volume
                        music_volume = max(0, music_volume - 0.05)
                        sound_manager.set_music_volume(music_volume)
                    elif current_option == 1:  # SFX volume
                        sfx_volume = max(0, sfx_volume - 0.05)
                        sound_manager.set_volume(sfx_volume)
                        sound_manager.play_sound("navigate_down")  # Test the volume
                elif event.key == pygame.K_RIGHT:
                    if current_option == 0:  # Music volume
                        music_volume = min(1.0, music_volume + 0.05)
                        sound_manager.set_music_volume(music_volume)
                    elif current_option == 1:  # SFX volume
                        sfx_volume = min(1.0, sfx_volume + 0.05)
                        sound_manager.set_volume(sfx_volume)
                        sound_manager.play_sound("navigate_up")  # Test the volume
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    if current_option == 2:  # Shuffle
                        shuffle_state = sound_manager.toggle_shuffle()
                        sound_manager.play_sound("accept")
                    elif current_option == 3:  # Repeat
                        repeat_state = sound_manager.toggle_repeat()
                        sound_manager.play_sound("accept")
                    elif current_option == 4:  # Back to menu
                        sound_manager.play_sound("back")
                        running = False
                elif event.key in [pygame.K_ESCAPE, pygame.K_TAB]:
                    sound_manager.play_sound("back")
                    running = False
        
        # GPIO button handling
        button_states = gpio_handler.get_button_states()
        
        if button_states['up']:
            current_option = (current_option - 1) % len(settings_options)
            sound_manager.play_sound("navigate_up")
            
        if button_states['down']:
            current_option = (current_option + 1) % len(settings_options)
            sound_manager.play_sound("navigate_down")
            
        if button_states['left']:
            if current_option == 0:  # Music volume
                music_volume = max(0, music_volume - 0.05)
                sound_manager.set_music_volume(music_volume)
            elif current_option == 1:  # SFX volume
                sfx_volume = max(0, sfx_volume - 0.05)
                sound_manager.set_volume(sfx_volume)
                sound_manager.play_sound("navigate_down")  # Test the volume
                
        if button_states['right']:
            if current_option == 0:  # Music volume
                music_volume = min(1.0, music_volume + 0.05)
                sound_manager.set_music_volume(music_volume)
            elif current_option == 1:  # SFX volume
                sfx_volume = min(1.0, sfx_volume + 0.05)
                sound_manager.set_volume(sfx_volume)
                sound_manager.play_sound("navigate_up")  # Test the volume
                
        if button_states['fire']:
            if current_option == 2:  # Shuffle
                shuffle_state = sound_manager.toggle_shuffle()
                sound_manager.play_sound("accept")
            elif current_option == 3:  # Repeat
                repeat_state = sound_manager.toggle_repeat()
                sound_manager.play_sound("accept")
            elif current_option == 4:  # Back to menu
                sound_manager.play_sound("back")
                running = False
                
        if button_states['mode']:
            sound_manager.play_sound("back")
            running = False
        
        pygame.display.flip()
        clock.tick(30)

def process_shot(x, y, shooter_board, target_board, shots_set):
    """Process a shot from one player to another's board"""
    # Swap coordinates for internal board representation
    # x = column (A-J), y = row (1-10)
    # But internally board is accessed as [row][col]
    board_x, board_y = y, x

    if (board_x, board_y) in shots_set:
        return False, False  # Shot already taken, no ship sunk

    shots_set.add((board_x, board_y))

    # Check if hit and if ship was sunk
    hit = False
    ship_sunk = False

    for ship in target_board.ships:
        if ship.receive_hit(board_x, board_y):
            hit = True
            ship_sunk = ship.is_sunk()
            break

    # Update the board state at the target location
    if hit:
        target_board.board[board_x, board_y] = CellState.HIT.value
        sound_manager.play_sound("hit")
        if ship_sunk:
            sound_manager.play_sound("ship_sunk")
    else:
        target_board.board[board_x, board_y] = CellState.MISS.value
        sound_manager.play_sound("miss")

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
        print(f"Starting game with AI mode: {ai_mode}, difficulty: {difficulty}")

        import numpy as np
        import random
        from src.ui.turn_transition_screen import TurnTransitionScreen
        from src.ui.exit_confirmation import ExitConfirmation
        from src.game.ai_opponent import AIOpponent, AIDifficulty
        from src.utils.image_display import ImageDisplay

        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)

        if player1_board is None:
            player1_board = GameBoard()
        if player2_board is None:
            player2_board = GameBoard()

        transition_screen = TurnTransitionScreen(screen, gpio_handler)
        exit_dialog = ExitConfirmation(screen, gpio_handler)
        image_display = ImageDisplay(screen)

        def check_game_over():
            """Check if the game is over (all ships sunk)"""
            player1_lost = all(ship.is_sunk() for ship in player1_board.ships)
            player2_lost = all(ship.is_sunk() for ship in player2_board.ships)

            if player1_lost:
                return 2  # Player 2 (or AI) wins
            elif player2_lost:
                return 1  # Player 1 wins
            return None

        ai_opponent = None
        if ai_mode:
            difficulty_map = {
                "Easy": AIDifficulty.EASY,
                "Medium": AIDifficulty.MEDIUM,
                "Hard": AIDifficulty.HARD,
                "Pao": AIDifficulty.PAO
            }

            ai_difficulty = difficulty_map.get(difficulty, AIDifficulty.MEDIUM)
            ai_opponent = AIOpponent(ai_difficulty, player1_board)
            player2_board = ai_opponent.board

        game_mode_text = "VS AI" if ai_mode else "VS Player"
        if ai_mode and difficulty:
            game_mode_text += f" ({difficulty})"
        pao_mode = ai_mode and difficulty == "Pao"
        if pao_mode:
            sound_manager.start_pao_mode()

        current_player = 1
        cursor_x, cursor_y = 0, 0
        player1_shots = set()
        player2_shots = set()
        winner = None
        move_delay = 0

        player1_view = np.zeros((10, 10), dtype=int)
        player2_view = np.zeros((10, 10), dtype=int)

        player1_own_view = player1_board.get_display_state()
        player2_own_view = player2_board.get_display_state()

        if not ai_mode:
            transition_screen.show_player_ready_screen(current_player)
        else:
            transition_screen.show_player_ready_screen(
                current_player,
                True,
                player1_own_view
            )

        showing_exit_dialog = False
        pao_missed = False
        turn_in_progress = False

        running = True
        while running:
            current_time = pygame.time.get_ticks()
            screen.fill(BLACK)

            mode_text = font.render(game_mode_text, True, WHITE)
            screen.blit(mode_text, (WIDTH - 200, 20))

            exit_text = small_font.render("Press MODE to exit", True, LIGHT_GRAY)
            screen.blit(exit_text, (20, HEIGHT - 30))

            if showing_exit_dialog:
                if exit_dialog.show():
                    running = False
                    break
                showing_exit_dialog = False
                continue

            if current_player == 1:
                active_board = player2_board
                view_board = player1_view
                shots = player1_shots
                own_board = player1_own_view
            else:
                active_board = player1_board
                view_board = player2_view
                shots = player2_shots
                own_board = player2_own_view

            # Center the opponent's board since we're not showing two boards
            draw_board(
                screen,
                font,
                view_board,
                (WIDTH - 300) // 2,  # Center the board
                80,
                30,
                cursor_x if (current_player == 1 or (current_player == 2 and not ai_mode)) else -1,
                cursor_y if (current_player == 1 or (current_player == 2 and not ai_mode)) else -1,
                (current_player == 1 or (current_player == 2 and not ai_mode)),
                "Opponent's Board"
            )

            # REMOVED: The "Your Board" display that was here

            if not winner:
                if current_player == 1:
                    player_text = font.render("Player 1's Turn", True, WHITE)
                elif not ai_mode:
                    player_text = font.render("Player 2's Turn", True, WHITE)
                else:
                    player_text = font.render("AI's Turn", True, WHITE)
                screen.blit(player_text, (20, 20))

            if winner:
                
                if winner == 1:
                    winner_text = font.render("Player 1 Wins!", True, (255, 215, 0))
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
                    if ai_mode:
                        status_text = small_font.render("AI is thinking...", True, WHITE)
                    else:
                        status_text = small_font.render("Player 2: Press FIRE to shoot", True, WHITE)
                    screen.blit(status_text, (WIDTH // 2 - 100, HEIGHT - 40))


            if not turn_in_progress:
                for event in pygame.event.get():
                       # Handle music end event
                    sound_manager.handle_music_end_event(event)

                    if event.type == pygame.QUIT:
                        running = False
                        pygame.quit()
                        sys.exit()

                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE or event.key == pygame.K_TAB:
                            showing_exit_dialog = True

                        if not winner and (current_player == 1 or (current_player == 2 and not ai_mode)):
                            if event.key == pygame.K_UP and cursor_y > 0:
                                cursor_y -= 1
                            elif event.key == pygame.K_DOWN and cursor_y < 9:
                                cursor_y += 1
                            elif event.key == pygame.K_LEFT and cursor_x > 0:
                                cursor_x -= 1
                            elif event.key == pygame.K_RIGHT and cursor_x < 9:
                                cursor_x += 1
                            elif event.key == pygame.K_SPACE:
                                turn_in_progress = True

                                # PLAY FIRE SOUND HERE
                                sound_manager.play_sound("fire")

                                if current_player == 1 and (board_x := y, board_y := x) not in player1_shots:
                                    board_x, board_y = cursor_y, cursor_x

                                    if (board_x, board_y) not in player1_shots:
                                        hit, ship_sunk = process_shot(cursor_x, cursor_y, None, player2_board, player1_shots)

                                        if hit:
                                            player1_view[cursor_y][cursor_x] = CellState.HIT.value
                                        else:
                                            player1_view[cursor_y][cursor_x] = CellState.MISS.value

                                            if pao_mode:
                                                sound_manager.start_pao_mode()
                                                screen.fill(BLACK)
                                                draw_board(screen, font, player1_view, 150, 80, 30, cursor_x, cursor_y, True, "Your Shot")
                                                draw_board(screen, font, player1_own_view, 400, 80, 25, -1, -1, False, "Your Board")

                                                miss_text = small_font.render(f"You fired at {chr(65 + cursor_x)}{cursor_y + 1}: MISS!", True, (0, 0, 255))
                                                screen.blit(miss_text, (WIDTH // 2 - 100, HEIGHT - 70))

                                                pao_warning = font.render("PAO MODE ACTIVATED - YOU LOSE!", True, (255, 0, 0))
                                                screen.blit(pao_warning, (WIDTH // 2 - 200, HEIGHT - 40))

                                                pygame.display.flip()
                                                pygame.time.delay(3000)

                                                pao_missed = True
                                                winner = 2
                                                image_display.display_pao_image()
                                                turn_in_progress = False
                                                continue

                                        pygame.display.flip()

                                        new_winner = check_game_over()
                                        if new_winner:
                                            winner = new_winner
                                            pygame.display.flip()
                                            time.sleep(1)
                                            turn_in_progress = False
                                        else:
                                            if not ai_mode:
                                                transition_screen.show_turn_result(current_player, cursor_y, cursor_x, hit, ship_sunk)
                                                transition_screen.show_player_ready_screen(2)
                                            else:
                                                transition_screen.show_turn_result(
                                                    current_player,
                                                    cursor_y,
                                                    cursor_x,
                                                    hit,
                                                    ship_sunk,
                                                    True,
                                                    player1_own_view
                                                )
                                                transition_screen.show_player_ready_screen(
                                                    2,
                                                    True,
                                                    player1_own_view
                                                )
                                            current_player = 2
                                            turn_in_progress = False

                                elif current_player == 2 and not ai_mode:
                                    board_x, board_y = cursor_y, cursor_x
                                    if (board_x, board_y) not in player2_shots:
                                        hit, ship_sunk = process_shot(cursor_x, cursor_y, None, player1_board, player2_shots)

                                        if hit:
                                            player2_view[cursor_y][cursor_x] = CellState.HIT.value
                                        else:
                                            player2_view[cursor_y][cursor_x] = CellState.MISS.value

                                        pygame.display.flip()

                                        new_winner = check_game_over()
                                        if new_winner:
                                            winner = new_winner
                                            pygame.display.flip()
                                            time.sleep(1)
                                            turn_in_progress = False
                                        else:
                                            transition_screen.show_turn_result(current_player, cursor_y, cursor_x, hit, ship_sunk)
                                            transition_screen.show_player_ready_screen(1)
                                            current_player = 1
                                            turn_in_progress = False
                                    else:
                                        turn_in_progress = False
                                else:
                                    turn_in_progress = False

                button_states = gpio_handler.get_button_states()

                if button_states['mode']:
                    showing_exit_dialog = True

                if not winner and (current_player == 1 or (current_player == 2 and not ai_mode)):
                    if button_states['up'] and cursor_y > 0:
                        cursor_y -= 1
                    if button_states['down'] and cursor_y < 9:
                        cursor_y += 1
                    if button_states['left'] and cursor_x > 0:
                        cursor_x -= 1
                    if button_states['right'] and cursor_x < 9:
                        cursor_x += 1

                    if button_states['fire']:
                        turn_in_progress = True

                        # PLAY FIRE SOUND HERE
                        sound_manager.play_sound("fire")

                        if current_player == 1:
                            board_x, board_y = cursor_y, cursor_x
                            if (board_x, board_y) not in player1_shots:
                                hit, ship_sunk = process_shot(cursor_x, cursor_y, None, player2_board, player1_shots)

                                if hit:
                                    player1_view[cursor_y][cursor_x] = CellState.HIT.value
                                else:
                                    player1_view[cursor_y][cursor_x] = CellState.MISS.value

                                    if pao_mode:
                                        transition_screen.show_turn_result(
                                            current_player,
                                            cursor_y,
                                            cursor_x,
                                            False,
                                            False,
                                            True,
                                            player1_own_view
                                        )
                                        screen.fill(BLACK)
                                        pao_warning = font.render("PAO MODE ACTIVATED - YOU LOSE!", True, (255, 0, 0))
                                        warning_rect = pao_warning.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                                        screen.blit(pao_warning, warning_rect)
                                        pygame.display.flip()
                                        pygame.time.delay(3000)
                                        pao_missed = True
                                        winner = 2
                                        image_display.display_pao_image()
                                        turn_in_progress = False
                                        continue

                                pygame.display.flip()

                                new_winner = check_game_over()
                                if new_winner:
                                    winner = new_winner
                                    pygame.display.flip()
                                    time.sleep(1)
                                    turn_in_progress = False
                                else:
                                    if not ai_mode:
                                        transition_screen.show_turn_result(current_player, cursor_y, cursor_x, hit, ship_sunk)
                                        transition_screen.show_player_ready_screen(2)
                                    else:
                                        transition_screen.show_turn_result(
                                            current_player,
                                            cursor_y,
                                            cursor_x,
                                            hit,
                                            ship_sunk,
                                            True,
                                            player1_own_view
                                        )
                                        transition_screen.show_player_ready_screen(
                                            2,
                                            True,
                                            player1_own_view
                                        )
                                    current_player = 2
                                    turn_in_progress = False
                            else:
                                turn_in_progress = False

                        elif current_player == 2 and not ai_mode:
                            board_x, board_y = cursor_y, cursor_x
                            if (board_x, board_y) not in player2_shots:
                                hit, ship_sunk = process_shot(cursor_x, cursor_y, None, player1_board, player2_shots)

                                if hit:
                                    player2_view[cursor_y][cursor_x] = CellState.HIT.value
                                else:
                                    player2_view[cursor_y][cursor_x] = CellState.MISS.value

                                pygame.display.flip()

                                new_winner = check_game_over()
                                if new_winner:
                                    winner = new_winner
                                    pygame.display.flip()
                                    time.sleep(1)
                                    turn_in_progress = False
                                else:
                                    transition_screen.show_turn_result(current_player, cursor_y, cursor_x, hit, ship_sunk)
                                    transition_screen.show_player_ready_screen(1)
                                    current_player = 1
                                    turn_in_progress = False
                            else:
                                turn_in_progress = False
                        else:
                            turn_in_progress = False
                elif winner:
                    if any(button_states.values()):
                        running = False

            if ai_mode and current_player == 2 and not winner:
                if difficulty == "Easy":
                    thinking_time = random.uniform(0.5, 1.0)
                elif difficulty == "Medium":
                    thinking_time = random.uniform(1.0, 1.5)
                else:
                    thinking_time = random.uniform(1.5, 2.0)

                screen.fill(BLACK)
                draw_board(screen, font, player2_view, 150, 80, 30, -1, -1, False, "AI's Shot")
                draw_board(screen, font, player1_own_view, 400, 80, 25, -1, -1, False, "Your Board")
                thinking_text = small_font.render("AI is thinking...", True, WHITE)
                thinking_rect = thinking_text.get_rect(center=(WIDTH // 2, HEIGHT - 40))
                screen.blit(thinking_text, thinking_rect)
                pygame.display.flip()

                pygame.time.delay(int(thinking_time * 1000))

                try:
                    board_x, board_y = ai_opponent.get_shot()
                    display_x, display_y = board_y, board_x
                    print(f"AI shot - board coords: ({board_x}, {board_y}), display coords: ({display_x}, {display_y})")

                    if not (0 <= board_x < 10 and 0 <= board_y < 10):
                        print(f"AI returned invalid shot: ({board_x}, {board_y})")
                        valid_shots = [(i, j) for i in range(10) for j in range(10) if (i, j) not in player2_shots]
                        if valid_shots:
                            board_x, board_y = random.choice(valid_shots)
                            display_x, display_y = board_y, board_x
                            board_x, board_y = 0, 0
                            display_x, display_y = board_y, board_x
                            print("Using fallback coords: (0,0)")

                    hit, ship_sunk = False, False
                    if (board_x, board_y) not in player2_shots:
                        player2_shots.add((board_x, board_y))

                        # Play fire sound for AI
                        sound_manager.play_sound("fire")

                        for ship in player1_board.ships:
                            if ship.receive_hit(board_x, board_y):
                                hit = True
                                ship_sunk = ship.is_sunk()
                                break

                        if hit:
                            player1_board.board[board_x, board_y] = CellState.HIT.value
                            player2_view[board_x][board_y] = CellState.HIT.value
                            player1_own_view[board_x][board_y] = CellState.HIT.value
                            # Play hit sound
                            sound_manager.play_sound("hit")
                            # Play ship sunk sound if needed
                            if ship_sunk:
                                sound_manager.play_sound("ship_sunk")
                        else:
                            player1_board.board[board_x, board_y] = CellState.MISS.value
                            player2_view[board_x][board_y] = CellState.MISS.value
                            player1_own_view[board_x][board_y] = CellState.MISS.value
                            # Play miss sound
                            sound_manager.play_sound("miss")

                        ai_opponent.process_shot_result(board_x, board_y, hit, ship_sunk)

                    screen.fill(BLACK)
                    draw_board(screen, font, player2_view, 150, 80, 30, display_x, display_y, True, "AI's Shot")
                    draw_board(screen, font, player1_own_view, 400, 80, 25, -1, -1, False, "Your Board")

                    hit_text = "HIT!" if hit else "MISS"
                    ship_text = " Ship sunk!" if ship_sunk else ""
                    status_text = small_font.render(
                        f"AI fired at {chr(65 + display_x)}{display_y + 1}: {hit_text}{ship_text}",
                        True,
                        (255, 0, 0) if hit else (255, 255, 255)
                    )
                    screen.blit(status_text, (WIDTH // 2 - 120, HEIGHT - 40))
                    pygame.display.flip()
                    pygame.time.delay(2000)

                    new_winner = check_game_over()
                    if new_winner:
                        winner = new_winner
                    else:
                        transition_screen.show_turn_result(
                            2,
                            display_y,
                            display_x,
                            hit,
                            ship_sunk,
                            True,
                            player1_own_view
                        )
                        transition_screen.show_player_ready_screen(
                            1,
                            True,
                            player1_own_view
                        )

                    current_player = 1

                except Exception as e:
                    print(f"AI error: {e}")
                    import traceback
                    traceback.print_exc()
                    error_text = small_font.render(f"AI error: {str(e)[:30]}...", True, (255, 0, 0))
                    screen.blit(error_text, (WIDTH // 2 - 120, HEIGHT - 70))
                    pygame.display.flip()
                    pygame.time.delay(2000)

            pygame.display.flip()
            clock.tick(30)

        return winner

    except Exception as e:
        print(f"Error in game_screen: {e}")
        import traceback
        traceback.print_exc()
        return None

def draw_board(screen, font, board, offset_x, offset_y, cell_size, cursor_x, cursor_y, show_cursor, title=None):
    """Helper function to draw a game board"""
    
    # Calculate board dimensions for centering
    board_width = 10 * cell_size
    board_height = 10 * cell_size
    
    # Adjust offset if we want to center the board
    if title:
        title_text = font.render(title, True, WHITE)
        title_rect = title_text.get_rect(center=(offset_x + board_width // 2, offset_y - 30))
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

    # Draw the board cells
    for y in range(10):
        for x in range(10):
            cell_rect = pygame.Rect(
                offset_x + x * cell_size,
                offset_y + y * cell_size,
                cell_size - 2,
                cell_size - 2
            )
            cell_value = board[y][x]
            if cell_value == CellState.EMPTY.value:
                color = (50, 50, 50)
            elif cell_value == CellState.SHIP.value:
                color = (0, 255, 0)
            elif cell_value == CellState.HIT.value:
                color = (255, 0, 0)
            else:
                color = (0, 0, 255)

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

    options = ["VS AI", "VS Player"]
    ai_difficulties = ["Easy", "Medium", "Hard", "Pao"]
    current_option = 0
    current_difficulty = 0
    show_difficulty = False

    running = True
    while running:
        screen.fill(BLACK)
        title_text = font.render("Select Game Mode", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 80))
        screen.blit(title_text, title_rect)

        for i, option in enumerate(options):
            color = LIGHT_BLUE if i == current_option else WHITE
            option_text = font.render(option, True, color)
            option_rect = option_text.get_rect(center=(WIDTH // 2, 180 + i * 60))
            screen.blit(option_text, option_rect)

            if i == current_option:
                rect = pygame.Rect(option_rect.left - 10, option_rect.top - 5,
                                   option_rect.width + 20, option_rect.height + 10)
                pygame.draw.rect(screen, color, rect, 2, border_radius=5)

        if current_option == 0:
            difficulty_title = small_font.render("Select Difficulty:", True, WHITE)
            screen.blit(difficulty_title, (WIDTH // 2 - 100, 320))

            for i, diff in enumerate(ai_difficulties):
                if diff == "Pao":
                    color = (255, 0, 0) if i == current_difficulty else (255, 100, 100)
                else:
                    color = LIGHT_BLUE if i == current_difficulty else WHITE

                diff_text = small_font.render(diff, True, color)
                diff_rect = diff_text.get_rect(center=(WIDTH // 2, 360 + i * 40))
                screen.blit(diff_text, diff_rect)

                if i == current_difficulty:
                    rect = pygame.Rect(diff_rect.left - 10, diff_rect.top - 5,
                                       diff_rect.width + 20, diff_rect.height + 10)
                    pygame.draw.rect(screen, color, rect, 2, border_radius=5)

            if current_difficulty == 3:
                warning_text = small_font.render("WARNING: Impossible difficulty!", True, (255, 0, 0))
                warning_rect = warning_text.get_rect(center=(WIDTH // 2, 520))
                screen.blit(warning_text, warning_rect)

        help_text = small_font.render("Up/Down: Navigate | Fire: Select | Mode: Back", True, LIGHT_GRAY)
        screen.blit(help_text, (WIDTH // 2 - 190, HEIGHT - 40))

        for event in pygame.event.get():
               # Handle music end event
            sound_manager.handle_music_end_event(event)
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, pygame.K_TAB]:
                    sound_manager.play_sound("back")  # Play back sound
                    running = False
                elif event.key == pygame.K_UP:
                    if current_option == 0 and current_difficulty > 0:
                        current_difficulty -= 1
                        sound_manager.play_sound("navigate_up")  # Play up sound
                    else:
                        old_option = current_option
                        current_option = (current_option - 1) % len(options)
                        current_difficulty = 0
                        if old_option != current_option:
                            sound_manager.play_sound("navigate_up")  # Play up sound
                elif event.key == pygame.K_DOWN:
                    if current_option == 0 and current_difficulty < len(ai_difficulties) - 1:
                        current_difficulty += 1
                        sound_manager.play_sound("navigate_down")  # Play down sound
                    else:
                        old_option = current_option
                        current_option = (current_option + 1) % len(options)
                        current_difficulty = 0
                        if old_option != current_option:
                            sound_manager.play_sound("navigate_down")  # Play down sound
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    sound_manager.play_sound("accept")  # Play accept sound
                    ai_mode = (current_option == 0)
                    difficulty = ai_difficulties[current_difficulty] if ai_mode else None

                    placement_screen = ShipPlacementScreen(screen, gpio_handler, ai_mode, difficulty)
                    player1_board, player2_board = placement_screen.run()
                    game_screen(ai_mode, difficulty, player1_board, player2_board)
                    running = False

        button_states = gpio_handler.get_button_states()

        if button_states['up']:
            if current_option == 0 and current_difficulty > 0:
                current_difficulty -= 1
                sound_manager.play_sound("navigate_up")  # Play up sound
            else:
                old_option = current_option
                current_option = (current_option - 1) % len(options)
                current_difficulty = 0
                if old_option != current_option:
                    sound_manager.play_sound("navigate_up")  # Play up sound

        if button_states['down']:
            if current_option == 0 and current_difficulty < len(ai_difficulties) - 1:
                current_difficulty += 1
                sound_manager.play_sound("navigate_down")  # Play down sound
            else:
                old_option = current_option
                current_option = (current_option + 1) % len(options)
                current_difficulty = 0
                if old_option != current_option:
                    sound_manager.play_sound("navigate_down")  # Play down sound

        if button_states['fire']:
            sound_manager.play_sound("accept")  # Play accept sound
            ai_mode = (current_option == 0)
            difficulty = ai_difficulties[current_difficulty] if ai_mode else None
            placement_screen = ShipPlacementScreen(screen, gpio_handler, ai_mode, difficulty)
            player1_board, player2_board = placement_screen.run()
            game_screen(ai_mode, difficulty, player1_board, player2_board)
            running = False

        if button_states['mode']:
            sound_manager.play_sound("back")  # Play back sound
            running = False

        pygame.display.flip()
        clock.tick(30)

def main_menu():
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

    current_selection = 0
    buttons[current_selection].selected = True
    clock = pygame.time.Clock()
    running = True

    # Use the existing global sound_manager instance
    global sound_manager

    while running:
        screen.fill(BLACK)
        title_text = title_font.render("Pao'er Ship", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 100))
        screen.blit(title_text, title_rect)

        for event in pygame.event.get():
            # Handle music end event
            sound_manager.handle_music_end_event(event)
            
            if event.type == pygame.QUIT:
                # Only quit the program if we're actually supposed to
                running = False
                quit_game()
                return  # Exit function after quitting
            elif event.type == pygame.MOUSEMOTION:
                for button in buttons:
                    button.check_hover(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button.rect.collidepoint(event.pos):
                        sound_manager.play_sound("accept")
                        button.check_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    for button in buttons:
                        button.selected = False
                    current_selection = (current_selection - 1) % len(buttons)
                    buttons[current_selection].selected = True
                    sound_manager.play_sound("navigate_up")
                elif event.key == pygame.K_DOWN:
                    for button in buttons:
                        button.selected = False
                    current_selection = (current_selection + 1) % len(buttons)
                    buttons[current_selection].selected = True
                    sound_manager.play_sound("navigate_down")
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    sound_manager.play_sound("accept")
                    buttons[current_selection].action()
                elif event.key == pygame.K_ESCAPE:
                    sound_manager.play_sound("back")
                    # Since we're already at the main menu, pressing escape should quit
                    running = False
                    quit_game()
                    return

        # Only check GPIO if we have a valid handler
        if gpio_handler:
            button_states = gpio_handler.get_button_states()
            if button_states['up']:
                for button in buttons:
                    button.selected = False
                current_selection = (current_selection - 1) % len(buttons)
                buttons[current_selection].selected = True
                sound_manager.play_sound("navigate_up")

            if button_states['down']:
                for button in buttons:
                    button.selected = False
                current_selection = (current_selection + 1) % len(buttons)
                buttons[current_selection].selected = True
                sound_manager.play_sound("navigate_down")

            if button_states['fire']:
                sound_manager.play_sound("accept")
                buttons[current_selection].action()
                
            if button_states['mode']:
                sound_manager.play_sound("back")
                # Since we're already at the main menu, pressing MODE should quit
                running = False
                quit_game()
                return

        for button in buttons:
            button.update()
            button.draw(screen)

        help_font = pygame.font.Font(None, 24)
        help_text = help_font.render("Up/Down: Navigate | Fire: Select | Mode: Quit", True, LIGHT_GRAY)
        screen.blit(help_text, (WIDTH // 2 - 150, HEIGHT - 40))

        pygame.display.flip()
        clock.tick(30)

gpio_handler = GPIOHandler()

def main():
    try:
        print("Starting main menu...")
        main_menu()
        # The program should only reach here if main_menu() exits without calling quit_game()
        # This happens when we click the Quit button or press MODE/ESC in the main menu
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # This code will run when the program is truly meant to exit
        print("Thank you for playing Pao'er Ship!")


# Also, let's modify the quit_game function to be more explicit
def quit_game():
    print("Exiting game...")
    if gpio_handler:
        gpio_handler.cleanup()
    if sound_manager:
        sound_manager.stop_background_music()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()