"""
Pyglet-based implementation of the display interface for the battleship game.
This replaces the Pygame-based DisplayMock with a Pyglet implementation.
"""
import pyglet
from pyglet import shapes
from .display_interface import DisplayInterface

class PygletDisplay(DisplayInterface):
    def __init__(self, width=1920, height=1080, fullscreen=True):
        self.fullscreen = fullscreen
        self.width = width
        self.height = height
        self.cell_size = min(width, height) // 17 if fullscreen else 40  # Adjust for fullscreen
        board_width = self.cell_size * 10
        board_height = self.cell_size * 10
        self.grid_offset_x = (width - board_width) // 2  
        self.grid_offset_y = (height - board_height) // 2  
        self.window = None
        self.batch = None
        self.status_message = "Welcome to Pao'er Ship!"
        
        # Store graphical elements
        self.grid_elements = []
        self.labels = []
        self.ship_elements = {}
        self.cursor = None
        
        # Colors (RGBA format for Pyglet)
        self.colors = {
            0: (50, 50, 50, 255),     # Empty - Dark Gray
            1: (0, 255, 0, 255),      # Ship - Green
            2: (255, 0, 0, 255),      # Hit - Red
            3: (0, 0, 255, 255),      # Miss - Blue
            'grid': (50, 50, 50, 255),  # Grid lines
            'text': (200, 200, 200, 255),  # Text color
            'cursor': (255, 255, 0, 255)   # Yellow cursor
        }

    def init_display(self):
        """Initialize the Pyglet display"""
        # Create main window
        self.window = pyglet.window.Window(
            width=self.width,
            height=self.height, 
            caption="Pao'er Ship",
            fullscreen=self.fullscreen
        )
        
        # Create a batch for efficient rendering
        self.batch = pyglet.graphics.Batch()
        
        # Set up event handlers
        @self.window.event
        def on_draw():
            self.window.clear()
            if self.batch:
                self.batch.draw()
        
        # Create LCD display for status messages
        self._create_lcd_display()
    
    def update(self, board_state, show_grid=True):
        """Update the display with the current board state"""
        if not self.window or not self.batch:
            return
            
        # Clear previous elements
        self.grid_elements = []
        self.ship_elements = {}
        
        # Recreate batch for rendering
        self.batch = pyglet.graphics.Batch()
        
        # Draw background
        background = shapes.Rectangle(
            0, 0, self.width, self.height, 
            color=(20, 20, 30, 255), 
            batch=self.batch
        )
        self.grid_elements.append(background)
        
        # Draw LCD display
        self._draw_lcd_display()
        
        # Draw grid coordinates
        self._draw_grid_coordinates()
        
        # Draw game grid
        self._draw_game_grid(board_state, show_grid)
        
        # Force a redraw
        self.window.dispatch_event('on_draw')

    def cleanup(self):
        """Clean up resources when shutting down"""
        if self.window:
            self.window.close()
    
    def _create_lcd_display(self):
        """Create the LCD display for status messages"""
        lcd_bg = shapes.Rectangle(
            self.width - 350, 50, 300, 100,
            color=(200, 200, 200, 255),
            batch=self.batch
        )
        lcd_border = shapes.Rectangle(
            self.width - 350, 50, 300, 100,
            color=(200, 200, 200, 255),
            batch=self.batch
        )
        lcd_outline = shapes.Line(
            self.width - 350, 50, 
            self.width - 50, 50, 
            color=(100, 100, 100, 255),
            batch=self.batch
        )
        self.grid_elements.extend([lcd_bg, lcd_border, lcd_outline])
        
        # Status message label
        self.status_label = pyglet.text.Label(
            self.status_message,
            font_name='Arial',
            font_size=24,
            x=self.width - 200,
            y=100,
            anchor_x='center',
            anchor_y='center',
            color=(0, 0, 0, 255),
            batch=self.batch
        )
        self.labels.append(self.status_label)
    
    def _draw_lcd_display(self):
        """Update the LCD display with the current status message"""
        if hasattr(self, 'status_label'):
            self.status_label.text = self.status_message
    
    def _draw_grid_coordinates(self):
        """Draw the coordinate labels for the grid"""
        for x in range(10):
            label = pyglet.text.Label(
                chr(65 + x),
                font_name='Arial',
                font_size=24,
                x=self.grid_offset_x + x * self.cell_size + 15,
                y=self.grid_offset_y - 30,
                color=(200, 200, 200, 255),
                batch=self.batch
            )
            self.labels.append(label)
        
        for y in range(10):
            label = pyglet.text.Label(
                str(y + 1),
                font_name='Arial',
                font_size=24,
                x=self.grid_offset_x - 30,
                y=self.grid_offset_y + y * self.cell_size + 10,
                color=(200, 200, 200, 255),
                batch=self.batch
            )
            self.labels.append(label)
    
    def _draw_game_grid(self, board_state, show_grid=True):
        """Draw the game grid with the current board state"""
        for y in range(len(board_state)):
            for x in range(len(board_state[0])):
                cell_value = board_state[y][x]
                color = self.colors.get(cell_value, (128, 128, 128, 255))
                
                cell_x = x * self.cell_size + self.grid_offset_x
                cell_y = y * self.cell_size + self.grid_offset_y
                
                # Draw cell shadow for 3D effect
                shadow = shapes.Rectangle(
                    cell_x + 3, cell_y + 3, 
                    self.cell_size - 2, self.cell_size - 2,
                    color=(30, 30, 30, 255),
                    batch=self.batch
                )
                
                # Draw the cell
                cell = shapes.Rectangle(
                    cell_x, cell_y, 
                    self.cell_size - 2, self.cell_size - 2,
                    color=color,
                    batch=self.batch
                )
                
                key = f"{y}_{x}"
                self.ship_elements[key] = [shadow, cell]
                
                # Draw grid lines if needed
                if show_grid:
                    # Draw simple outline
                    outline = shapes.Line(
                        cell_x, cell_y, 
                        cell_x + self.cell_size - 2, cell_y,
                        color=(50, 50, 50, 255),
                        batch=self.batch
                    )
                    self.ship_elements[key].append(outline)
    
    def _draw_cursor(self, x, y):
        """Draw the cursor at the specified grid position"""
        if self.cursor:
            # Remove old cursor from batch
            self.grid_elements.remove(self.cursor)
            
        # Create new cursor
        cursor_x = x * self.cell_size + self.grid_offset_x
        cursor_y = y * self.cell_size + self.grid_offset_y
        
        # Create cursor using rectangle outline
        self.cursor = shapes.Rectangle(
            cursor_x - 2, cursor_y - 2,
            self.cell_size + 2, self.cell_size + 2,
            color=self.colors['cursor'],
            batch=self.batch
        )
        
        self.grid_elements.append(self.cursor)
    
    def set_status(self, message):
        """Set the status message displayed on the LCD"""
        self.status_message = message
        if hasattr(self, 'status_label'):
            self.status_label.text = message