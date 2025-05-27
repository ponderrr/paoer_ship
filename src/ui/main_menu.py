import pygame
import sys
import config
from src.sound.sound_manager import SoundManager


class Button:
    def __init__(self, x, y, width, height, text, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.base_color = config.BLUE
        self.hover_color = config.LIGHT_BLUE
        self.current_color = self.base_color
        self.hovered = False
        self.selected = False
        self.border_color = config.WHITE
        self.border_width = 2

    def update(self):
        self.current_color = (
            self.hover_color if (self.selected or self.hovered) else self.base_color
        )

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            self.current_color,
            self.rect,
            border_radius=config.BUTTON_BORDER_RADIUS,
        )

        if self.selected:
            pygame.draw.rect(
                screen,
                config.YELLOW,
                self.rect,
                3,
                border_radius=config.BUTTON_BORDER_RADIUS,
            )
        else:
            pygame.draw.rect(
                screen,
                self.border_color,
                self.rect,
                2,
                border_radius=config.BUTTON_BORDER_RADIUS,
            )

        text_surface = pygame.font.Font(None, config.BUTTON_FONT_SIZE).render(
            self.text, True, config.WHITE
        )
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.action()


def main_menu(
    screen,
    width,
    height,
    gpio_handler,
    sound_manager,
    game_mode_select_func,
    settings_screen_func,
    select_background_color_func,
    quit_game_func,
):
    """
    Main menu screen with buttons for game options

    Args:
        screen: Pygame display surface
        width: Screen width
        height: Screen height
        gpio_handler: GPIO handler for button inputs
        sound_manager: Sound manager instance
        game_mode_select_func: Function to launch game mode selection
        settings_screen_func: Function to launch settings screen
        select_background_color_func: Function to launch background color selection
        quit_game_func: Function to quit the game
    """
    center_x = (width - config.BUTTON_WIDTH) // 2
    start_y = 200

    buttons = [
        Button(
            center_x,
            start_y,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Start Game",
            game_mode_select_func,
        ),
        Button(
            center_x,
            start_y + config.BUTTON_SPACING,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Settings",
            settings_screen_func,
        ),
        Button(
            center_x,
            start_y + config.BUTTON_SPACING * 2,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Background Color",
            select_background_color_func,
        ),
        Button(
            center_x,
            start_y + config.BUTTON_SPACING * 3,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Quit",
            quit_game_func,
        ),
    ]

    title_font = pygame.font.Font(None, config.TITLE_FONT_SIZE)
    help_font = pygame.font.Font(None, config.SMALL_FONT_SIZE)

    current_selection = 0
    buttons[current_selection].selected = True
    clock = pygame.time.Clock()
    running = True

    while running:
        screen.fill(config.selected_background_color)
        title_text = title_font.render("Pao'er Ship", True, config.WHITE)
        title_rect = title_text.get_rect(center=(width // 2, 100))
        screen.blit(title_text, title_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                for button in buttons:
                    button.check_hover(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    button.check_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == config.INPUT_MOVE_UP:
                    for button in buttons:
                        button.selected = False
                    current_selection = (current_selection - 1) % len(buttons)
                    buttons[current_selection].selected = True
                elif event.key == config.INPUT_MOVE_DOWN:
                    for button in buttons:
                        button.selected = False
                    current_selection = (current_selection + 1) % len(buttons)
                    buttons[current_selection].selected = True
                elif event.key in [pygame.K_RETURN, config.INPUT_FIRE]:
                    buttons[current_selection].action()
                elif event.key == pygame.K_ESCAPE:
                    running = False

        button_states = gpio_handler.get_button_states()
        if button_states["up"]:
            for button in buttons:
                button.selected = False
            current_selection = (current_selection - 1) % len(buttons)
            buttons[current_selection].selected = True

        if button_states["down"]:
            for button in buttons:
                button.selected = False
            current_selection = (current_selection + 1) % len(buttons)
            buttons[current_selection].selected = True

        if button_states["fire"]:
            buttons[current_selection].action()

        for button in buttons:
            button.update()
            button.draw(screen)

        help_text = help_font.render(
            "Up/Down: Navigate | Fire: Select | Mode: Back", True, config.LIGHT_GRAY
        )
        screen.blit(help_text, (width // 2 - 150, height - 40))

        pygame.display.flip()
        clock.tick(config.TARGET_FPS)
