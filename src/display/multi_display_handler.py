"""
Multi-display manager for handling dual-screen setup on Raspberry Pi
"""
import pyglet
import os
import platform
import subprocess

class MultiDisplayManager:
    """Class for handling multiple displays with Pyglet"""
    def __init__(self):
        self.displays = self._get_displays()
        self.num_displays = len(self.displays)
        self.is_rpi = self._is_raspberry_pi()
        
        # Windows for each display
        self.windows = []
        
        # Default settings
        self.width = 800
        self.height = 600
        self.fullscreen = False
    
    def _is_raspberry_pi(self):
        """Check if we're running on a Raspberry Pi"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                return 'Raspberry Pi' in model
        except:
            return False
    
    def _get_displays(self):
        """Get available displays using Pyglet 2.x API"""
        displays = []
        
        # Get the platform-specific display wrapper
        platform = pyglet.window.get_platform()
        
        # Get the default display
        default_display = platform.get_default_display()
        
        # Get all screens
        screens = default_display.get_screens()
        
        for screen in screens:
            displays.append({
                'screen': screen,
                'width': screen.width,
                'height': screen.height,
                'x': screen.x,
                'y': screen.y
            })
        
        # If no displays found, create a fallback
        if not displays:
            displays.append({
                'screen': None,
                'width': 800,
                'height': 600,
                'x': 0,
                'y': 0
            })
        
        return displays
    
    def detect_displays(self):
        """Detect available displays and update display information"""
        self.displays = self._get_displays()
        self.num_displays = len(self.displays)
        
        # Print display information
        print(f"Detected {self.num_displays} display(s):")
        for i, display in enumerate(self.displays):
            print(f"  Display {i+1}: {display['width']}x{display['height']} at ({display['x']}, {display['y']})")
        
        return self.displays
    
    def create_window(self, display_index=0, width=None, height=None, caption="Battleship Game", fullscreen=False):
        """
        Create a window on the specified display
        
        Args:
            display_index: Index of the display to use
            width: Window width (uses display width if None)
            height: Window height (uses display height if None)
            caption: Window caption
            fullscreen: Whether to use fullscreen mode
        
        Returns:
            pyglet.window.Window: The created window
        """
        # Make sure display_index is valid
        if display_index >= self.num_displays:
            display_index = 0
        
        # Get target display
        display = self.displays[display_index]
        
        # Set dimensions
        if width is None:
            width = display['width'] if fullscreen else 800
        if height is None:
            height = display['height'] if fullscreen else 600
        
        # Create window
        try:
            window = pyglet.window.Window(
                width=width,
                height=height,
                caption=caption,
                fullscreen=fullscreen,
                screen=display['screen']
            )
            
            # Store window
            if len(self.windows) <= display_index:
                self.windows.extend([None] * (display_index + 1 - len(self.windows)))
            self.windows[display_index] = window
            
            return window
        except Exception as e:
            print(f"Error creating window on display {display_index}: {str(e)}")
            
            # Fallback to default display
            if display_index != 0:
                print("Falling back to default display")
                return self.create_window(0, width, height, caption, fullscreen)
            
            # Last resort: create a window without specifying a screen
            print("Creating window without screen specification")
            window = pyglet.window.Window(
                width=width,
                height=height,
                caption=caption,
                fullscreen=fullscreen
            )
            self.windows = [window]
            return window
    
    def create_dual_display_windows(self, fullscreen=False):
        """
        Create windows for a dual-display setup
        
        Returns:
            tuple: (player1_window, player2_window)
        """
        # Do we have multiple displays?
        if self.num_displays < 2:
            print("WARNING: Only one display detected. Both windows will be on the same display.")
            
            # Create windows on the same display
            player1_window = self.create_window(0, 800, 600, "Player 1 - Battleship", fullscreen)
            
            # Create a second window (if possible)
            try:
                player2_window = pyglet.window.Window(
                    width=800,
                    height=600,
                    caption="Player 2 - Battleship"
                )
                self.windows.append(player2_window)
            except:
                print("ERROR: Cannot create second window. Two-player mode not possible.")
                player2_window = None
        else:
            # Create windows on separate displays
            player1_window = self.create_window(0, None, None, "Player 1 - Battleship", fullscreen)
            player2_window = self.create_window(1, None, None, "Player 2 - Battleship", fullscreen)
        
        return player1_window, player2_window
    
    def close_all_windows(self):
        """Close all windows"""
        for window in self.windows:
            if window:
                window.close()
        self.windows = []
    
    def get_window(self, display_index=0):
        """Get window for the specified display"""
        if 0 <= display_index < len(self.windows):
            return self.windows[display_index]
        return None
    
    def fix_rpi_display_issues(self):
        """
        Fix common display issues on Raspberry Pi
        
        Returns:
            bool: True if fixes were applied, False otherwise
        """
        if not self.is_rpi:
            return False
        
        # For Raspberry Pi: check for screen issues and try to fix them
        try:
            # Try to force HDMI output on both ports
            if self.num_displays < 2:
                print("Trying to enable both HDMI outputs...")
                
                # Force HDMI outputs using tvservice
                subprocess.run(["tvservice", "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Wait for displays to initialize
                import time
                time.sleep(2)
                
                # Re-detect displays
                self.detect_displays()
                
                return self.num_displays > 1
        except Exception as e:
            print(f"Error fixing Raspberry Pi display issues: {str(e)}")
        
        return False
    
    def get_optimal_configuration(self):
        """
        Get optimal display configuration
        
        Returns:
            dict: Configuration settings
        """
        config = {
            'dual_display': self.num_displays > 1,
            'main_width': self.displays[0]['width'],
            'main_height': self.displays[0]['height'],
            'secondary_width': self.displays[min(1, self.num_displays-1)]['width'],
            'secondary_height': self.displays[min(1, self.num_displays-1)]['height'],
            'fullscreen': True if self.is_rpi else False
        }
        
        # If screens are different sizes, adjust for consistency
        if config['dual_display']:
            min_width = min(config['main_width'], config['secondary_width'])
            min_height = min(config['main_height'], config['secondary_height'])
            
            # Reduce to 80% of the smaller display
            game_width = int(min_width * 0.8)
            game_height = int(min_height * 0.8)
            
            config['game_width'] = game_width
            config['game_height'] = game_height
        else:
            # Single display: use 80% of available space
            config['game_width'] = int(config['main_width'] * 0.8)
            config['game_height'] = int(config['main_height'] * 0.8)
        
        return config