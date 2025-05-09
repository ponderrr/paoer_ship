BOARD_SIZE = 10  

SHIP_TYPES = {
    "Carrier": 5,
    "Battleship": 4,
    "Cruiser": 3,
    "Submarine": 3,
    "Destroyer": 2,
}

COLOR_EMPTY = (50, 50, 50)      
COLOR_SHIP = (0, 255, 0)        # Green (Ship Placement)
COLOR_HIT = (255, 0, 0)         # Red (Hit Ship)
COLOR_MISS = (0, 0, 255)        # Blue (Missed Shot)
COLOR_GRID = (200, 200, 200)    # Light Gray (Grid Lines)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CELL_SIZE = 40
GRID_OFFSET = 50  

INPUT_FIRE = "space"
INPUT_MOVE_UP = "w"
INPUT_MOVE_DOWN = "s"
INPUT_MOVE_LEFT = "a"
INPUT_MOVE_RIGHT = "d"

GAME_STATE_SETUP = "setup"
GAME_STATE_PLAYING = "playing"
GAME_STATE_GAME_OVER = "game_over"

BACKGROUND_COLORS = {
    "Black": (0, 0, 0),
    "Navy": (0, 0, 128),
    "Gray": (128, 128, 128),
    "Red": (255, 0, 0),
    "Green": (0, 255, 0),
    "Blue": (0, 0, 255),
    "Yellow": (255, 255, 0),
    "Magenta": (255, 0, 255),
    "Cyan":    (0, 255, 255),
    "Orange":  (255, 165, 0),
    "Purple":  (128, 0, 128),
    "Pink":    (255, 192, 203),
}
