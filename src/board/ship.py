class Ship:
    def __init__(self, length, orientation, position):
        self.length = length
        self.orientation = orientation
        self.position = position  # (row, col)
        self.hits = [False] * length

    def draw(self, screen):
        """Draws the ship on the Pygame screen."""
        row, col = self.position
        for i in range(self.length):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            if self.orientation == "horizontal":
                x += i * CELL_SIZE
            else:
                y += i * CELL_SIZE

            pygame.draw.rect(screen, (100, 100, 255), (x, y, CELL_SIZE, CELL_SIZE))
