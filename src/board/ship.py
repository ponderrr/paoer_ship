class Ship:
    def __init__(self, length, orientation, position):
        """
        Initialize a ship with length, orientation, and position.
        
        Args:
            length (int): Length of the ship.
            orientation (str): "horizontal" or "vertical".
            position (tuple): (row, col) where the ship starts.
        """
        self.length = length
        self.orientation = orientation
        self.position = position  # (row, col)
        self.hits = [False] * length  # Tracks hits for each segment

    def is_sunk(self):
        """Returns True if all segments of the ship are hit, otherwise False."""
        return all(self.hits)

    def receive_hit(self, x, y):
        """
        Marks a segment of the ship as hit.

        Args:
            x (int): Row coordinate of the hit.
            y (int): Column coordinate of the hit.
        
        Returns:
            bool: True if the hit is valid (a part of the ship), False otherwise.
        """
        ship_x, ship_y = self.position

        for i in range(self.length):
            if self.orientation == "horizontal":
                if (ship_x, ship_y + i) == (x, y):
                    self.hits[i] = True
                    return True
            else:  # Vertical
                if (ship_x + i, ship_y) == (x, y):
                    self.hits[i] = True
                    return True
        
        return False
