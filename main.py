import pygame
import sys
import random
from src.board.game_board import GameBoard
from src.hardware.display_mock import DisplayMock

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
fullscreen_enabled = False  # Default to windowed mode
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pao'er Ship")

# Colors
WHITE = (255, 255, 255)
BLACK = (20, 20, 30)  # Darker background for a sleek look
BLUE = (50, 150, 255)  # Vibrant blue for a modern feel
DARK_BLUE = (30, 100, 200)
LIGHT_BLUE = (80, 170, 255)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)

# Game settings
sound_on = True
difficulty = "Medium"
ai_animations = True
board_theme = "Classic"
grid_enabled = True

# Load fonts
pygame.font.init()
title_font = pygame.font.Font(None, 70)
button_font = pygame.font.Font(None, 40)

# 🛠 Modern Button Class
class Button:
    def __init__(self, x, y, width, height, text, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.base_color = BLUE
        self.hover_color = LIGHT_BLUE
        self.current_color = self.base_color

    def draw(self, screen):
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=15)
        text_surface = button_font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.current_color = self.hover_color if self.rect.collidepoint(pos) else self.base_color

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.action()

# 🌅 Animated Gradient Background
def draw_background():
    gradient = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        color = (
            int(BLACK[0] + (BLUE[0] - BLACK[0]) * (y / HEIGHT)),
            int(BLACK[1] + (BLUE[1] - BLACK[1]) * (y / HEIGHT)),
            int(BLACK[2] + (BLUE[2] - BLACK[2]) * (y / HEIGHT)),
        )
        pygame.draw.line(gradient, color, (0, y), (WIDTH, y))
    screen.blit(gradient, (0, 0))

# 🎚 Settings Menu with Fullscreen Toggle
def settings_menu():
    global sound_on, difficulty, ai_animations, board_theme, grid_enabled, fullscreen_enabled, screen
    running = True

    # Toggle Fullscreen
    def toggle_fullscreen():
        global fullscreen_enabled, screen
        fullscreen_enabled = not fullscreen_enabled
        if fullscreen_enabled:
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode((WIDTH, HEIGHT))

    buttons = [
        Button(250, 150, 300, 60, f"Sound: {'ON' if sound_on else 'OFF'}", lambda: toggle_setting("sound")),
        Button(250, 220, 300, 60, f"Difficulty: {difficulty}", lambda: toggle_setting("difficulty")),
        Button(250, 290, 300, 60, f"AI Animations: {'ON' if ai_animations else 'OFF'}", lambda: toggle_setting("ai_animations")),
        Button(250, 360, 300, 60, f"Board Theme: {board_theme}", lambda: toggle_setting("board_theme")),
        Button(250, 430, 300, 60, f"Grid Lines: {'ON' if grid_enabled else 'OFF'}", lambda: toggle_setting("grid")),
        Button(250, 500, 300, 60, f"Fullscreen: {'ON' if fullscreen_enabled else 'OFF'}", toggle_fullscreen),
        Button(250, 570, 300, 60, "Back", main_menu)
    ]

    while running:
        draw_background()
        screen.blit(title_font.render("Settings", True, WHITE), (300, 80))

        for button in buttons:
            button.text = f"Sound: {'ON' if sound_on else 'OFF'}" if button.text.startswith("Sound") else button.text
            button.text = f"Difficulty: {difficulty}" if button.text.startswith("Difficulty") else button.text
            button.text = f"AI Animations: {'ON' if ai_animations else 'OFF'}" if button.text.startswith("AI") else button.text
            button.text = f"Board Theme: {board_theme}" if button.text.startswith("Board") else button.text
            button.text = f"Grid Lines: {'ON' if grid_enabled else 'OFF'}" if button.text.startswith("Grid") else button.text
            button.text = f"Fullscreen: {'ON' if fullscreen_enabled else 'OFF'}" if button.text.startswith("Fullscreen") else button.text

            button.check_hover(pygame.mouse.get_pos())
            button.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: quit_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons: button.check_click(pygame.mouse.get_pos())

        pygame.display.flip()

# 🎮 Start Game function
def start_game():
    game_loop()

# ❌ Quit function
def quit_game():
    pygame.quit()
    sys.exit()

# 🏠 Modern Main Menu
def main_menu():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN if fullscreen_enabled else 0)

    buttons = [
        Button(300, 250, 200, 60, "Start Game", start_game),
        Button(300, 350, 200, 60, "Settings", settings_menu),
        Button(300, 450, 200, 60, "Quit", quit_game)
    ]

    while True:
        draw_background()
        screen.blit(title_font.render("Pao'er Ship", True, WHITE), (250, 80))

        for button in buttons:
            button.check_hover(pygame.mouse.get_pos())
            button.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: quit_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons: button.check_click(pygame.mouse.get_pos())

        pygame.display.flip()

# 🎯 Modern Game Loop with Fullscreen Support
def game_loop():
    board = GameBoard()
    display = DisplayMock()
    display.init_display()

    if difficulty == "Pao (Impossible)":
        board.pao_mode = True

    board.place_ship(2, 3, 3, horizontal=True)
    board.place_ship(5, 5, 4, horizontal=False)

    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                grid_x, grid_y = (x - 50) // UIConstants.CELL_SIZE, (y - 50) // UIConstants.CELL_SIZE
                if 0 <= grid_x < UIConstants.GRID_SIZE and 0 <= grid_y < UIConstants.GRID_SIZE:
                    hit, all_sunk = board.fire(grid_x, grid_y)

                    if all_sunk:
                        game_over_screen()
                        return

        # ✅ Now the function matches DisplayMock's method
        display.update(board.get_display_state(), show_grid=grid_enabled)

        clock.tick(60)


def game_over_screen():
    """Displays a Game Over screen when the player wins."""
    screen.fill(UIConstants.BLACK)
    game_over_text = title_font.render("Game Over! You Win!", True, UIConstants.WHITE)
    screen.blit(game_over_text, (UIConstants.WINDOW_SIZE[0] // 4, UIConstants.WINDOW_SIZE[1] // 3))

    pygame.display.flip()
    pygame.time.delay(3000)  # Show for 3 seconds
    main_menu()


# 🏁 Main Function
def main():
    main_menu()
    game_loop()

if __name__ == "__main__":
    main()
