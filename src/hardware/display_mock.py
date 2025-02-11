# src/hardware/display_mock.py

import pygame
from .display_interface import DisplayInterface

class DisplayMock(DisplayInterface):
    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        self.cell_size = 40
        self.screen = None
        
    def init_display(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Pao'er Ship - Development View")

    def update(self, board_state):
        if self.screen is None:
            return

        self.screen.fill((0, 0, 0))  # Black background
        
        # Draw grid
        for y in range(len(board_state)):
            for x in range(len(board_state[0])):
                color = self._get_cell_color(board_state[y][x])
                rect = pygame.Rect(
                    x * self.cell_size + 50,
                    y * self.cell_size + 50,
                    self.cell_size - 2,
                    self.cell_size - 2
                )
                pygame.draw.rect(self.screen, color, rect)
        
        pygame.display.flip()

    def _get_cell_color(self, cell_value):
        colors = {
            0: (50, 50, 50),    # Empty - Dark Gray
            1: (0, 255, 0),     # Ship - Green
            2: (255, 0, 0),     # Hit - Red
            3: (0, 0, 255)      # Miss - Blue
        }
        return colors.get(cell_value, (128, 128, 128))

    def cleanup(self):
        pygame.quit()