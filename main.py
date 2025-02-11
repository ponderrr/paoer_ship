# main.py

import pygame
from src.board.game_board import GameBoard
from src.hardware.display_mock import DisplayMock

def main():
    # Initialize components
    board = GameBoard()
    display = DisplayMock()

    # Setup
    display.init_display()
    
    # Place some test ships
    board.place_ship(2, 3, 3, horizontal=True)
    board.place_ship(5, 5, 4, horizontal=False)

    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Convert mouse position to grid coordinates
                x, y = pygame.mouse.get_pos()
                grid_x = (x - 50) // 40
                grid_y = (y - 50) // 40
                if 0 <= grid_x < 10 and 0 <= grid_y < 10:
                    board.fire(grid_x, grid_y)

        # Update display
        display.update(board.get_display_state())
        clock.tick(60)

    display.cleanup()

if __name__ == "__main__":
    main()