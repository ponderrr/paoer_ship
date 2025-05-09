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
from src.utils.constants import BACKGROUND_COLORS
from src.hardware.gpio_handler import GPIOHandler
from src.hardware.gpio_handler import GPIOHandler, IS_RASPBERRY_PI
from src.ui.main_menu import main_menu, Button  
from src.ui.settings_screen import settings_screen
from src.ui.game_mode_select import game_mode_select

import config

try:
    import gpiod
    IS_RASPBERRY_PI = True
except ImportError:
    IS_RASPBERRY_PI = False

pygame.init()

WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pao'er Ship")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
LIGHT_BLUE = (80, 170, 255)
LIGHT_GRAY = (180, 180, 180)
RED = (255, 0, 0)

pygame.font.init()
title_font = pygame.font.Font(None, 50)
button_font = pygame.font.Font(None, 30)

sound_manager = SoundManager()
sound_manager.start_background_music()

def quit_game():
    gpio_handler.cleanup()
    pygame.quit()
    sys.exit()

def select_background_color():
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    colors = list(BACKGROUND_COLORS.keys())
    selected = 0

    selecting = True
    while selecting:
        screen.fill(BLACK)

        title_text = font.render("Select Background Color", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 80))
        screen.blit(title_text, title_rect)

        for i, color in enumerate(colors):
            color_text = font.render(color, True, LIGHT_BLUE if i == selected else WHITE)
            color_rect = color_text.get_rect(center=(WIDTH // 2, 180 + i * 40))
            screen.blit(color_text, color_rect)

        help_font = pygame.font.Font(None, 24)
        help_text = help_font.render("Up/Down: Navigate | Fire: Select | Mode: Back", True, LIGHT_GRAY)
        screen.blit(help_text, (WIDTH // 2 - 180, HEIGHT - 40))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, pygame.K_TAB]:
                    selecting = False
                elif event.key == pygame.K_UP:
                    selected = (selected - 1) % len(colors)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(colors)
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    config.selected_background_color = BACKGROUND_COLORS[colors[selected]]
                    selecting = False

        button_states = gpio_handler.get_button_states()
        if button_states['up']:
            selected = (selected - 1) % len(colors)
        if button_states['down']:
            selected = (selected + 1) % len(colors)
        if button_states['fire']:
            config.selected_background_color = BACKGROUND_COLORS[colors[selected]]
            selecting = False
        if button_states['mode']:
            selecting = False

        pygame.display.flip()
        clock.tick(30)


def process_shot(x, y, shooter_board, target_board, shots_set):
    """Process a shot from one player to another's board"""
    board_x, board_y = y, x

    if (board_x, board_y) in shots_set:
        return False, False 

    shots_set.add((board_x, board_y))

    hit = False
    ship_sunk = False

    for ship in target_board.ships:
        if ship.receive_hit(board_x, board_y):
            hit = True
            ship_sunk = ship.is_sunk()
            break

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
                return 2  
            elif player2_lost:
                return 1  
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
        
        turn_timer = 30.0  
        timer_start = pygame.time.get_ticks() / 1000.0  
        timer_warning_threshold = 10.0  

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
            screen.fill(config.selected_background_color)

            mode_text = font.render(game_mode_text, True, WHITE)
            screen.blit(mode_text, (WIDTH - 200, 20))

            exit_text = small_font.render("Press MODE to exit", True, LIGHT_GRAY)
            screen.blit(exit_text, (20, HEIGHT - 30))
            
            if not ai_mode and not winner and not showing_exit_dialog:
                elapsed_time = pygame.time.get_ticks() / 1000.0 - timer_start
                remaining_time = max(0, turn_timer - elapsed_time)
                
                timer_color = RED if remaining_time < timer_warning_threshold else WHITE
                
                timer_text = font.render(f"Time: {remaining_time:.1f}", True, timer_color)
                timer_rect = timer_text.get_rect(center=(WIDTH // 2, 25))
                screen.blit(timer_text, timer_rect)
                
                if remaining_time <= 0 and not turn_in_progress:
                    sound_manager.play_sound("navigate_down") 
                    
                    if current_player == 1:
                        transition_screen.show_player_ready_screen(2)
                        current_player = 2
                    else:
                        transition_screen.show_player_ready_screen(1)
                        current_player = 1
                    
                    timer_start = pygame.time.get_ticks() / 1000.0

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

            board_center_x = WIDTH // 2 - 150  
            draw_board(
                screen,
                font,
                view_board,
                board_center_x,
                80,
                30,
                cursor_x if (current_player == 1 or (current_player == 2 and not ai_mode)) else -1,
                cursor_y if (current_player == 1 or (current_player == 2 and not ai_mode)) else -1,
                (current_player == 1 or (current_player == 2 and not ai_mode)),
                "Opponent's Board"
            )

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
                                                screen.fill(config.selected_background_color)
                                                draw_board(screen, font, player1_view, board_center_x, 80, 30, cursor_x, cursor_y, True, "Your Shot")

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
                                            timer_start = pygame.time.get_ticks() / 1000.0  
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
                                            timer_start = pygame.time.get_ticks() / 1000.0  
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
                                        screen.fill(config.selected_background_color)
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
                                    timer_start = pygame.time.get_ticks() / 1000.0  
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
                                    timer_start = pygame.time.get_ticks() / 1000.0 
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


                screen.fill(config.selected_background_color)
                draw_board(screen, font, player2_view, board_center_x, 80, 30, -1, -1, False, "AI's Shot")
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
                            sound_manager.play_sound("hit")
                            if ship_sunk:
                                sound_manager.play_sound("ship_sunk")
                        else:
                            player1_board.board[board_x, board_y] = CellState.MISS.value
                            player2_view[board_x][board_y] = CellState.MISS.value
                            player1_own_view[board_x][board_y] = CellState.MISS.value
                            sound_manager.play_sound("miss")

                        ai_opponent.process_shot_result(board_x, board_y, hit, ship_sunk)

                    screen.fill(config.selected_background_color)
                    draw_board(screen, font, player2_view, board_center_x, 80, 30, display_x, display_y, True, "AI's Shot")

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
    
    board_width = 10 * cell_size
    board_height = 10 * cell_size
    
    if title:
        title_text = font.render(title, True, WHITE)
        title_rect = title_text.get_rect(center=(offset_x + board_width // 2, offset_y - 30))
        screen.blit(title_text, title_rect)

    for i in range(10):
        letter = chr(65 + i)
        text = pygame.font.Font(None, 20).render(letter, True, WHITE)
        screen.blit(text, (offset_x + i * cell_size + cell_size // 3, offset_y - 20))

    for i in range(10):
        number = str(i + 1)
        text = pygame.font.Font(None, 20).render(number, True, WHITE)
        screen.blit(text, (offset_x - 20, offset_y + i * cell_size + cell_size // 3))

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

    if show_cursor and cursor_x >= 0 and cursor_y >= 0:
        cursor_rect = pygame.Rect(
            offset_x + cursor_x * cell_size - 2,
            offset_y + cursor_y * cell_size - 2,
            cell_size + 2,
            cell_size + 2
        )
        pygame.draw.rect(screen, (255, 255, 0), cursor_rect, 2)


gpio_handler = GPIOHandler()


def main():
    try:
        global gpio_handler, sound_manager
        
        if not gpio_handler:
            gpio_handler = GPIOHandler()
            
        if not hasattr(sound_manager, 'sounds') or sound_manager.sounds is None:
            sound_manager = SoundManager()
            sound_manager.start_background_music()
        
        main_menu(screen, WIDTH, HEIGHT, gpio_handler, sound_manager, 
                 game_mode_select, settings_screen, 
                 select_background_color, quit_game)
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Cleaning up resources...")
        if gpio_handler:
            gpio_handler.cleanup()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
