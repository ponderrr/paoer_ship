import pygame
from .display_interface import DisplayInterface

class DisplayMock(DisplayInterface):
    def __init__(self, width=1920, height=1080, fullscreen=True):
        self.fullscreen = fullscreen
        self.width = width
        self.height = height
        self.cell_size = min(width, height) // 17 if fullscreen else 40  # Adjust for fullscreen
        board_width = self.cell_size * 10
        board_height = self.cell_size * 10
        self.grid_offset_x = (width - board_width) // 2  
        self.grid_offset_y = (height - board_height) // 2  
        self.screen = None
        self.font = None
        self.status_message = "Welcome to Pao'er Ship!"

    def init_display(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Pao'er Ship - Development View")
        self.font = pygame.font.SysFont('Arial', 24)

    def update(self, board_state, show_grid=True):
        if self.screen is None:
            return
        self.screen.fill((20, 20, 30))
        self._draw_lcd_display()
        self._draw_grid_coordinates()
        self._draw_control_buttons()
        self._draw_game_grid(board_state, show_grid)
        pygame.display.flip()

    def cleanup(self):
        pygame.quit()

    def _draw_cursor(self, x, y):
        """Draw the cursor at the specified grid position."""
        cursor_rect = pygame.Rect(
            x * self.cell_size + self.grid_offset_x,  
            y * self.cell_size + self.grid_offset_y,
            self.cell_size - 2,
            self.cell_size - 2
        )
        pygame.draw.rect(self.screen, (255, 255, 0), cursor_rect, 3)

    def _draw_lcd_display(self):
        lcd_rect = pygame.Rect(self.width - 350, 50, 300, 100)
        pygame.draw.rect(self.screen, (200, 200, 200), lcd_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), lcd_rect, 2)
        text = self.font.render(self.status_message, True, (0, 0, 0))
        text_rect = text.get_rect(center=lcd_rect.center)
        self.screen.blit(text, text_rect)

    def _draw_grid_coordinates(self):
        for x in range(10):
            label = self.font.render(chr(65 + x), True, (200, 200, 200))
            self.screen.blit(label, (self.grid_offset_x + x * self.cell_size + 15, self.grid_offset_y - 30))
        for y in range(10):
            label = self.font.render(str(y + 1), True, (200, 200, 200))
            self.screen.blit(label, (self.grid_offset_x - 30, self.grid_offset_y + y * self.cell_size + 10))

    def _draw_control_buttons(self):
        pass

    def _draw_game_grid(self, board_state, show_grid=True):
        for y in range(len(board_state)):
            for x in range(len(board_state[0])):
                color = self._get_cell_color(board_state[y][x])
                cell_x = x * self.cell_size + self.grid_offset_x
                cell_y = y * self.cell_size + self.grid_offset_y
                cell_rect = pygame.Rect(cell_x, cell_y, self.cell_size - 2, self.cell_size - 2)
                shadow_offset = 3
                shadow_rect = cell_rect.copy()
                shadow_rect.x += shadow_offset
                shadow_rect.y += shadow_offset
                pygame.draw.rect(self.screen, (30, 30, 30), shadow_rect, border_radius=8)
                pygame.draw.rect(self.screen, color, cell_rect, border_radius=8)
                if show_grid:
                    pygame.draw.rect(self.screen, (50, 50, 50), cell_rect, 1, border_radius=8)

    def _get_cell_color(self, cell_value):
        colors = {0: (50, 50, 50), 1: (0, 255, 0), 2: (255, 0, 0), 3: (0, 0, 255)}
        return colors.get(cell_value, (128, 128, 128))

    def set_status(self, message):
        self.status_message = message
