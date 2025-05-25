"""
Pao'er Ship - A Battleship-style game for Raspberry Pi
Main entry point and game logic
"""

import pygame
import sys
import time
import numpy as np
import random

# Import centralized configuration
import config

from src.board.game_board import GameBoard, CellState
from src.ui.ship_placement_screen import ShipPlacementScreen
from src.game.ai_opponent import AIOpponent, AIDifficulty
from src.utils.image_display import ImageDisplay
from src.sound.sound_manager import SoundManager
from src.hardware.gpio_handler import GPIOHandler, IS_RASPBERRY_PI
from src.ui.main_menu import main_menu
from src.ui.settings_screen import settings_screen
from src.ui.game_mode_select import game_mode_select
from src.ui.turn_transition_screen import TurnTransitionScreen
from src.ui.exit_confirmation import ExitConfirmation

# Initialize Pygame
pygame.init()

# Display setup using config
screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
pygame.display.set_caption("Pao'er Ship")

# Font initialization using config
pygame.font.init()
title_font = pygame.font.Font(None, config.TITLE_FONT_SIZE)
button_font = pygame.font.Font(None, config.BUTTON_FONT_SIZE)

# Global managers
sound_manager = SoundManager()
gpio_handler = GPIOHandler()


def quit_game():
    """Clean shutdown of the game"""
    gpio_handler.cleanup()
    pygame.quit()
    sys.exit()


def select_background_color():
    """Background color selection interface"""
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    colors = list(config.BACKGROUND_COLORS.keys())
    selected = 0

    selecting = True
    while selecting:
        screen.fill(config.BLACK)

        title_text = font.render("Select Background Color", True, config.WHITE)
        title_rect = title_text.get_rect(center=(config.SCREEN_WIDTH // 2, 80))
        screen.blit(title_text, title_rect)

        for i, color in enumerate(colors):
            color_text = font.render(
                color, True, config.LIGHT_BLUE if i == selected else config.WHITE
            )
            color_rect = color_text.get_rect(
                center=(config.SCREEN_WIDTH // 2, 180 + i * 40)
            )
            screen.blit(color_text, color_rect)

        help_font = pygame.font.Font(None, config.SMALL_FONT_SIZE)
        help_text = help_font.render(
            "Up/Down: Navigate | Fire: Select | Mode: Back", True, config.LIGHT_GRAY
        )
        screen.blit(
            help_text, (config.SCREEN_WIDTH // 2 - 180, config.SCREEN_HEIGHT - 40)
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, config.INPUT_MODE]:
                    selecting = False
                elif event.key == config.INPUT_MOVE_UP:
                    selected = (selected - 1) % len(colors)
                elif event.key == config.INPUT_MOVE_DOWN:
                    selected = (selected + 1) % len(colors)
                elif event.key in [pygame.K_RETURN, config.INPUT_FIRE]:
                    config.selected_background_color = config.BACKGROUND_COLORS[
                        colors[selected]
                    ]
                    selecting = False

        button_states = gpio_handler.get_button_states()
        if button_states["up"]:
            selected = (selected - 1) % len(colors)
        if button_states["down"]:
            selected = (selected + 1) % len(colors)
        if button_states["fire"]:
            config.selected_background_color = config.BACKGROUND_COLORS[
                colors[selected]
            ]
            selecting = False
        if button_states["mode"]:
            selecting = False

        pygame.display.flip()
        clock.tick(config.TARGET_FPS)


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


def draw_board(
    screen,
    font,
    board,
    offset_x,
    offset_y,
    cell_size,
    cursor_x,
    cursor_y,
    show_cursor,
    title=None,
):
    """Draw a game board with optional cursor and title"""
    board_width = config.BOARD_SIZE * cell_size
    board_height = config.BOARD_SIZE * cell_size

    if title:
        title_text = font.render(title, True, config.WHITE)
        title_rect = title_text.get_rect(
            center=(offset_x + board_width // 2, offset_y - 30)
        )
        screen.blit(title_text, title_rect)

    # Draw coordinate labels
    for i in range(config.BOARD_SIZE):
        letter = chr(65 + i)
        text = pygame.font.Font(None, 20).render(letter, True, config.WHITE)
        screen.blit(text, (offset_x + i * cell_size + cell_size // 3, offset_y - 20))

    for i in range(config.BOARD_SIZE):
        number = str(i + 1)
        text = pygame.font.Font(None, 20).render(number, True, config.WHITE)
        screen.blit(text, (offset_x - 20, offset_y + i * cell_size + cell_size // 3))

    # Draw board cells
    for y in range(config.BOARD_SIZE):
        for x in range(config.BOARD_SIZE):
            cell_rect = pygame.Rect(
                offset_x + x * cell_size,
                offset_y + y * cell_size,
                cell_size - 2,
                cell_size - 2,
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

            pygame.draw.rect(screen, color, cell_rect)
            pygame.draw.rect(screen, config.COLOR_GRID, cell_rect, 1)

    # Draw cursor
    if show_cursor and cursor_x >= 0 and cursor_y >= 0:
        cursor_rect = pygame.Rect(
            offset_x + cursor_x * cell_size - 2,
            offset_y + cursor_y * cell_size - 2,
            cell_size + 2,
            cell_size + 2,
        )
        pygame.draw.rect(screen, config.COLOR_CURSOR, cursor_rect, 2)


def check_game_over(player1_board, player2_board):
    """Check if the game is over and return winner"""
    player1_lost = all(ship.is_sunk() for ship in player1_board.ships)
    player2_lost = all(ship.is_sunk() for ship in player2_board.ships)

    if player1_lost:
        return 2
    elif player2_lost:
        return 1
    return None


def main():
    """Main entry point"""
    try:
        sound_manager.start_background_music()

        main_menu(
            screen,
            config.SCREEN_WIDTH,
            config.SCREEN_HEIGHT,
            gpio_handler,
            sound_manager,
            lambda: game_mode_select(screen, gpio_handler, sound_manager, game_screen),
            lambda: settings_screen(screen, gpio_handler, sound_manager),
            select_background_color,
            quit_game,
        )

    except KeyboardInterrupt:
        pass
    except Exception as e:
        if config.ENABLE_DEBUG_PRINTS:
            print(f"Error: {e}")
    finally:
        if gpio_handler:
            gpio_handler.cleanup()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
