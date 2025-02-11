# src/board/game_board.py

import numpy as np
from enum import Enum

class CellState(Enum):
    EMPTY = 0
    SHIP = 1
    HIT = 2
    MISS = 3

class GameBoard:
    def __init__(self, size=10):
        self.size = size
        self.board = np.zeros((size, size), dtype=int)
        self.ships = []

    def place_ship(self, x, y, length, horizontal=True):
        """
        Place a ship on the board
        Returns True if placement successful, False if invalid
        """
        if horizontal:
            if x + length > self.size:
                return False
            # Check if space is empty
            if np.any(self.board[y, x:x+length] != CellState.EMPTY.value):
                return False
            # Place ship
            self.board[y, x:x+length] = CellState.SHIP.value
        else:
            if y + length > self.size:
                return False
            if np.any(self.board[y:y+length, x] != CellState.EMPTY.value):
                return False
            self.board[y:y+length, x] = CellState.SHIP.value
        return True

    def fire(self, x, y):
        """
        Fire at a position on the board
        Returns: (hit, sunk)
        """
        if not (0 <= x < self.size and 0 <= y < self.size):
            return False, False

        if self.board[y, x] == CellState.SHIP.value:
            self.board[y, x] = CellState.HIT.value
            return True, False  # Hit, not sunk (sunk logic to be added)
        elif self.board[y, x] == CellState.EMPTY.value:
            self.board[y, x] = CellState.MISS.value
        
        return False, False

    def get_display_state(self):
        """
        Returns the current state of the board for display
        """
        return self.board.copy()