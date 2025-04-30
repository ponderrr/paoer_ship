# Pao'er Ship

Pao'er Ship is a Battleship-style game designed for Raspberry Pi with hardware button controls. It features both single-player mode against AI opponents of varying difficulty levels and two-player mode for head-to-head gameplay.

![Pao'er Ship Game](https://via.placeholder.com/800x400?text=Pao%27er+Ship+Game)

## Features

- **Multiple Game Modes**:
  - Player vs AI (Easy, Medium, Hard difficulties)
  - Player vs Player
  - Special "Pao Mode" - an ultra-challenging AI opponent

- **Hardware Integration**:
  - Designed for Raspberry Pi (compatible with Pi 4 and Pi 5)
  - Support for GPIO button controls
  - Fallback to keyboard controls when running on non-Pi systems

- **Customizable Settings**:
  - Sound effects and background music
  - Adjustable volume controls
  - Changeable background colors

- **Interactive Ship Placement**:
  - Place ships manually with a guided interface
  - Rotate ships for strategic positioning

- **Polished UI Elements**:
  - Turn transition screens
  - Game state indicators
  - Player statistics

## Requirements

### Hardware
- Raspberry Pi (optimized for Raspberry Pi 4 and 5)
- GPIO button setup (optional)
- Display

### Software Dependencies
- Python 3.x
- Pygame
- gpiod (for Raspberry Pi GPIO support)
- NumPy

## Controls

### Keyboard Controls (for development/testing)
- Arrow keys: Navigate cursor/menus
- Space: Fire/Select
- Tab: Mode/Back
- R: Rotate ships during placement

### GPIO Button Controls
- Up, Down, Left, Right: Navigation
- Fire: Select/Shoot
- Mode: Back/Exit
- Rotate: Rotate ships during placement

## Game Modes

### vs AI
Play against the computer with three difficulty levels:
- **Easy**: Random targeting with minimal follow-up
- **Medium**: Smarter targeting with basic strategy
- **Hard**: Advanced targeting using probability calculations

### vs Player
Play against another person taking turns on the same device.

### Pao Mode
An extremely challenging mode where missing a shot results in immediate defeat!

## Project Structure

- `src/`: Main source code
  - `board/`: Game board and ship logic
  - `game/`: Game state and controller
  - `hardware/`: Hardware interfaces (GPIO, display)
  - `input/`: Input handling
  - `sound/`: Sound management
  - `ui/`: User interface components
  - `utils/`: Utility functions
