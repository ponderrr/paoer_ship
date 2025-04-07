import pygame
import os
from src.board.game_board import CellState

class DualDisplayHandler:
    """
    Handler for managing both the main display and portable display
    for the Player vs Player mode of the game.
    """
    def __init__(self, main_screen, portable_screen=None):
        """
        Initialize the dual display handler
        
        Args:
            main_screen: Pygame surface for the main display
            portable_screen: Pygame surface for the portable display (optional)
        """
        self.main_screen = main_screen
        self.portable_screen = portable_screen
        
        # Get dimensions of screens
        self.main_width = main_screen.get_width()
        self.main_height = main_screen.get_height()
        
        # If portable screen is available, get its dimensions
        if portable_screen:
            self.portable_width = portable_screen.get_width()
            self.portable_height = portable_screen.get_height()
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BLUE = (50, 150, 255)
        self.DARK_BLUE = (0, 0, 255)  # For misses
        self.LIGHT_BLUE = (80, 170, 255)
        self.LIGHT_GRAY = (180, 180, 180)
        self.GREEN = (0, 255, 0)  # For ships
        self.RED = (255, 0, 0)    # For hits
        self.YELLOW = (255, 255, 0)  # For cursor
        
        # Fonts
        self.title_font = pygame.font.Font(None, 36)
        self.info_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
    
    def clear_portable_screen(self):
        """Clear the portable screen with a black background"""
        if self.portable_screen:
            self.portable_screen.fill(self.BLACK)
    
    def draw_board_on_portable(self, board_state, shots=None, hits=None, title="Your Ships"):
        """
        Draw a game board on the portable display
        
        Args:
            board_state: The game board state to draw
            shots: Set of coordinates that have been fired at
            hits: Set of coordinates that were hits
            title: Title to display above the board
        """
        if not self.portable_screen:
            return
            
        # Clear the screen
        self.portable_screen.fill(self.BLACK)
        
        # Calculate cell size based on screen dimensions
        cell_size = min(30, (min(self.portable_width, self.portable_height) - 120) // 10)
        
        # Calculate grid offset to center the board
        grid_offset_x = (self.portable_width - (cell_size * 10)) // 2
        grid_offset_y = (self.portable_height - (cell_size * 10)) // 2 + 20  # Add space for title
        
        # Draw title
        title_text = self.title_font.render(title, True, self.WHITE)
        title_rect = title_text.get_rect(center=(self.portable_width // 2, grid_offset_y - 30))
        self.portable_screen.blit(title_text, title_rect)
        
        # Draw column labels (A-J)
        for i in range(10):
            letter = chr(65 + i)
            label = self.small_font.render(letter, True, self.WHITE)
            self.portable_screen.blit(label, (grid_offset_x + i * cell_size + cell_size // 3, grid_offset_y - 20))
        
        # Draw row labels (1-10)
        for i in range(10):
            label = self.small_font.render(str(i + 1), True, self.WHITE)
            self.portable_screen.blit(label, (grid_offset_x - 20, grid_offset_y + i * cell_size + cell_size // 3))
        
        # Initialize shots and hits sets if not provided
        if shots is None:
            shots = set()
        if hits is None:
            hits = set()
        
        # Draw grid cells
        for y in range(10):
            for x in range(10):
                cell_rect = pygame.Rect(
                    grid_offset_x + x * cell_size,
                    grid_offset_y + y * cell_size,
                    cell_size - 2,
                    cell_size - 2
                )
                
                # Determine cell color based on state
                if (x, y) in hits:
                    color = self.RED  # Hit
                elif (x, y) in shots:
                    color = self.DARK_BLUE  # Miss
                elif board_state[x][y] == CellState.SHIP.value:
                    color = self.GREEN  # Ship
                else:
                    color = (50, 50, 50)  # Empty cell
                
                # Draw cell
                pygame.draw.rect(self.portable_screen, color, cell_rect)
                pygame.draw.rect(self.portable_screen, (100, 100, 100), cell_rect, 1)
        
        # Draw instruction at bottom
        instruction = self.info_font.render("Press ROTATE button to continue", True, self.LIGHT_GRAY)
        instruction_rect = instruction.get_rect(center=(self.portable_width // 2, self.portable_height - 30))
        self.portable_screen.blit(instruction, instruction_rect)
        
        # Update display
        pygame.display.flip()
    
    def draw_waiting_screen(self, player_number):
        """
        Draw a waiting screen on the portable display
        
        Args:
            player_number: The next player's number
        """
        if not self.portable_screen:
            return
            
        # Clear the screen
        self.portable_screen.fill(self.BLACK)
        
        # Draw title
        title_text = self.title_font.render(f"Player {player_number}'s Turn", True, self.WHITE)
        title_rect = title_text.get_rect(center=(self.portable_width // 2, self.portable_height // 3))
        self.portable_screen.blit(title_text, title_rect)
        
        # Draw instruction
        instruction = self.info_font.render("Press ROTATE button to view your ships", True, self.LIGHT_BLUE)
        instruction_rect = instruction.get_rect(center=(self.portable_width // 2, self.portable_height // 2))
        self.portable_screen.blit(instruction, instruction_rect)
        
        # Draw privacy notice
        privacy = self.info_font.render("Make sure the other player isn't looking", True, self.LIGHT_GRAY)
        privacy_rect = privacy.get_rect(center=(self.portable_width // 2, self.portable_height // 2 + 40))
        self.portable_screen.blit(privacy, privacy_rect)
        
        # Update display
        pygame.display.flip()