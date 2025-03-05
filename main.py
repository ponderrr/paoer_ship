import pygame
import sys
import time

# Try to import GPIO support
try:
    import gpiod
    IS_RASPBERRY_PI = True
except ImportError:
    IS_RASPBERRY_PI = False

# Initialize Pygame
pygame.init()

# Screen settings - smaller for better performance
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pao'er Ship")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
LIGHT_BLUE = (80, 170, 255)
LIGHT_GRAY = (180, 180, 180)

# Load fonts
pygame.font.init()
title_font = pygame.font.Font(None, 50)
button_font = pygame.font.Font(None, 30)

# GPIO Button Handler
class GPIOHandler:
    def __init__(self):
        self.chip = None
        self.lines = {}
        self.last_states = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'fire': False,
            'mode': False
        }
        
        # Define GPIO pins for buttons (BCM numbering)
        self.PIN_UP = 17    # Pin 11
        self.PIN_DOWN = 27  # Pin 13
        self.PIN_LEFT = 22  # Pin 15
        self.PIN_RIGHT = 23 # Pin 16
        self.PIN_FIRE = 24  # Pin 18
        self.PIN_MODE = 25  # Pin 22
        
        if IS_RASPBERRY_PI:
            self.setup()
    
    def setup(self):
        try:
            # Try to open the GPIO chip for Pi 5
            self.chip = gpiod.Chip("gpiochip4")
            
            # Pin to button name mapping
            pin_button_map = {
                self.PIN_UP: 'up',
                self.PIN_DOWN: 'down',
                self.PIN_LEFT: 'left',
                self.PIN_RIGHT: 'right',
                self.PIN_FIRE: 'fire',
                self.PIN_MODE: 'mode'
            }
            
            # Set up all the lines using the older API (which we know works)
            for pin, button_name in pin_button_map.items():
                line = self.chip.get_line(pin)
                line.request(consumer=f"paoer-ship-{button_name}", type=gpiod.LINE_REQ_DIR_IN)
                self.lines[pin] = line
                
        except Exception as e:
            print(f"Error setting up GPIO: {e}")
            if self.chip:
                self.chip.close()
                self.chip = None
    
    def cleanup(self):
        if self.chip:
            self.chip.close()
            self.chip = None
    
    def get_button_states(self):
        actions = {
            'up': False,
            'down': False, 
            'left': False,
            'right': False,
            'fire': False,
            'mode': False
        }
        
        if not IS_RASPBERRY_PI or not self.chip:
            return actions
        
        try:
            # Pin to button name mapping
            pin_button_map = {
                self.PIN_UP: 'up',
                self.PIN_DOWN: 'down',
                self.PIN_LEFT: 'left',
                self.PIN_RIGHT: 'right',
                self.PIN_FIRE: 'fire',
                self.PIN_MODE: 'mode'
            }
            
            for pin, button_name in pin_button_map.items():
                if pin not in self.lines:
                    continue
                
                # Read line value (active LOW with pull-up)
                line = self.lines[pin]
                # For buttons with pull-up resistors, 0 means pressed (active low)
                current_state = (line.get_value() == 0)
                
                # Only register a press when the state changes from released to pressed
                if current_state and not self.last_states[button_name]:
                    actions[button_name] = True
                
                # Update last state
                self.last_states[button_name] = current_state
                
        except Exception as e:
            print(f"Error reading GPIO: {e}")
        
        return actions

# Simple button class
class Button:
    def __init__(self, x, y, width, height, text, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.base_color = BLUE
        self.hover_color = LIGHT_BLUE
        self.current_color = self.base_color
        self.hovered = False
        self.selected = False

    def update(self):
        self.current_color = self.hover_color if (self.selected or self.hovered) else self.base_color

    def draw(self, screen):
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=5)
        text_surface = button_font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.action()

