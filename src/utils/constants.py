import pygame

# Screen settings
WIDTH, HEIGHT = 600, 600
GRID_SIZE = 10
CELL_SIZE = WIDTH // GRID_SIZE

# Colors
LINE_COLOR = (255, 255, 255)
SHIP_COLOR = (100, 100, 255)
BACKGROUND_COLOR = (0, 0, 50)

# Pygame fonts
pygame.font.init()
FONT = pygame.font.Font(None, 36)
