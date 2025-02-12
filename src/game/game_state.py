import pygame
from src.board.game_board import GameBoard
from src.hardware.display_mock import DisplayMock
from src.game.game_state import GameState

class GameController:
    def __init__(self):
        self.board = GameBoard()
        self.display = DisplayMock()
        self.state = GameState.SETUP
        self.current_player = 1  # Player 1 starts
        self.scores = {1: 0, 2: 0}  # Score tracking for two players
        self.winner = None
        
    def setup_game(self):
        """Initialize the game by placing ships and setting up the board."""
        self.display.init_display()
        self.board.place_ship(2, 3, 3, horizontal=True)
        self.board.place_ship(5, 5, 4, horizontal=False)
        self.state = GameState.PLAYING
    
    def switch_turn(self):
        """Switch the turn between players."""
        self.current_player = 1 if self.current_player == 2 else 2
    
    def process_turn(self, x, y):
        """Handle a player's move."""
        hit, _ = self.board.fire(x, y)
        if hit:
            self.scores[self.current_player] += 1
        
        if self.check_win():
            self.state = GameState.GAME_OVER
            self.winner = self.current_player
        else:
            self.switch_turn()
    
    def check_win(self):
        """Check if all ships have been sunk."""
        return (self.board.board == 2).sum() == len(self.board.ships)
    
    def run_game(self):
        """Main game loop."""
        self.setup_game()
        running = True
        clock = pygame.time.Clock()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and self.state == GameState.PLAYING:
                    x, y = pygame.mouse.get_pos()
                    grid_x = (x - 50) // 40
                    grid_y = (y - 50) // 40
                    if 0 <= grid_x < 10 and 0 <= grid_y < 10:
                        self.process_turn(grid_x, grid_y)
            
            self.display.update(self.board.get_display_state())
            clock.tick(60)
        
        self.display.cleanup()
        if self.state == GameState.GAME_OVER:
            print(f"Game Over! Player {self.winner} wins!")

if __name__ == "__main__":
    game = GameController()
    game.run_game()
