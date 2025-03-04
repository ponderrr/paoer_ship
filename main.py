import pygame
import sys
import random
import math
import os

from src.board.game_board import GameBoard
from src.hardware.display_mock import DisplayMock
from src.input.button_handler import ButtonHandler
from src.cursor import GameCursor

# Import GPIO implementation based on platform
try:
    import RPi.GPIO as GPIO
    from src.hardware.gpio_rpi import GPIORPI as GPIOImpl
    IS_RASPBERRY_PI = True
    print("Running on Raspberry Pi - using GPIO pins")
except (ImportError, RuntimeError):
    from src.hardware.gpio_mock import GPIOMock as GPIOImpl
    IS_RASPBERRY_PI = False
    print("Not running on Raspberry Pi - using keyboard input")

# Initialize Pygame
pygame.init()

# Screen settings for 1920x1080
WIDTH, HEIGHT = 1920, 1080
fullscreen_enabled = False  # Default to windowed mode
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pao'er Ship")

# Colors
WHITE = (255, 255, 255)
BLACK = (20, 20, 30)      # Darker background for a sleek look
BLUE = (50, 150, 255)     # Vibrant blue for a modern feel
LIGHT_BLUE = (80, 170, 255)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)

# Game settings
sound_on = True
difficulty = "Medium"
ai_animations = True
grid_enabled = True

# Load fonts
pygame.font.init()
title_font = pygame.font.Font(None, 70)
button_font = pygame.font.Font(None, 40)

# Initialize GPIO
gpio = GPIOImpl()
gpio.setup()

# --- Fade Transition Helpers (250ms duration) ---
def fade_out(screen, duration=250):
    """Fade out over the specified duration (ms)."""
    fade_surface = pygame.Surface((WIDTH, HEIGHT))
    fade_surface.fill(BLACK)
    start_time = pygame.time.get_ticks()
    clock = pygame.time.Clock()
    while True:
        elapsed = pygame.time.get_ticks() - start_time
        if elapsed >= duration:
            break
        alpha = int(255 * (elapsed / duration))
        fade_surface.set_alpha(alpha)
        draw_background()  # Redraw current background (if desired)
        screen.blit(fade_surface, (0, 0))
        pygame.display.update()
        clock.tick(60)
    fade_surface.set_alpha(255)
    screen.blit(fade_surface, (0, 0))
    pygame.display.update()

def fade_in(screen, duration=250):
    """Fade in over the specified duration (ms)."""
    fade_surface = pygame.Surface((WIDTH, HEIGHT))
    fade_surface.fill(BLACK)
    start_time = pygame.time.get_ticks()
    clock = pygame.time.Clock()
    while True:
        elapsed = pygame.time.get_ticks() - start_time
        if elapsed >= duration:
            break
        alpha = int(255 * (1 - elapsed / duration))
        fade_surface.set_alpha(alpha)
        draw_background()  # Redraw current background (if desired)
        screen.blit(fade_surface, (0, 0))
        pygame.display.update()
        clock.tick(60)
    fade_surface.set_alpha(0)
    screen.blit(fade_surface, (0, 0))
    pygame.display.update()

# --- Turn Transition Popup ---
def turn_transition(player):
    """Display a full-screen popup indicating the next player's turn and wait for input."""
    screen.fill(BLACK)
    message = f"Player {player}'s Turn\nPress any key to continue..."
    lines = message.splitlines()
    total_height = len(lines) * 50
    y_offset = (HEIGHT - total_height) // 2
    for line in lines:
        text_surface = title_font.render(line, True, WHITE)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, y_offset))
        screen.blit(text_surface, text_rect)
        y_offset += 50
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False
            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

# --- Particle System for Background ---
particles = []

def init_particles(n=50):
    global particles
    particles = []
    for i in range(n):
        particle = {
            'x': random.uniform(0, WIDTH),
            'y': random.uniform(0, HEIGHT),
            'size': random.uniform(1, 3),
            'speed': 0.4,  # Fixed slow speed for all particles
            'color': (200, 200, 255)  # A soft light blue
        }
        particles.append(particle)

