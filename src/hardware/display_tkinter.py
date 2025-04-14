import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
from .display_interface import DisplayInterface
from src.board.game_board import CellState

class DisplayTkinter(DisplayInterface):
    def __init__(self, width=800, height=600, screen_number=1):
        """
        Initialize the Tkinter display for secondary monitor
        
        Args:
            width (int): Width of the display
            height (int): Height of the display
            screen_number (int): Screen number (0 for primary, 1 for secondary)
        """
        self.width = width
        self.height = height
        self.screen_number = screen_number
        self.window = None
        self.canvas = None
        self.cell_size = min(width, height) // 17
        self.grid_offset_x = (width - (self.cell_size * 10)) // 2
        self.grid_offset_y = (height - (self.cell_size * 10)) // 2
        self.status_message = "Welcome to Pao'er Ship!"
        self.title_font = None
        self.label_font = None
        self.message_label = None
        
        # Colors
        self.EMPTY_COLOR = "#323232"  # Dark Gray
        self.SHIP_COLOR = "#00FF00"   # Green
        self.HIT_COLOR = "#FF0000"    # Red
        self.MISS_COLOR = "#0000FF"   # Blue
        self.GRID_COLOR = "#646464"   # Medium Gray
        self.BG_COLOR = "#141420"     # Dark Blue-Black

    def init_display(self):
        """Initialize the Tkinter window on the secondary display"""
        self.window = tk.Tk()
        self.window.title("Pao'er Ship - Secondary Display")
        
        # Position on secondary monitor
        if self.screen_number == 1:
            # Try to detect screen dimensions and position
            try:
                # Get screen information
                screen_info = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
                # Position window on second screen (assuming screens are side by side)
                self.window.geometry(f"{self.width}x{self.height}+{screen_info[0]}+0")
            except:
                # Fallback to a reasonable position
                self.window.geometry(f"{self.width}x{self.height}+1920+0")
        
        # Configure the window
        self.window.configure(bg=self.BG_COLOR)
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(
            self.window, 
            width=self.width, 
            height=self.height, 
            bg=self.BG_COLOR,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create fonts
        self.title_font = ("Arial", 24, "bold")
        self.label_font = ("Arial", 14)
        
        # Create status label
        self.message_label = tk.Label(
            self.window, 
            text=self.status_message,
            font=self.title_font,
            bg=self.BG_COLOR,
            fg="white"
        )
        self.message_label.place(relx=0.5, y=30, anchor="center")
        
        # Make sure Tkinter events are processed
        self.window.update()

    def update(self, board_state, show_grid=True):
        """
        Update the display with the current board state
        
        Args:
            board_state: 2D array representing the game board
            show_grid: Whether to show grid lines
        """
        if not self.window:
            return
            
        # Clear canvas
        self.canvas.delete("all")
        
        # Draw title
        self.message_label.config(text=self.status_message)
        
        # Draw grid coordinates
        self._draw_grid_coordinates()
        
        # Draw game grid
        self._draw_game_grid(board_state, show_grid)
        
        # Update Tkinter window
        self.window.update()
    
    def _draw_grid_coordinates(self):
        """Draw grid coordinate labels (A-J, 1-10)"""
        # Draw column labels (A-J)
        for x in range(10):
            self.canvas.create_text(
                self.grid_offset_x + x * self.cell_size + self.cell_size // 2,
                self.grid_offset_y - 20,
                text=chr(65 + x),
                fill="white",
                font=self.label_font
            )
        
        # Draw row labels (1-10)
        for y in range(10):
            self.canvas.create_text(
                self.grid_offset_x - 20,
                self.grid_offset_y + y * self.cell_size + self.cell_size // 2,
                text=str(y + 1),
                fill="white",
                font=self.label_font
            )
    
    def _draw_game_grid(self, board_state, show_grid=True):
        """
        Draw the game grid with current board state
        
        Args:
            board_state: 2D array representing the game board
            show_grid: Whether to show grid lines
        """
        for y in range(len(board_state)):
            for x in range(len(board_state[0])):
                color = self._get_cell_color(board_state[y][x])
                
                cell_x = x * self.cell_size + self.grid_offset_x
                cell_y = y * self.cell_size + self.grid_offset_y
                
                # Draw cell with rounded corners
                self.canvas.create_rectangle(
                    cell_x, cell_y,
                    cell_x + self.cell_size - 2,
                    cell_y + self.cell_size - 2,
                    fill=color,
                    outline=self.GRID_COLOR if show_grid else color,
                    width=1,
                    # Simulate rounded corners with small pixels cut off
                    stipple='gray75' if board_state[y][x] == CellState.EMPTY.value else ''
                )
                
                # Draw hit/miss markers
                if board_state[y][x] == CellState.HIT.value:
                    # Draw X for hit
                    self.canvas.create_line(
                        cell_x + 5, cell_y + 5,
                        cell_x + self.cell_size - 7, cell_y + self.cell_size - 7,
                        fill="white", width=2
                    )
                    self.canvas.create_line(
                        cell_x + self.cell_size - 7, cell_y + 5,
                        cell_x + 5, cell_y + self.cell_size - 7,
                        fill="white", width=2
                    )
                elif board_state[y][x] == CellState.MISS.value:
                    # Draw O for miss
                    self.canvas.create_oval(
                        cell_x + 5, cell_y + 5,
                        cell_x + self.cell_size - 7, cell_y + self.cell_size - 7,
                        outline="white", width=2
                    )
    
    def _get_cell_color(self, cell_value):
        """Convert cell value to color"""
        if cell_value == CellState.EMPTY.value:
            return self.EMPTY_COLOR
        elif cell_value == CellState.SHIP.value:
            return self.SHIP_COLOR
        elif cell_value == CellState.HIT.value:
            return self.HIT_COLOR
        elif cell_value == CellState.MISS.value:
            return self.MISS_COLOR
        else:
            return self.GRID_COLOR
    
    def set_status(self, message):
        """Set the status message"""
        self.status_message = message
        if self.message_label:
            self.message_label.config(text=message)
    
    def cleanup(self):
        """Clean up the Tkinter window"""
        if self.window:
            self.window.destroy()