# main.py
import pygame
from src.board.game_board import GameBoard
from src.hardware.display_mock import DisplayMock
from src.input.button_handler import ButtonHandler

def main():
    # Initialize components
    board = GameBoard()
    display = DisplayMock()
    button_handler = ButtonHandler()

    # Setup
    display.init_display()
    
    # Place some test ships
    board.place_ship(2, 3, 3, horizontal=True)
    board.place_ship(5, 5, 4, horizontal=False)

    running = True
    clock = pygame.time.Clock()
    last_fire_time = 0  # Prevent rapid-fire
    fire_delay = 250  # Milliseconds between shots

    while running:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Handle input
        keys = pygame.key.get_pressed()
        actions = button_handler.update(keys)

        # Process actions
        if actions['moved']:
            display.set_status(f"Cursor at {chr(65 + actions['position'][0])}{actions['position'][1] + 1}")

        if actions['fired'] and current_time - last_fire_time > fire_delay:
            x, y = actions['position']
            hit, sunk = board.fire(x, y)
            if hit:
                display.set_status(f"HIT at {chr(65 + x)}{y + 1}!")
            else:
                display.set_status(f"Miss at {chr(65 + x)}{y + 1}")
            last_fire_time = current_time

        if actions['mode_changed']:
            display.set_status("Mode changed!")

        # Update display
        display.update(board.get_display_state())
        display._draw_cursor(button_handler.cursor_x, button_handler.cursor_y)
        pygame.display.flip()
        clock.tick(60)

    display.cleanup()

if __name__ == "__main__":
    main()