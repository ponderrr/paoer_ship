import pygame
from board.game_board import draw_grid
from board.ship import Ship
from utils.constants import WIDTH, HEIGHT, BACKGROUND_COLOR, CELL_SIZE, FONT

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Battleship")

ships = []

def handle_mouse_click(pos):
    """Places ships when clicking on the board."""
    col = pos[0] // CELL_SIZE
    row = pos[1] // CELL_SIZE
    new_ship = Ship(length=3, orientation="horizontal", position=(row, col))
    ships.append(new_ship)

def draw_button(text, x, y, width, height):
    """Draws a button on the screen."""
    pygame.draw.rect(screen, (200, 0, 0), (x, y, width, height))
    label = FONT.render(text, True, (255, 255, 255))
    screen.blit(label, (x + 10, y + 10))

running = True
while running:
    screen.fill(BACKGROUND_COLOR)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            handle_mouse_click(event.pos)

    draw_grid(screen)

    for ship in ships:
        ship.draw(screen)

    draw_button("Start Game", 450, 50, 120, 40)

    pygame.display.flip()

pygame.quit()