# Game states
def game_screen():
    """Simplified game screen"""
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    
    # Set up basic game layout
    board = [[0 for _ in range(10)] for _ in range(10)]
    board[2][3] = 1  # Place a "ship" at 2,3
    board[5][5] = 1  # Place another "ship" at 5,5
    
    cursor_x, cursor_y = 0, 0
    
    running = True
    while running:
        # Fill background
        screen.fill(BLACK)
        
        # Draw grid
        cell_size = 30
        grid_offset_x = 150
        grid_offset_y = 100
        
        # Draw column letters and row numbers
        for i in range(10):
            # Column labels (A-J)
            letter = chr(65 + i)
            text = font.render(letter, True, WHITE)
            screen.blit(text, (grid_offset_x + i * cell_size + 10, grid_offset_y - 30))
            
            # Row labels (1-10)
            number = str(i + 1)
            text = font.render(number, True, WHITE)
            screen.blit(text, (grid_offset_x - 30, grid_offset_y + i * cell_size + 10))
        
        # Draw grid cells
        for y in range(10):
            for x in range(10):
                cell_x = grid_offset_x + x * cell_size
                cell_y = grid_offset_y + y * cell_size
                
                # Determine cell color based on state
                if board[y][x] == 0:
                    color = (50, 50, 50)  # Empty cell
                elif board[y][x] == 1:
                    color = (0, 255, 0)   # Ship
                elif board[y][x] == 2:
                    color = (255, 0, 0)   # Hit
                else:
                    color = (0, 0, 255)   # Miss
                
                # Draw cell
                pygame.draw.rect(screen, color, (cell_x, cell_y, cell_size - 2, cell_size - 2))
        
        # Draw cursor
        cursor_rect = pygame.Rect(
            grid_offset_x + cursor_x * cell_size,
            grid_offset_y + cursor_y * cell_size,
            cell_size - 2,
            cell_size - 2
        )
        pygame.draw.rect(screen, (255, 255, 0), cursor_rect, 3)
        
        # Draw status
        status_text = font.render("Press 'Mode' button to return to menu", True, WHITE)
        screen.blit(status_text, (WIDTH // 2 - 200, HEIGHT - 50))
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP and cursor_y > 0:
                    cursor_y -= 1
                elif event.key == pygame.K_DOWN and cursor_y < 9:
                    cursor_y += 1
                elif event.key == pygame.K_LEFT and cursor_x > 0:
                    cursor_x -= 1
                elif event.key == pygame.K_RIGHT and cursor_x < 9:
                    cursor_x += 1
                elif event.key == pygame.K_SPACE:
                    # Fire at cell
                    if board[cursor_y][cursor_x] == 1:
                        board[cursor_y][cursor_x] = 2  # Hit
                    elif board[cursor_y][cursor_x] == 0:
                        board[cursor_y][cursor_x] = 3  # Miss
        
        # Check GPIO buttons
        button_states = gpio_handler.get_button_states()
        
        if button_states['up'] and cursor_y > 0:
            cursor_y -= 1
        if button_states['down'] and cursor_y < 9:
            cursor_y += 1
        if button_states['left'] and cursor_x > 0:
            cursor_x -= 1
        if button_states['right'] and cursor_x < 9:
            cursor_x += 1
        if button_states['fire']:
            # Fire at cell
            if board[cursor_y][cursor_x] == 1:
                board[cursor_y][cursor_x] = 2  # Hit
            elif board[cursor_y][cursor_x] == 0:
                board[cursor_y][cursor_x] = 3  # Miss
        if button_states['mode']:
            running = False
        
        # Update display
        pygame.display.flip()
        clock.tick(30)

def settings_screen():
    """Simplified settings screen"""
    screen.fill(BLACK)
    font = pygame.font.Font(None, 36)
    text = font.render("Settings Screen (Placeholder)", True, WHITE)
    screen.blit(text, (WIDTH//2 - 180, HEIGHT//2))
    
    back_text = font.render("Press any key to return to menu", True, WHITE)
    screen.blit(back_text, (WIDTH//2 - 180, HEIGHT//2 + 50))
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False
            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Check for GPIO button presses
        button_states = gpio_handler.get_button_states()
        if any(button_states.values()):
            waiting = False
        
        # Small delay to prevent CPU hogging
        time.sleep(0.01)

def main_menu():
    # Set up menu buttons
    button_width = 200
    button_height = 50
    center_x = (WIDTH - button_width) // 2
    start_y = 200
    spacing = 70

    buttons = [
        Button(center_x, start_y, button_width, button_height, "Start Game", game_screen),
        Button(center_x, start_y + spacing, button_width, button_height, "Settings", settings_screen),
        Button(center_x, start_y + spacing * 2, button_width, button_height, "Quit", quit_game)
    ]
    
    # Default selection
    current_selection = 0
    buttons[current_selection].selected = True

    clock = pygame.time.Clock()
    
    # Main menu loop
    running = True
    while running:
        # Fill background
        screen.fill(BLACK)
        
        # Draw title
        title_text = title_font.render("Pao'er Ship", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 100))
        screen.blit(title_text, title_rect)
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Mouse events
            elif event.type == pygame.MOUSEMOTION:
                for button in buttons:
                    button.check_hover(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    button.check_click(event.pos)
            
            # Keyboard navigation
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    # Clear selections
                    for button in buttons:
                        button.selected = False
                    # Move selection up
                    current_selection = (current_selection - 1) % len(buttons)
                    buttons[current_selection].selected = True
                
                elif event.key == pygame.K_DOWN:
                    # Clear selections
                    for button in buttons:
                        button.selected = False
                    # Move selection down
                    current_selection = (current_selection + 1) % len(buttons)
                    buttons[current_selection].selected = True
                
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # Activate selected button
                    buttons[current_selection].action()
                
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        # Check for GPIO button presses
        button_states = gpio_handler.get_button_states()
        
        if button_states['up']:
            # Clear selections
            for button in buttons:
                button.selected = False
            # Move selection up
            current_selection = (current_selection - 1) % len(buttons)
            buttons[current_selection].selected = True
        
        if button_states['down']:
            # Clear selections
            for button in buttons:
                button.selected = False
            # Move selection down
            current_selection = (current_selection + 1) % len(buttons)
            buttons[current_selection].selected = True
        
        if button_states['fire']:
            # Activate selected button
            buttons[current_selection].action()
        
        # Update and draw buttons
        for button in buttons:
            button.update()
            button.draw(screen)
        
        # Display controls help
        help_font = pygame.font.Font(None, 24)
        help_text = help_font.render("Up/Down: Navigate | Fire: Select | Mode: Back", True, LIGHT_GRAY)
        screen.blit(help_text, (WIDTH // 2 - 150, HEIGHT - 40))
        
        # Update display
        pygame.display.flip()
        
        # Limit framerate
        clock.tick(30)

def quit_game():
    gpio_handler.cleanup()
    pygame.quit()
    sys.exit()

# Initialize GPIO handler
gpio_handler = GPIOHandler()

def main():
    try:
        main_menu()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        gpio_handler.cleanup()
        pygame.quit()

if __name__ == "__main__":
    main()