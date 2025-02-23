import pygame
from src.board.game_board import GameBoard
from src.hardware.display_mock import DisplayMock
from src.game.game_state import GameState

class GameController:
    def __init__(self):
        self.board = GameBoard()
        self.display = DisplayMock()
        self.state = GameState.SETUP
        self.shots_fired = set()  # Track player shots
        self.winner = None
        
    def setup_game(self):
        """Initialize the game by placing ships and setting up the board."""
        self.display.init_display()
        
        # Mockup: Just place a couple of ships manually
        self.board.place_ship(2, 3, 3, horizontal=True)
        self.board.place_ship(5, 5, 4, horizontal=False)
        
        self.state = GameState.PLAYING
    
    def process_turn(self, x, y):
        """Mockup: Fire at a location, check for win."""
        if (x, y) in self.shots_fired:
            return  # Ignore repeated shots

        self.shots_fired.add((x, y))
        hit, _ = self.board.fire(x, y)

        if self.check_win():
            self.state = GameState.GAME_OVER
            self.winner = "Player"

    def check_win(self):
        """Check if all ships have been hit."""
        return (self.board.board == 2).sum() == len(self.board.ships)
    
    def run_game(self):
        """Main game loop for mockup."""
        self.setup_game()
        running = True
        clock = pygame.time.Clock()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and self.state == GameState.PLAYING:
                    x, y = pygame.mouse.get_pos()
                    grid_x = (x - 100) // 40
                    grid_y = (y - 100) // 40
                    if 0 <= grid_x < 10 and 0 <= grid_y < 10:
                        self.process_turn(grid_x, grid_y)
            
            self.display.update(self.board.get_display_state())
            clock.tick(60)
        
        self.display.cleanup()
        if self.state == GameState.GAME_OVER:
            print("Game Over! You Win!")  # Mockup: Always assume player wins

if __name__ == "__main__":
    game = GameController()
    game.run_game()
