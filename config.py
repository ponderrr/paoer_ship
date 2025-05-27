"""
Pao'er Ship - Centralized Configuration
All game constants, settings, and configuration values
"""

import pygame
import os

# =============================================================================
# DISPLAY CONFIGURATION
# =============================================================================
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FULLSCREEN = True

# =============================================================================
# COLORS
# =============================================================================
# Primary Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
LIGHT_BLUE = (80, 170, 255)
LIGHT_GRAY = (180, 180, 180)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Game Colors
COLOR_EMPTY = (50, 50, 50)  # Empty board cells
COLOR_SHIP = (0, 255, 0)  # Ship placement (green)
COLOR_HIT = (255, 0, 0)  # Hit ship (red)
COLOR_MISS = (0, 0, 255)  # Missed shot (blue)
COLOR_GRID = (200, 200, 200)  # Grid lines
COLOR_CURSOR = (255, 255, 0)  # Cursor highlight
COLOR_INVALID = (255, 100, 100)  # Invalid placement

# Background Colors (selectable)
BACKGROUND_COLORS = {
    "Black": (0, 0, 0),
    "Navy": (0, 0, 128),
    "Gray": (128, 128, 128),
    "Red": (255, 0, 0),
    "Green": (0, 255, 0),
    "Blue": (0, 0, 255),
    "Yellow": (255, 255, 0),
    "Magenta": (255, 0, 255),
    "Cyan": (0, 255, 255),
    "Orange": (255, 165, 0),
    "Purple": (128, 0, 128),
    "Pink": (255, 192, 203),
}

# Default background color (can be changed at runtime)
selected_background_color = BACKGROUND_COLORS["Black"]

# =============================================================================
# UI CONFIGURATION
# =============================================================================
# Button Dimensions
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
BUTTON_SPACING = 70
BUTTON_BORDER_RADIUS = 5

# Font Sizes
TITLE_FONT_SIZE = 50
BUTTON_FONT_SIZE = 30
INFO_FONT_SIZE = 24
SMALL_FONT_SIZE = 20

# =============================================================================
# GAME BOARD CONFIGURATION
# =============================================================================
BOARD_SIZE = 10
CELL_SIZE = 40
GRID_OFFSET = 50

# Ship Types and Lengths
SHIP_TYPES = {
    "Carrier": 5,
    "Battleship": 4,
    "Cruiser": 3,
    "Submarine": 3,
    "Destroyer": 2,
}

# =============================================================================
# GAMEPLAY CONFIGURATION
# =============================================================================
# Game States
GAME_STATE_SETUP = "setup"
GAME_STATE_PLAYING = "playing"
GAME_STATE_GAME_OVER = "game_over"

# Player vs Player Settings
TURN_TIMER = 30.0  # seconds
TIMER_WARNING_THRESHOLD = 10.0  # seconds

# AI Configuration
AI_DIFFICULTIES = ["Easy", "Medium", "Hard", "Pao"]
AI_THINKING_TIME = {
    "Easy": (0.5, 1.0),  # min, max seconds
    "Medium": (1.0, 1.5),
    "Hard": (1.5, 2.0),
    "Pao": (2.0, 3.0),
}

# =============================================================================
# INPUT CONFIGURATION
# =============================================================================
# Keyboard Mappings
INPUT_FIRE = pygame.K_SPACE
INPUT_MODE = pygame.K_TAB
INPUT_ROTATE = pygame.K_r
INPUT_MOVE_UP = pygame.K_UP
INPUT_MOVE_DOWN = pygame.K_DOWN
INPUT_MOVE_LEFT = pygame.K_LEFT
INPUT_MOVE_RIGHT = pygame.K_RIGHT

# Button Delay (milliseconds)
BUTTON_MOVE_DELAY = 150
BUTTON_DEBOUNCE_TIME = 0.15

# =============================================================================
# HARDWARE CONFIGURATION (Raspberry Pi)
# =============================================================================
# GPIO Pin Assignments
PIN_UP = 17  # Physical Pin 11
PIN_DOWN = 27  # Physical Pin 13
PIN_LEFT = 22  # Physical Pin 15
PIN_RIGHT = 23  # Physical Pin 16
PIN_FIRE = 24  # Physical Pin 18
PIN_MODE = 25  # Physical Pin 22
PIN_ROTATE = 26  # Physical Pin 37

# =============================================================================
# AUDIO CONFIGURATION
# =============================================================================
# Audio Settings
AUDIO_SAMPLE_RATE = 44100
AUDIO_BUFFER_SIZE = 2048
AUDIO_BUFFER_SIZE_PI = 1024  # Smaller buffer for Raspberry Pi

# Default Volumes
DEFAULT_MUSIC_VOLUME = 0.5
DEFAULT_SFX_VOLUME = 0.7

# =============================================================================
# FILE PATHS
# =============================================================================
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

# =============================================================================
# DEVELOPMENT CONFIGURATION
# =============================================================================
# Debug Settings
DEBUG_MODE = False
SHOW_FPS = False
ENABLE_DEBUG_PRINTS = False

# Performance Settings
TARGET_FPS = 30
MAX_AI_THINKING_TIME = 5.0  # Fallback limit


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
def get_adaptive_cell_size(screen_width, screen_height):
    """Calculate cell size based on screen dimensions"""
    return int(min(screen_width, screen_height) * 0.03)


def get_board_offset(screen_width, screen_height, cell_size):
    """Calculate board centering offset"""
    board_width = cell_size * BOARD_SIZE
    board_height = cell_size * BOARD_SIZE
    offset_x = (screen_width - board_width) // 2
    offset_y = (screen_height - board_height) // 2
    return offset_x, offset_y


def get_font_size(screen_height, base_size):
    """Scale font size based on screen height"""
    return max(base_size, int(screen_height * (base_size / 1080)))


# =============================================================================
# VALIDATION
# =============================================================================
def validate_config():
    """Validate configuration values"""
    assert BOARD_SIZE > 0, "Board size must be positive"
    assert len(SHIP_TYPES) > 0, "Must have at least one ship type"
    assert TURN_TIMER > 0, "Turn timer must be positive"
    assert all(
        length > 0 for length in SHIP_TYPES.values()
    ), "Ship lengths must be positive"


# Run validation on import
validate_config()
