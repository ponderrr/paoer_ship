import numpy as np
import random
from enum import Enum
from src.board.ship import Ship  # Import Ship class

class CellState(Enum):
    EMPTY = 0
    SHIP = 1
    HIT = 2
    MISS = 3

class GameBoard:
    def __init__(self, size=10):
        self.size = size
        self.board = np.zeros((size, size), dtype=int)
        self.ships = []  # Stores Ship objects
        self.pao_mode = False
        self.ai_targets = []

    def place_ship(self, x, y, length, horizontal=True):
        """
        Places a ship on the board and stores it in self.ships.
        
        Args:
            x (int): Row coordinate.
            y (int): Column coordinate.
            length (int): Length of the ship.
            horizontal (bool): True if ship is horizontal, False if vertical.
        
        Returns:
            bool: True if placement successful, False otherwise.
        """
        # Check board limits
        if horizontal and (y + length > self.size):
            return False
        if not horizontal and (x + length > self.size):
            return False

        # Check for overlap
        for i in range(length):
            if horizontal and self.board[x, y + i] != CellState.EMPTY.value:
                return False
            if not horizontal and self.board[x + i, y] != CellState.EMPTY.value:
                return False

        # Place ship on board
        for i in range(length):
            if horizontal:
                self.board[x, y + i] = CellState.SHIP.value
            else:
                self.board[x + i, y] = CellState.SHIP.value

        # Store Ship object
        orientation = "horizontal" if horizontal else "vertical"
        new_ship = Ship(length, orientation, (x, y))
        self.ships.append(new_ship)
        
        return True

    def fire(self, x, y):
        """
        Handles firing at a coordinate.
        
        Args:
            x (int): Row coordinate.
            y (int): Column coordinate.
        
        Returns:
            tuple: (bool hit, bool all_sunk)
        """
        if not (0 <= x < self.size and 0 <= y < self.size):
            return False, False

        for ship in self.ships:
            if ship.receive_hit(x, y):
                self.board[x, y] = CellState.HIT.value
                return True, self.check_all_sunk()

        self.board[x, y] = CellState.MISS.value
        return False, self.check_all_sunk()

    def check_all_sunk(self):
        """Checks if all ships on the board are sunk."""
        return all(ship.is_sunk() for ship in self.ships)

    def get_display_state(self):
        """Returns board state for display."""
        return self.board.copy()
