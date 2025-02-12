# src/input/button_handler.py
import pygame

class ButtonHandler:
    def __init__(self):
        self.cursor_x = 0
        self.cursor_y = 0
        self.max_grid = 9  # 10x10 grid (0-9)

    def update(self, keys):
        """Handle keyboard input and return any actions"""
        actions = {
            'moved': False,
            'fired': False,
            'mode_changed': False,
            'position': (self.cursor_x, self.cursor_y)
        }

        # Arrow key movement
        if keys[pygame.K_LEFT] and self.cursor_x > 0:
            self.cursor_x -= 1
            actions['moved'] = True
        if keys[pygame.K_RIGHT] and self.cursor_x < self.max_grid:
            self.cursor_x += 1
            actions['moved'] = True
        if keys[pygame.K_UP] and self.cursor_y > 0:
            self.cursor_y -= 1
            actions['moved'] = True
        if keys[pygame.K_DOWN] and self.cursor_y < self.max_grid:
            self.cursor_y += 1
            actions['moved'] = True

        # Fire action
        if keys[pygame.K_SPACE]:
            actions['fired'] = True

        # Mode switch
        if keys[pygame.K_TAB]:
            actions['mode_changed'] = True

        return actions