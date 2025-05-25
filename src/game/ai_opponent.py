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
        self.shots = set()
        self.hits = []
        self.current_target = None
        self.hunt_directions = []
        self.last_hit_successful = False

        # track hunting state
        self.hunting_mode = False
        self.hunt_start = None
        self.hunt_direction = None

        # track probability map
        self.probability_map = np.zeros((10, 10))
        self.parity_mask = self.generate_parity_mask()

        self.pao_mode = difficulty == AIDifficulty.PAO

        self.place_ships()

        if self.difficulty == AIDifficulty.HARD:
            self.initialize_probability_map()

    def generate_parity_mask(self):
        """Generate a parity mask for the checkerboard pattern targeting"""
        mask = np.zeros((10, 10))
        for i in range(10):
            for j in range(10):
                if (i + j) % 2 == 0:
                    mask[i, j] = 1
        return mask

    def place_ships(self):
        """Place ships on the AI's board based on difficulty level"""
        self.board.reset_board()

        from src.utils.constants import SHIP_TYPES

        ship_types = list(SHIP_TYPES.items())

        if self.difficulty == AIDifficulty.EASY:
            self._place_ships_randomly(ship_types)
        elif self.difficulty == AIDifficulty.MEDIUM:
            self._place_ships_smartly(ship_types)
        else:
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
                x = random.randint(1, 8)
                y = random.randint(1, 8)
                horizontal = random.choice([True, False])

                if horizontal and y + ship_length > 9:
                    y = 9 - ship_length
                if not horizontal and x + ship_length > 9:
                    x = 9 - ship_length

                placed = self.board.place_ship(x, y, ship_length, horizontal)
                attempts += 1

            if not placed:
                self.board.reset_board()
                return self._place_ships_smartly(ship_types)

        return True

    def _place_ships_optimally(self, ship_types):
        """Optimal ship placement for Hard difficulty (dispersed throughout board)"""
        sorted_ships = sorted(ship_types, key=lambda x: x[1], reverse=True)

        for ship_name, ship_length in sorted_ships:
            placed = False
            max_attempts = 100
            attempts = 0

            best_placement = None
            best_score = -1

            while attempts < max_attempts:
                x = random.randint(0, 9)
                y = random.randint(0, 9)
                horizontal = random.choice([True, False])

                can_place = True
                if horizontal:
                    if y + ship_length > 10:
                        can_place = False
                    else:
                        for i in range(ship_length):
                            if (
                                y + i >= 10
                                or self.board.board[x, y + i] != CellState.EMPTY.value
                            ):
                                can_place = False
                                break
                else:
                    if x + ship_length > 10:
                        can_place = False
                    else:
                        for i in range(ship_length):
                            if (
                                x + i >= 10
                                or self.board.board[x + i, y] != CellState.EMPTY.value
                            ):
                                can_place = False
                                break

                if can_place:
                    score = self._calculate_placement_score(
                        x, y, ship_length, horizontal
                    )

                    if score > best_score:
                        best_score = score
                        best_placement = (x, y, horizontal)

                attempts += 1

            if best_placement:
                x, y, horizontal = best_placement
                placed = self.board.place_ship(x, y, ship_length, horizontal)

            if not placed:
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

        if horizontal:
            for i in range(ship_length):
                if y + i < 10:
                    board_copy[x, y + i] = CellState.SHIP.value
        else:
            for i in range(ship_length):
                if x + i < 10:
                    board_copy[x + i, y] = CellState.SHIP.value

        min_distance = 10
        for i in range(10):
            for j in range(10):
                if board_copy[i, j] == CellState.SHIP.value:
                    for k in range(10):
                        for l in range(10):
                            if (i != k or j != l) and board_copy[
                                k, l
                            ] == CellState.SHIP.value:
                                distance = abs(i - k) + abs(j - l)
                                min_distance = min(min_distance, distance)

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
            center_dist = abs(x - center_x) + abs(y + ship_length / 2 - center_y)
        else:
            center_dist = abs(x + ship_length / 2 - center_x) + abs(y - center_y)
        score -= center_dist * 0.5

        return score

    def initialize_probability_map(self):
        """Initialize the probability map for Hard difficulty targeting"""
        self.probability_map = np.ones((10, 10))
        self.probability_map = self.probability_map * self.parity_mask

    def update_probability_map(self, x, y, hit):
        """Update the probability map based on hit or miss"""
        if self.difficulty != AIDifficulty.HARD:
            return

        self.probability_map[x, y] = 0

        if hit:
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                    self.probability_map[nx, ny] += 2
        else:
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                    self.probability_map[nx, ny] = max(
                        0, self.probability_map[nx, ny] - 0.5
                    )

    def get_shot(self):
        """
        Determine the AI's next shot coordinates based on difficulty level

        Returns:
            tuple: (x, y) coordinates to target
        """
        try:
            if self.difficulty == AIDifficulty.EASY:
                time.sleep(random.uniform(0.5, 1.5))
            elif self.difficulty == AIDifficulty.MEDIUM:
                time.sleep(random.uniform(1.0, 2.0))
            elif self.difficulty == AIDifficulty.HARD:
                time.sleep(random.uniform(1.5, 3.0))
            else:
                time.sleep(random.uniform(2.0, 3.0))

            if self.pao_mode and self.player_board:
                return self._get_pao_shot()

            if self.difficulty == AIDifficulty.EASY:
                return self._get_easy_shot()
            elif self.difficulty == AIDifficulty.MEDIUM:
                return self._get_medium_shot()
            elif self.difficulty == AIDifficulty.HARD:
                return self._get_hard_shot()
            else:
                return self._get_medium_shot()

        except Exception as e:
            print(f"Error in get_shot: {e}")
            import traceback

            traceback.print_exc()
            return self._get_fallback_shot()

    def _get_fallback_shot(self):
        """Fallback method when other shot methods fail"""
        print("Using fallback shot method")
        available_shots = [
            (i, j) for i in range(10) for j in range(10) if (i, j) not in self.shots
        ]
        if available_shots:
            return random.choice(available_shots)
        return (0, 0)

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
        for i in range(10):
            for j in range(10):
                if (i, j) not in self.shots:
                    available_shots.append((i, j))

        if available_shots:
            return random.choice(available_shots)
        else:
            return (0, 0)

    def _get_medium_shot(self):
        """Smarter targeting with follow-up for Medium difficulty"""
        # hunting mode (following up on a hit)
        if self.hunting_mode and self.hits:
            last_hit_x, last_hit_y = self.hits[-1]

            if self.hunt_direction:
                dx, dy = self.hunt_direction.value
                nx, ny = last_hit_x + dx, last_hit_y + dy

                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                    return (nx, ny)
                else:
                    if self.hunt_start:
                        opposite_directions = {
                            Direction.NORTH: Direction.SOUTH,
                            Direction.EAST: Direction.WEST,
                            Direction.SOUTH: Direction.NORTH,
                            Direction.WEST: Direction.EAST,
                        }
                        self.hunt_direction = opposite_directions[self.hunt_direction]
                        dx, dy = self.hunt_direction.value
                        nx, ny = self.hunt_start[0] + dx, self.hunt_start[1] + dy

                        if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                            return (nx, ny)

            possible_shots = []
            for direction in Direction:
                dx, dy = direction.value
                nx, ny = last_hit_x + dx, last_hit_y + dy
                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                    possible_shots.append((nx, ny, direction))

            if possible_shots:
                nx, ny, direction = random.choice(possible_shots)
                if not self.hunt_direction:
                    self.hunt_direction = direction
                    self.hunt_start = (last_hit_x, last_hit_y)
                return (nx, ny)

            self.hunting_mode = False
            self.hunt_direction = None
            self.hunt_start = None

        # checkerboard pattern for 50% of shots
        if random.random() < 0.5:
            possible_shots = []
            for i in range(10):
                for j in range(10):
                    if (i + j) % 2 == 0 and (i, j) not in self.shots:
                        possible_shots.append((i, j))

            if possible_shots:
                return random.choice(possible_shots)

        available_shots = []
        for i in range(10):
            for j in range(10):
                if (i, j) not in self.shots:
                    available_shots.append((i, j))

        if available_shots:
            return random.choice(available_shots)
        return (0, 0)

    def _get_hard_shot(self):
        """
        Advanced targeting using probability map and hunt patterns for Hard difficulty
        """
        # hunting mode (following up on hits)
        if self.hunting_mode and self.hits:
            last_hit_x, last_hit_y = self.hits[-1]

            if self.hunt_direction:
                dx, dy = self.hunt_direction.value
                nx, ny = last_hit_x + dx, last_hit_y + dy

                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                    return (nx, ny)
                else:
                    if self.hunt_start:
                        opposite_directions = {
                            Direction.NORTH: Direction.SOUTH,
                            Direction.EAST: Direction.WEST,
                            Direction.SOUTH: Direction.NORTH,
                            Direction.WEST: Direction.EAST,
                        }
                        self.hunt_direction = opposite_directions[self.hunt_direction]

                        current_pos = self.hunt_start
                        while True:
                            dx, dy = self.hunt_direction.value
                            nx, ny = current_pos[0] + dx, current_pos[1] + dy

                            if (
                                0 <= nx < 10
                                and 0 <= ny < 10
                                and (nx, ny) not in self.shots
                            ):
                                return (nx, ny)
                            elif (
                                0 <= nx < 10
                                and 0 <= ny < 10
                                and (nx, ny) in self.shots
                                and (nx, ny) in self.hits
                            ):
                                current_pos = (nx, ny)
                            else:
                                break

            possible_shots = []
            for direction in Direction:
                dx, dy = direction.value
                nx, ny = last_hit_x + dx, last_hit_y + dy
                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in self.shots:
                    possible_shots.append((nx, ny, direction))

            if possible_shots:
                best_shot = None
                best_prob = -1

                for nx, ny, direction in possible_shots:
                    if self.probability_map[nx, ny] > best_prob:
                        best_prob = self.probability_map[nx, ny]
                        best_shot = (nx, ny, direction)

                nx, ny, direction = best_shot
                if not self.hunt_direction:
                    self.hunt_direction = direction
                    self.hunt_start = (last_hit_x, last_hit_y)
                return (nx, ny)

            self.hunting_mode = False
            self.hunt_direction = None
            self.hunt_start = None

        max_prob = 0
        best_shots = []

        for i in range(10):
            for j in range(10):
                if (i, j) not in self.shots and self.probability_map[i, j] > max_prob:
                    max_prob = self.probability_map[i, j]
                    best_shots = [(i, j)]
                elif (i, j) not in self.shots and self.probability_map[
                    i, j
                ] == max_prob:
                    best_shots.append((i, j))

        if best_shots:
            return random.choice(best_shots)

        available_shots = []
        for i in range(10):
            for j in range(10):
                if (i, j) not in self.shots:
                    available_shots.append((i, j))

        if available_shots:
            return random.choice(available_shots)

        return (0, 0)

    def _get_pao_shot(self):
        """Pao mode targeting - targets known ship locations"""
        if not self.player_board:
            available_shots = []
            for i in range(10):
                for j in range(10):
                    if (i, j) not in self.shots:
                        available_shots.append((i, j))

            if available_shots:
                return random.choice(available_shots)
            return (0, 0)

        for x in range(10):
            for y in range(10):
                if (x, y) not in self.shots and self.player_board.board[
                    x, y
                ] == CellState.SHIP.value:
                    return (x, y)

        available_shots = []
        for i in range(10):
            for j in range(10):
                if (i, j) not in self.shots:
                    available_shots.append((i, j))

        if available_shots:
            return random.choice(available_shots)
        return (0, 0)  # Emergency fallback

    def process_shot_result(self, x, y, hit, ship_sunk=False):
        """
        Process the result of the AI's shot

        Args:
            x (int): Row coordinate of the shot
            y (int): Column coordinate of the shot
            hit (bool): Whether the shot hit a ship
            ship_sunk (bool): Whether a ship was sunk by this shot
        """
        self.shots.add((x, y))

        if hit:
            self.hits.append((x, y))
            self.last_hit_successful = True

            if not self.pao_mode and not self.hunting_mode:
                self.hunting_mode = True
                self.hunt_direction = None
                self.hunt_start = (x, y)

            if ship_sunk:
                self.hunting_mode = False
                self.hunt_direction = None
                self.hunt_start = None
        else:
            self.last_hit_successful = False

        self.update_probability_map(x, y, hit)