def update_particles():
    global particles
    for p in particles:
        p['y'] += p['speed']
        if p['y'] > HEIGHT:
            p['y'] = 0
            p['x'] = random.uniform(0, WIDTH)

# --- Button Class with Animation and Marquee Effect ---
class Button:
    def __init__(self, x, y, width, height, text, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.base_color = BLUE
        self.hover_color = LIGHT_BLUE
        self.current_color = self.base_color
        self.hovered = False
        self.selected = False  # For hardware button navigation
        self.scale = 1.0
        self.animation_speed = 0.1  # For scaling effect
        self.text_scroll_offset = 0  # For marquee effect

    def update(self):
        # Scale based on hover/selection state
        target_scale = 1.1 if (self.hovered or self.selected) else 1.0
        self.scale += (target_scale - self.scale) * self.animation_speed

        # Use hover color if selected or hovered
        self.current_color = self.hover_color if (self.selected or self.hovered) else self.base_color

        # Check if the text is too wide for the scaled button.
        text_width, _ = button_font.size(self.text)
        scaled_button_width = int(self.rect.width * self.scale) - 10  # 10 pixels padding
        if text_width > scaled_button_width:
            self.text_scroll_offset += 1  # Adjust scroll speed as needed.
            max_offset = text_width - scaled_button_width + 20  # 20 pixels gap at end
            if self.text_scroll_offset > max_offset:
                self.text_scroll_offset = 0
        else:
            self.text_scroll_offset = 0

    def draw(self, screen):
        # Calculate scaled rectangle to keep the button centered.
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        scaled_rect = pygame.Rect(0, 0, scaled_width, scaled_height)
        scaled_rect.center = self.rect.center

        # Draw the button.
        pygame.draw.rect(screen, self.current_color, scaled_rect, border_radius=15)
        
        # Render the full text.
        text_surface = button_font.render(self.text, True, WHITE)
        text_width = text_surface.get_width()
        available_width = scaled_rect.width - 10  # 10 pixels padding

        if text_width > available_width:
            clip_rect = pygame.Rect(self.text_scroll_offset, 0, available_width, text_surface.get_height())
            if clip_rect.right > text_width:
                clip_rect.right = text_width
            clipped_surface = text_surface.subsurface(clip_rect)
            text_y = scaled_rect.centery - clipped_surface.get_height() // 2
            screen.blit(clipped_surface, (scaled_rect.x + 5, text_y))
        else:
            text_rect = text_surface.get_rect(center=scaled_rect.center)
            screen.blit(text_surface, text_rect)

    def check_hover(self, pos):
        if self.rect.collidepoint(pos):
            self.hovered = True
        else:
            self.hovered = False

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.action()

# --- Static Gradient Background with Slow-Moving Particles ---
def draw_background():
    gradient = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        factor = y / HEIGHT
        r = int(BLACK[0] + (BLUE[0] - BLACK[0]) * factor)
        g = int(BLACK[1] + (BLUE[1] - BLACK[1]) * factor)
        b = int(BLACK[2] + (BLUE[2] - BLACK[2]) * factor)
        pygame.draw.line(gradient, (r, g, b), (0, y), (WIDTH, y))
    screen.blit(gradient, (0, 0))
    update_particles()
    for p in particles:
        pygame.draw.circle(screen, p['color'], (int(p['x']), int(p['y'])), int(p['size']))

# --- Centralized Settings Dictionary (Board Theme Removed) ---
default_settings = {
    "sound": True,
    "difficulty": "Medium",
    "ai_animations": True,
    "grid": True,
    "fullscreen": False
}
settings = default_settings.copy()

# --- Settings Menu as a Dedicated Class (without Board Theme) ---
class SettingsMenu:
    def __init__(self, screen, button_handler):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.button_handler = button_handler
        self.current_selection = 0  # Currently selected button
        self.create_buttons()
        self.frame_count = 0  # For wave animation

    def create_buttons(self):
        """Creates all the buttons for the settings menu."""
        button_width = 400
        button_height = 100
        center_x = (WIDTH - button_width) // 2
        start_y = 350
        spacing = 120
        self.buttons = [
            Button(center_x, start_y, button_width, button_height, f"Sound: {'ON' if settings['sound'] else 'OFF'}", lambda: self.toggle("sound")),
            Button(center_x, start_y + spacing, button_width, button_height, f"Difficulty: {settings['difficulty']}", lambda: self.toggle("difficulty")),
            Button(center_x, start_y + 2 * spacing, button_width, button_height, f"AI Animations: {'ON' if settings['ai_animations'] else 'OFF'}", lambda: self.toggle("ai_animations")),
            Button(center_x, start_y + 3 * spacing, button_width, button_height, f"Grid Lines: {'ON' if settings['grid'] else 'OFF'}", lambda: self.toggle("grid")),
            Button(center_x, start_y + 4 * spacing, button_width, button_height, f"Fullscreen: {'ON' if settings['fullscreen'] else 'OFF'}", lambda: self.toggle_fullscreen()),
            Button(center_x, start_y + 5 * spacing, button_width, button_height, "Back", self.back)
        ]
        # Set first button as selected
        self.buttons[0].selected = True

    def toggle(self, key):
        """Toggle game settings like sound, difficulty, AI animations, etc."""
        if key == "difficulty":
            options = ["Easy", "Medium", "Hard", "Pao (Impossible)"]
            current = settings[key]
            idx = options.index(current)
            settings[key] = options[(idx + 1) % len(options)]
        else:
            settings[key] = not settings[key]
        self.update_buttons()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode and update the display settings."""
        settings["fullscreen"] = not settings["fullscreen"]
        global screen
        if settings["fullscreen"]:
            info = pygame.display.Info()
            screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.update_buttons()

    def update_buttons(self):
        """Update button labels to reflect current settings."""
        for button in self.buttons:
            if button.text.startswith("Sound:"):
                button.text = f"Sound: {'ON' if settings['sound'] else 'OFF'}"
            elif button.text.startswith("Difficulty:"):
                button.text = f"Difficulty: {settings['difficulty']}"
            elif button.text.startswith("AI Animations:"):
                button.text = f"AI Animations: {'ON' if settings['ai_animations'] else 'OFF'}"
            elif button.text.startswith("Grid Lines:"):
                button.text = f"Grid Lines: {'ON' if settings['grid'] else 'OFF'}"
            elif button.text.startswith("Fullscreen:"):
                button.text = f"Fullscreen: {'ON' if settings['fullscreen'] else 'OFF'}"

    def draw_wavy_settings_title(self):
        """Draws the 'Settings' title with a wavy animation effect."""
        title_text = "Settings"
        x = WIDTH // 2 - len(title_text) * 20  # Center the text
        wave_amplitude = 12  # Height of wave
        wave_speed = 0.05  # Controls wave animation speed

        for i, letter in enumerate(title_text):
            y_wave = math.sin(self.frame_count * wave_speed + i * 0.5) * wave_amplitude
            letter_surface = title_font.render(letter, True, WHITE)
            letter_rect = letter_surface.get_rect(midtop=(x + i * 40, 200 + y_wave))
            self.screen.blit(letter_surface, letter_rect)

    def back(self):
        """Exit the settings menu and return to main menu."""
        self.running = False

    def run(self):
        """Main loop for the settings menu."""
        self.running = True
        while self.running:
            draw_background()
            self.draw_wavy_settings_title()

            # Get keyboard/GPIO input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for button in self.buttons:
                        button.check_click(pygame.mouse.get_pos())
                elif event.type == pygame.MOUSEWHEEL:
                    pass  # Ignore scroll wheel input
            
            # Update button hover based on mouse position
            mouse_pos = pygame.mouse.get_pos()
            for i, button in enumerate(self.buttons):
                button.check_hover(mouse_pos)
            
            # Handle GPIO/keyboard button navigation
            actions = self.button_handler.update()
            
            if actions['menu_up']:
                # Clear all selections
                for button in self.buttons:
                    button.selected = False
                
                # Move selection up
                self.current_selection = (self.current_selection - 1) % len(self.buttons)
                self.buttons[self.current_selection].selected = True
                
            if actions['menu_down']:
                # Clear all selections
                for button in self.buttons:
                    button.selected = False
                
                # Move selection down
                self.current_selection = (self.current_selection + 1) % len(self.buttons)
                self.buttons[self.current_selection].selected = True
            
            if actions['menu_select']:
                # Activate the selected button
                self.buttons[self.current_selection].action()
            
            if actions['menu_back']:
                self.back()

            # Update and draw all buttons
            for button in self.buttons:
                button.update()
                button.draw(self.screen)

            pygame.display.flip()
            self.frame_count += 1  # Increase frame count for continuous animation
            self.clock.tick(60)

def settings_menu():
    fade_out(screen, duration=250)
    menu = SettingsMenu(screen, button_handler)
    menu.run()
    fade_in(screen, duration=250)
    main_menu()

def start_game():
    fade_out(screen, duration=250)
    game_loop()

def quit_game():
    # Clean up GPIO first
    gpio.cleanup()
    pygame.quit()
    sys.exit()

def draw_wavy_title(text, font, y_offset, frame_count):
    """Draws text with a wavy animation effect"""
    x = WIDTH // 2 - len(text) * 20  # Center the text
    wave_amplitude = 15  # Height of wave
    wave_speed = 0.05  # Controls wave animation speed

    for i, letter in enumerate(text):
        # Create a wave effect by offsetting each letter
        y_wave = math.sin(frame_count * wave_speed + i * 0.5) * wave_amplitude
        letter_surface = font.render(letter, True, WHITE)
        letter_rect = letter_surface.get_rect(midtop=(x + i * 40, y_offset + y_wave))
        screen.blit(letter_surface, letter_rect)

def main_menu():
    global screen  
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN if settings["fullscreen"] else 0)

    button_width = 400
    button_height = 100
    center_x = (WIDTH - button_width) // 2
    start_y = 500
    spacing = 150

    buttons = [
        Button(center_x, start_y, button_width, button_height, "Start Game", start_game),
        Button(center_x, start_y + spacing, button_width, button_height, "Settings", settings_menu),
        Button(center_x, start_y + 2 * spacing, button_width, button_height, "Quit", quit_game)
    ]
    
    # Set first button as selected
    current_selection = 0
    buttons[current_selection].selected = True

    clock = pygame.time.Clock()
    frame_count = 0  # Track animation frames

    # Initialize button handler with GPIO
    button_handler = ButtonHandler(gpio)

    while True:
        draw_background()
        
        # Draw the animated wavy title
        draw_wavy_title("Pao'er Ship", title_font, 150, frame_count)
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    button.check_click(pygame.mouse.get_pos())
        
        # Update button hover based on mouse position
        mouse_pos = pygame.mouse.get_pos()
        for button in buttons:
            button.check_hover(mouse_pos)
            
        # Handle GPIO/keyboard button navigation
        actions = button_handler.update()
        
        if actions['menu_up']:
            # Clear all selections
            for button in buttons:
                button.selected = False
            
            # Move selection up
            current_selection = (current_selection - 1) % len(buttons)
            buttons[current_selection].selected = True
            
        if actions['menu_down']:
            # Clear all selections
            for button in buttons:
                button.selected = False
            
            # Move selection down
            current_selection = (current_selection + 1) % len(buttons)
            buttons[current_selection].selected = True
        
        if actions['menu_select']:
            # Activate the selected button
            buttons[current_selection].action()