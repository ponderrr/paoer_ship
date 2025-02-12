# src/hardware/display_mock.py
import pygame
from .display_interface import DisplayInterface

class DisplayMock(DisplayInterface):
    def __init__(self, width=1024, height=768):
        self.width = width
        self.height = height
        self.cell_size = 40
        self.grid_offset_x = 100
        self.grid_offset_y = 100
        self.screen = None
        self.font = None
        self.status_message = "Welcome to Pao'er Ship!"

    def _draw_cursor(self, x, y):
        """Draw the cursor at the specified grid position"""
        cursor_rect = pygame.Rect(
            x * self.cell_size + self.grid_offset_x,
            y * self.cell_size + self.grid_offset_y,
            self.cell_size - 2,
            self.cell_size - 2
        )
        pygame.draw.rect(self.screen, (255, 255, 0), cursor_rect, 3)  # Yellow cursor
        
    def init_display(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Pao'er Ship - Development View")
        self.font = pygame.font.SysFont('Arial', 24)

    def update(self, board_state, show_grid=True):
        if self.screen is None:
            return

        self.screen.fill((20, 20, 30))  # Dark blue-gray background
        
        # Draw LCD display area
        self._draw_lcd_display()
        
        # Draw grid coordinates
        self._draw_grid_coordinates()
        
        # Draw control buttons
        self._draw_control_buttons()
        
        # Draw game grid
        self._draw_game_grid(board_state, show_grid)
        
        pygame.display.flip()

    def _draw_lcd_display(self):
        # LCD display area
        lcd_rect = pygame.Rect(self.width - 300, 50, 250, 100)
        pygame.draw.rect(self.screen, (200, 200, 200), lcd_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), lcd_rect, 2)
        
        # Render status text
        text = self.font.render(self.status_message, True, (0, 0, 0))
        text_rect = text.get_rect(center=lcd_rect.center)
        self.screen.blit(text, text_rect)

    def _draw_grid_coordinates(self):
        # Draw column labels (A-J)
        for x in range(10):
            label = self.font.render(chr(65 + x), True, (200, 200, 200))
            self.screen.blit(label, (self.grid_offset_x + x * self.cell_size + 15, 
                                   self.grid_offset_y - 30))

        # Draw row labels (1-10)
        for y in range(10):
            label = self.font.render(str(y + 1), True, (200, 200, 200))
            self.screen.blit(label, (self.grid_offset_x - 30, 
                                   self.grid_offset_y + y * self.cell_size + 10))

    def _draw_control_buttons(self):
        button_colors = {
            'UP': (0, 255, 0),
            'DOWN': (0, 255, 0),
            'LEFT': (0, 255, 0),
            'RIGHT': (0, 255, 0),
            'FIRE': (255, 0, 0),
            'MODE': (0, 0, 255)
        }
        
        button_positions = {
            'UP': (650, 500),
            'DOWN': (650, 600),
            'LEFT': (600, 550),
            'RIGHT': (700, 550),
            'FIRE': (800, 550),
            'MODE': (900, 550)
        }

        for button, pos in button_positions.items():
            pygame.draw.circle(self.screen, button_colors[button], pos, 20)
            text = self.font.render(button, True, (255, 255, 255))
            text_rect = text.get_rect(center=(pos[0], pos[1] + 40))
            self.screen.blit(text, text_rect)

    def _draw_game_grid(self, board_state, show_grid=True):
        for y in range(len(board_state)):
            for x in range(len(board_state[0])):
                color = self._get_cell_color(board_state[y][x])
                rect = pygame.Rect(
                    x * self.cell_size + self.grid_offset_x,
                    y * self.cell_size + self.grid_offset_y,
                    self.cell_size - 2,
                    self.cell_size - 2
                )
                pygame.draw.rect(self.screen, color, rect)
                
                # Draw grid lines if enabled
                if show_grid:
                    pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)

    def _get_cell_color(self, cell_value):
        colors = {
            0: (50, 50, 50),     # Empty - Dark Gray
            1: (0, 255, 0),      # Ship - Green
            2: (255, 0, 0),      # Hit - Red
            3: (0, 0, 255)       # Miss - Blue
        }
        return colors.get(cell_value, (128, 128, 128))

    def set_status(self, message):
        """Update the LCD status message"""
        self.status_message = message

    def cleanup(self):
        pygame.quit()