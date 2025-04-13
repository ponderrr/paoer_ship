import random
import time
import numpy as np
from enum import Enum
from src.board.game_board import GameBoard, CellState
from src.board.ship import Ship

class AIDifficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3
    PAO = 4

class Direction(Enum):
    NORTH = (-1, 0)
    EAST = (0, 1)
    SOUTH = (1, 0)
    WEST = (0, -1)

class AIOpponent:
    def __init__(self, difficulty=AIDifficulty.MEDIUM, player_board=None):
        """
        Initialize the AI opponent
        
        Args:
            difficulty (AIDifficulty): AI difficulty level
            player_board (GameBoard): Reference to player's board (for Pao mode)
        """
        self.difficulty = difficulty
        self.player_board = player_board
        self.board = GameBoard()
        self.shots = set()  # Tracks AI's shots
        self.hits = []  # List of successful hit coordinates
        self.current_target = None  # Current target for follow-up shots
        self.hunt_directions = []  # Directions to try after a hit
        self.last_hit_successful = False
        
        # For Medium/Hard difficulties - track hunting state
        self.hunting_mode = False
        self.hunt_start = None  # Starting point of current ship hunt
        self.hunt_direction = None  # Current direction being followed
        
        # For Hard difficulty - track probability map
        self.probability_map = np.zeros((10, 10))
        self.parity_mask = self.generate_parity_mask()
        
        # For Pao mode
        self.pao_mode = (difficulty == AIDifficulty.PAO)
        
        # Place ships according to difficulty
        self.place_ships()
        
        # Initialize probability map if using Hard difficulty
        if self.difficulty == AIDifficulty.HARD:
            self.initialize_probability_map()
    
    def generate_parity_mask(self):
        """Generate a parity mask for the checkerboard pattern targeting"""
        mask = np.zeros((10, 10))
        for i in range(10):
            for j in range(10):
                # Checkerboard pattern
                if (i + j) % 2 == 0:
                    mask[i, j] = 1
        return mask
    
    def place_ships(self):
        """Place ships on the AI's board based on difficulty level"""
        self.board.reset_board()
        
        # Get ship configurations from constants
        from src.utils.constants import SHIP_TYPES
        
        ship_types = list(SHIP_TYPES.items())
        
        if self.difficulty == AIDifficulty.EASY:
            # Random placement for Easy
            self._place_ships_randomly(ship_types)
        elif self.difficulty == AIDifficulty.MEDIUM:
            # Smarter placement for Medium (avoid edges)
            self._place_ships_smartly(ship_types)
        else:
            # Optimal placement for Hard and Pao
            self._place_ships_optimally(ship_types)
    
    def _place_ships_randomly(self, ship_types):
        """Completely random ship placement for Easy difficulty"""
        for ship_name, ship_length in ship_types:
            placed = False
            max_attempts = 100
            attempts = 0
            
            while not placed and attempts < max_attempts:
                x = random.randint(0, 9)
                y = random.randint(0, 9)
                horizontal = random.choice([True, False])
                
                placed = self.board.place_ship(x, y, ship_length, horizontal)
                attempts += 1
            
            if not placed:
                # If we failed after max attempts, try again with all ships
                self.board.reset_board()
                return self._place_ships_randomly(ship_types)
        
        return True
    
    def _place_ships_smartly(self, ship_types):
        """Smarter ship placement for Medium difficulty (avoid edges)"""
        for ship_name, ship_length in ship_types:
            placed = False
            max_attempts = 100
            attempts = 0
            
            while not placed and attempts < max_attempts:
                # Avoid placing ships at the edges for medium difficulty
                x = random.randint(1, 8)
                y = random.randint(1, 8)
                horizontal = random.choice([True, False])
                
                # For longer ships, adjust position to avoid going off board
                if horizontal and y + ship_length > 9:
                    y = 9 - ship_length
                if not horizontal and x + ship_length > 9:
                    x = 9 - ship_length
                
                placed = self.board.place_ship(x, y, ship_length, horizontal)
                attempts += 1
            
            if not placed:
                # If we failed after max attempts, try again with all ships
                self.board.reset_board()
                return self._place_ships_smartly(ship_types)
        
        return True
    
    def _place_ships_optimally(self, ship_types):
        """Optimal ship placement for Hard difficulty (dispersed throughout board)"""
        # Start with the largest ships
        sorted_ships = sorted(ship_types, key=lambda x: x[1], reverse=True)
        
        for ship_name, ship_length in sorted_ships:
            placed = False
            max_attempts = 100
            attempts = 0
            
            best_placement = None
            best_score = -1
            
            # Try multiple placements and choose the best one
            while attempts < max_attempts:
                x = random.randint(0, 9)
                y = random.randint(0, 9)
                horizontal = random.choice([True, False])
                
                # Check if placement is valid
                can_place = True
                if horizontal:
                    if y + ship_length > 10:
                        can_place = False
                    else:
                        for i in range(ship_length):
                            if y + i >= 10 or self.board.board[x, y + i] != CellState.EMPTY.value:
                                can_place = False
                                break
                else:
                    if x + ship_length > 10:
                        can_place = False
                    else:
                        for i in range(ship_length):
                            if x + i >= 10 or self.board.board[x + i, y] != CellState.EMPTY.value:
                                can_place = False
                                break
                
                if can_place:
                    # Calculate placement score (higher is better)
                    score = self._calculate_placement_score(x, y, ship_length, horizontal)
                    
                    if score > best_score:
                        best_score = score
                        best_placement = (x, y, horizontal)
                
                attempts += 1
            
            # Place the ship at the best location
            if best_placement:
                x, y, horizontal = best_placement
                placed = self.board.place_ship(x, y, ship_length, horizontal)
            
            if not placed:
                # If we failed after max attempts, try again with all ships
                self.board.reset_board()
                return self._place_ships_optimally(ship_types)
        
        return True
    
    def _calculate_placement_score(self, x, y, ship_length, horizontal):
        """
        Calculate a score for a potential ship placement.
        Higher scores represent better placements.
        """
        score = 0
        board_copy = self.board.board.copy()
        
        # Temporarily place the ship
        if horizontal:
            for i in range(ship_length):
                if y + i < 10:
                    board_copy[x, y + i] = CellState.SHIP.value
        else:
            for i in range(ship_length):
                if x + i < 10:
                    board_copy[x + i, y] = CellState.SHIP.value
        
        # Calculate distance to other ships
        min_distance = 10  # Initialize with max possible distance
        for i in range(10):
            for j in range(10):
                if board_copy[i, j] == CellState.SHIP.value:
                    for k in range(10):
                        for l in range(10):
                            if (i != k or j != l) and board_copy[k, l] == CellState.SHIP.value:
                                distance = abs(i - k) + abs(j - l)
                                min_distance = min(min_distance, distance)
        
        # Higher score for more distance between ships
        score += min_distance
        
        # Penalty for edge placement
        if horizontal:
            if x == 0 or x == 9:
                score -= 2
            for i in range(ship_length):
                if y + i == 0 or y + i == 9:
                    score -= 1
        else:
            if y == 0 or y == 9:
                score -= 2
            for i in range(ship_length):
                if x + i == 0 or x + i == 9:
                    score -= 1
        
        # Bonus for central placement
        center_x, center_y = 4.5, 4.5
        if horizontal:
            center_dist = abs(x - center_x) + abs(y + ship_length/2 - center_y)
        else:
            center_dist = abs(x + ship_length/2 - center_x) + abs(y - center_y)
        score -= center_dist * 0.5  # Small penalty for being far from center
        
        return score
    
    def initialize_probability_map(self):
        """Initialize the probability map for Hard difficulty targeting"""
        self.probability_map = np.ones((10, 10))
        # Apply parity mask (checkerboard pattern) for initial targeting
        self.probability_map = self.probability_map * self.parity_mask
    
    def update_probability_map(self, x, y, hit):
        """Update the probability map based on hit or miss"""
        if self.difficulty != AIDifficulty.HARD:
            return
            
        # Clear the shot position
        self.probability_map[x, y] = 0
        
        if hit:
            # Increase probability of surrounding cells
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                    self.probability_map[nx, ny] += 2
        else:
            # Decrease probability of surrounding cells
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                    self.probability_map[nx, ny] = max(0, self.probability_map[nx, ny] - 0.5)
    
    def get_shot(self):
        """
        Determine the AI's next shot coordinates based on difficulty level
        
        Returns:
            tuple: (x, y) coordinates to target
        """
        # Add a delay to simulate "thinking"
        if self.difficulty == AIDifficulty.EASY:
            time.sleep(random.uniform(0.5, 1.5))
        elif self.difficulty == AIDifficulty.MEDIUM:
            time.sleep(random.uniform(1.0, 2.0))
        elif self.difficulty == AIDifficulty.HARD:
            time.sleep(random.uniform(1.5, 3.0))
        else:  # PAO mode
            time.sleep(random.uniform(2.0, 3.0))
        
        # Pao mode - target known ship locations
        if self.pao_mode and self.player_board:
            return self._get_pao_shot()
        
        # Choose targeting strategy based on difficulty
        if self.difficulty == AIDifficulty.EASY:
            return self._get_easy_shot()
        elif self.difficulty == AIDifficulty.MEDIUM:
            return self._get_medium_shot()
        else:  # HARD
            return self._get_hard_shot()
    
