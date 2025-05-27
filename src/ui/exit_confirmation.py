import pygame
import config


class ExitConfirmation:
    def __init__(self, screen, gpio_handler):
        """
        Initialize the exit confirmation dialog

        Args:
            screen: Pygame screen surface
            gpio_handler: GPIO interface for button inputs
        """
        self.screen = screen
        self.gpio_handler = gpio_handler

        self.width = screen.get_width()
        self.height = screen.get_height()

        self.title_font_size = config.get_font_size(self.height, 36)
        self.info_font_size = config.get_font_size(self.height, 24)
        self.title_font = pygame.font.Font(None, self.title_font_size)
        self.info_font = pygame.font.Font(None, self.info_font_size)

        self.last_button_states = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "fire": False,
            "mode": False,
            "rotate": False,
        }

    def get_button_states(self):
        """Get button states with edge detection"""
        if self.gpio_handler:
            current_states = self.gpio_handler.get_button_states()
        else:
            keys = pygame.key.get_pressed()
            current_states = {
                "up": keys[config.INPUT_MOVE_UP],
                "down": keys[config.INPUT_MOVE_DOWN],
                "left": keys[config.INPUT_MOVE_LEFT],
                "right": keys[config.INPUT_MOVE_RIGHT],
                "fire": keys[config.INPUT_FIRE],
                "mode": keys[config.INPUT_MODE],
                "rotate": keys[config.INPUT_ROTATE],
            }

        button_states = {}
        for key in current_states:
            button_states[key] = (
                current_states[key] and not self.last_button_states[key]
            )
            self.last_button_states[key] = current_states[key]

        return button_states

    def show(self):
        """
        Show the exit confirmation dialog

        Returns:
            bool: True if exit confirmed, False if cancelled
        """
        dialog_width = int(min(400, self.width * 0.4))
        dialog_height = int(min(200, self.height * 0.25))

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        dialog_rect = pygame.Rect(
            (self.width - dialog_width) // 2,
            (self.height - dialog_height) // 2,
            dialog_width,
            dialog_height,
        )

        pygame.draw.rect(self.screen, (50, 50, 50), dialog_rect, border_radius=10)
        pygame.draw.rect(self.screen, config.WHITE, dialog_rect, 2, border_radius=10)

        title = self.title_font.render("Exit Game?", True, config.WHITE)
        title_rect = title.get_rect(
            center=(self.width // 2, dialog_rect.top + dialog_height // 5)
        )
        self.screen.blit(title, title_rect)

        message = self.info_font.render(
            "Are you sure you want to exit the game?", True, config.LIGHT_GRAY
        )
        message_rect = message.get_rect(
            center=(self.width // 2, dialog_rect.top + dialog_height // 2.5)
        )
        self.screen.blit(message, message_rect)

        mode_text = self.info_font.render(
            "Press MODE again to confirm exit", True, config.RED
        )
        mode_rect = mode_text.get_rect(
            center=(self.width // 2, dialog_rect.top + dialog_height * 0.6)
        )
        self.screen.blit(mode_text, mode_rect)

        any_text = self.info_font.render(
            "Press any other button to continue playing", True, config.LIGHT_BLUE
        )
        any_rect = any_text.get_rect(
            center=(self.width // 2, dialog_rect.top + dialog_height * 0.8)
        )
        self.screen.blit(any_text, any_rect)

        pygame.display.flip()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return True
                elif event.type == pygame.KEYDOWN:
                    if event.key == config.INPUT_MODE:
                        return True
                    else:
                        return False

            button_states = self.get_button_states()
            if button_states["mode"]:
                return True
            elif any(value for key, value in button_states.items() if key != "mode"):
                return False

            pygame.time.delay(50)
