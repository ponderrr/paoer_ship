class GameCursor:
    def __init__(self, grid_size=10, cell_size=40):
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.x = 0
        self.y = 0
        
    def move(self, dx, dy):
        """
        Move cursor by grid coordinates, ensuring it stays within bounds
        """
        new_x = max(0, min(self.grid_size - 1, self.x + dx))
        new_y = max(0, min(self.grid_size - 1, self.y + dy))
        self.x = new_x
        self.y = new_y
    
    def get_grid_position(self):
        """
        Returns current grid coordinates (x, y)
        """
        return self.x, self.y