import pygame
from utils.constants import WIDTH, HEIGHT, GRID_SIZE, CELL_SIZE, LINE_COLOR

def draw_grid(screen):
    """Draws a 10x10 grid for the game board."""
    for x in range(0, WIDTH, CELL_SIZE):
        pygame.draw.line(screen, LINE_COLOR, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, LINE_COLOR, (0, y), (WIDTH, y))
