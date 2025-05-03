from src.board.game_board import GameBoard

class Player:
    def __init__(self, player_id):
        self.player_id = player_id
        self.board = GameBoard()
        self.shot_history = []  
        self.hits = 0  
        self.misses = 0  
    
    def place_ship(self, x, y, length, horizontal=True):
        """Places a ship on the player's board."""
        return self.board.place_ship(x, y, length, horizontal)
    
    def fire(self, x, y, opponent_board):
        """Fires at a given coordinate on the opponent's board."""
        hit, _ = opponent_board.fire(x, y)
        self.shot_history.append((x, y))
        if hit:
            self.hits += 1
        else:
            self.misses += 1
        return hit
    
    def get_shot_history(self):
        """Returns the list of shots fired by the player."""
        return self.shot_history
    
    def get_statistics(self):
        """Returns the player's game statistics."""
        total_shots = self.hits + self.misses
        accuracy = (self.hits / total_shots) * 100 if total_shots > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_shots": total_shots,
            "accuracy": accuracy
        }