def _get_easy_shot(self):
    """Random targeting with minimal follow-up for Easy difficulty"""
    # 70% random shots, 30% follow up on hits
    if self.hits and random.random() < 0.3:
        # Get the last hit position
        last_hit_x, last_hit_y = self.hits[-1]
        
        # Try adjacent positions randomly
        possible_shots = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = last_hit_x + dx, last_hit_y + dy
            if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                possible_shots.append((nx, ny))
        
        if possible_shots:
            return random.choice(possible_shots)
    
    # Create a list of all available positions that haven't been shot
    available_shots = []
    for x in range(10):
        for y in range(10):
            if (x, y) not in self.shots:
                available_shots.append((x, y))
    
    # Make sure there are still available shots
    if available_shots:
        return random.choice(available_shots)
    else:
        # Fallback - this should never happen in a normal game
        return (0, 0)

    
    def _get_medium_shot(self):
        """Smarter targeting with follow-up for Medium difficulty"""
        # If in hunting mode (following up on a hit)
        if self.hunting_mode and self.hits:
            # Get possible shots around the last hit
            last_hit_x, last_hit_y = self.hits[-1]
            
            # If we have a hunt direction, continue in that direction
            if self.hunt_direction:
                dx, dy = self.hunt_direction.value
                nx, ny = last_hit_x + dx, last_hit_y + dy
                
                # If the next position is valid and not already shot
                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                    return (nx, ny)
                else:
                    # Switch to the opposite direction from the original hit
                    if self.hunt_start:
                        opposite_directions = {
                            Direction.NORTH: Direction.SOUTH,
                            Direction.EAST: Direction.WEST,
                            Direction.SOUTH: Direction.NORTH,
                            Direction.WEST: Direction.EAST
                        }
                        self.hunt_direction = opposite_directions[self.hunt_direction]
                        dx, dy = self.hunt_direction.value
                        nx, ny = self.hunt_start[0] + dx, self.hunt_start[1] + dy
                        
                        if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                            return (nx, ny)
            
            # No valid direction, try adjacent positions
            possible_shots = []
            for direction in Direction:
                dx, dy = direction.value
                nx, ny = last_hit_x + dx, last_hit_y + dy
                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                    possible_shots.append((nx, ny, direction))
            
            if possible_shots:
                nx, ny, direction = random.choice(possible_shots)
                # Set the hunt direction if this is the first shot after a hit
                if not self.hunt_direction:
                    self.hunt_direction = direction
                    self.hunt_start = (last_hit_x, last_hit_y)
                return (nx, ny)
            
            # No valid adjacent shots, reset hunting mode
            self.hunting_mode = False
            self.hunt_direction = None
            self.hunt_start = None
        
        # Use a basic checkerboard pattern for 50% of shots
        if random.random() < 0.5:
            possible_shots = []
            for i in range(10):
                for j in range(10):
                    if (i + j) % 2 == 0 and (i, j) not in self.shots:
                        possible_shots.append((i, j))
            
            if possible_shots:
                return random.choice(possible_shots)
        
        # Random shot as fallback
        while True:
            x = random.randint(0, 9)
            y = random.randint(0, 9)
            if (x, y) not in self.shots:
                return (x, y)
    
    def _get_hard_shot(self):
        """
        Advanced targeting using probability map and hunt patterns for Hard difficulty
        """
        # If in hunting mode (following up on hits)
        if self.hunting_mode and self.hits:
            # Get the last hit
            last_hit_x, last_hit_y = self.hits[-1]
            
            # If we have a hunt direction, continue in that direction
            if self.hunt_direction:
                dx, dy = self.hunt_direction.value
                nx, ny = last_hit_x + dx, last_hit_y + dy
                
                # If the next position is valid and not already shot
                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                    return (nx, ny)
                else:
                    # If we've reached the end of a ship in this direction,
                    # switch to the opposite direction from the original hit
                    if self.hunt_start:
                        opposite_directions = {
                            Direction.NORTH: Direction.SOUTH,
                            Direction.EAST: Direction.WEST,
                            Direction.SOUTH: Direction.NORTH,
                            Direction.WEST: Direction.EAST
                        }
                        self.hunt_direction = opposite_directions[self.hunt_direction]
                        
                        # Start from the hunt_start and go in opposite direction
                        current_pos = self.hunt_start
                        while True:
                            dx, dy = self.hunt_direction.value
                            nx, ny = current_pos[0] + dx, current_pos[1] + dy
                            
                            if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                                return (nx, ny)
                            elif 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) in self.shots and (nx, ny) in self.hits:
                                # Continue past this hit in the same direction
                                current_pos = (nx, ny)
                            else:
                                break
            
            # No valid shots in current direction, try adjacent positions to last hit
            possible_shots = []
            for direction in Direction:
                dx, dy = direction.value
                nx, ny = last_hit_x + dx, last_hit_y + dy
                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                    possible_shots.append((nx, ny, direction))
            
            if possible_shots:
                # Choose the direction with the highest probability
                best_shot = None
                best_prob = -1
                
                for nx, ny, direction in possible_shots:
                    if self.probability_map[nx, ny] > best_prob:
                        best_prob = self.probability_map[nx, ny]
                        best_shot = (nx, ny, direction)
                
                nx, ny, direction = best_shot
                # Set the hunt direction if this is the first shot after a hit
                if not self.hunt_direction:
                    self.hunt_direction = direction
                    self.hunt_start = (last_hit_x, last_hit_y)
                return (nx, ny)
            
            # No valid adjacent shots, reset hunting mode
            self.hunting_mode = False
            self.hunt_direction = None
            self.hunt_start = None
        
        # Use probability map for targeting
        # Find the cell with the highest probability
        max_prob = 0
        best_shots = []
        
        for i in range(10):
            for j in range(10):
                if (i, j) not in self.shots and self.probability_map[i, j] > max_prob:
                    max_prob = self.probability_map[i, j]
                    best_shots = [(i, j)]
                elif (i, j) not in self.shots and self.probability_map[i, j] == max_prob:
                    best_shots.append((i, j))
        
        if best_shots:
            return random.choice(best_shots)
        
        # Fallback to random untargeted cell
        while True:
            x = random.randint(0, 9)
            y = random.randint(0, 9)
            if (x, y) not in self.shots:
                return (x, y)
    
    def _get_pao_shot(self):
        """Pao mode targeting - targets known ship locations"""
        if not self.player_board:
            # Fallback to random if no player_board reference
            while True:
                x = random.randint(0, 9)
                y = random.randint(0, 9)
                if (x, y) not in self.shots:
                    return (x, y)
        
        # Find an unsunk ship cell
        for x in range(10):
            for y in range(10):
                if (x, y) not in self.shots and self.player_board.board[x, y] == CellState.SHIP.value:
                    return (x, y)
        
        # If no ship cells found, take a random shot
        while True:
            x = random.randint(0, 9)
            y = random.randint(0, 9)
            if (x, y) not in self.shots:
                return (x, y)
    
    def process_shot_result(self, x, y, hit, ship_sunk=False):
        """
        Process the result of the AI's shot
        
        Args:
            x (int): Row coordinate of the shot
            y (int): Column coordinate of the shot
            hit (bool): Whether the shot hit a ship
            ship_sunk (bool): Whether a ship was sunk by this shot
        """
        # Record the shot
        self.shots.add((x, y))
        
        # Update hunting state based on hit result
        if hit:
            self.hits.append((x, y))
            self.last_hit_successful = True
            
            # Enter hunting mode if not in Pao mode and not already hunting
            if not self.pao_mode and not self.hunting_mode:
                self.hunting_mode = True
                self.hunt_direction = None
                self.hunt_start = (x, y)
            
            # If a ship was sunk, reset hunting mode for next ship
            if ship_sunk:
                self.hunting_mode = False
                self.hunt_direction = None
                self.hunt_start = None
        else:
            self.last_hit_successful = False
        
        # Update probability map for Hard difficulty
        self.update_probability_map(x, y, hit)