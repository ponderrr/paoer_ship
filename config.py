import pygame
import os

# Display Configuration
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FULLSCREEN = True

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
LIGHT_BLUE = (80, 170, 255)
LIGHT_GRAY = (180, 180, 180)
RED = (255, 0, 0)

# Background color options
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

# Default background color
selected_background_color = BACKGROUND_COLORS["Black"]

# Button dimensions
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
BUTTON_SPACING = 70
BUTTON_BORDER_RADIUS = 5

# Fonts
TITLE_FONT_SIZE = 50
BUTTON_FONT_SIZE = 30
INFO_FONT_SIZE = 24
SMALL_FONT_SIZE = 20

# Board settings
BOARD_SIZE = 10  
CELL_SIZE = 40
GRID_OFFSET = 50  

# Ship Configurations 
SHIP_TYPES = {
    "Carrier": 5,
    "Battleship": 4,
    "Cruiser": 3,
    "Submarine": 3,
    "Destroyer": 2,
}

# Game states
GAME_STATE_SETUP = "setup"
GAME_STATE_PLAYING = "playing"
GAME_STATE_GAME_OVER = "game_over"

# Player vs player settings
TURN_TIMER = 30.0  
TIMER_WARNING_THRESHOLD = 10.0  

# Base directory for the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Sound directories
SOUND_DIR = os.path.join(BASE_DIR, "src", "sounds")
BACKGROUND_MUSIC_DIR = os.path.join(SOUND_DIR, "background_music")
BACKGROUND_MUSIC_PATH = os.path.join(BACKGROUND_MUSIC_DIR, "background.mp3")
PAO_MUSIC_PATH = os.path.join(BACKGROUND_MUSIC_DIR, "pao.mp3")

# Image directories
IMAGE_DIR = os.path.join(BASE_DIR, "assets", "images")
PAO_IMAGE_PATH = os.path.join(IMAGE_DIR, "pao.png")

# Button pins
PIN_UP = 17      # Pin 11
PIN_DOWN = 27    # Pin 13
PIN_LEFT = 22    # Pin 15
PIN_RIGHT = 23   # Pin 16
PIN_FIRE = 24    # Pin 18
PIN_MODE = 25    # Pin 22
PIN_ROTATE = 26  # Pin 37

# Input mappings
INPUT_FIRE = "space"
INPUT_MOVE_UP = "w"
INPUT_MOVE_DOWN = "s"
INPUT_MOVE_LEFT = "a"
INPUT_MOVE_RIGHT = "d"

# AI Configuration
AI_DIFFICULTIES = ["Easy", "Medium", "Hard", "Pao"]
AI_THINKING_TIME = {
    "Easy": (0.5, 1.0),     
    "Medium": (1.0, 1.5),
    "Hard": (1.5, 2.0),
    "Pao": (2.0, 3.0)
}

# Default volumes
DEFAULT_MUSIC_VOLUME = 0.5
DEFAULT_SFX_VOLUME = 0.7

# Audio settings
AUDIO_SAMPLE_RATE = 44100
AUDIO_BUFFER_SIZE = 2048  