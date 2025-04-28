import pygame
import os
import math  # Import math module for sin function

class ImageDisplay:
    def __init__(self, screen):
        """
        Initialize image display utility
        
        Args:
            screen: Pygame screen surface
        """
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
    def display_pao_image(self, duration=5.0):
        """
        Display Professor Pao image
        
        Args:
            duration (float): Duration to display the image in seconds
        """
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up to the project root
        project_root = os.path.dirname(os.path.dirname(current_dir))
        # Path to the image file
        image_path = os.path.join(project_root, "assets", "images", "pao.png")
        
        try:
            # First, check if the image exists at the expected path
            if not os.path.exists(image_path):
                print(f"Pao image not found at: {image_path}")
                # Try alternative locations
                alt_paths = [
                    os.path.join(project_root, "images", "pao.png"),
                    os.path.join(project_root, "src", "assets", "images", "pao.png"),
                    os.path.join(project_root, "pao.png")
                ]
                
                for alt_path in alt_paths:
                    if os.path.exists(alt_path):
                        image_path = alt_path
                        print(f"Found pao image at: {alt_path}")
                        break
                else:
                    raise FileNotFoundError(f"Could not find pao.png in any expected location")
            
            # Load the image
            image = pygame.image.load(image_path)
            
            # Scale image to fit screen while maintaining aspect ratio
            img_width, img_height = image.get_size()
            ratio = min(self.width / img_width, self.height / img_height)
            new_size = (int(img_width * ratio * 0.8), int(img_height * ratio * 0.8))
            image = pygame.transform.scale(image, new_size)
            
            # Calculate position (centered)
            x = (self.width - new_size[0]) // 2
            y = (self.height - new_size[1]) // 2
            
            # Fill screen with dark background
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))  # Black with transparency
            self.screen.blit(overlay, (0, 0))
            
            # Draw text
            font = pygame.font.Font(None, 48)
            text = font.render("PAO MODE ACTIVATED!", True, (255, 0, 0))
            text_rect = text.get_rect(center=(self.width // 2, y - 40))
            
            # Add glowing/pulsating effect
            start_time = pygame.time.get_ticks()
            running = True
            
            while running and (pygame.time.get_ticks() - start_time) / 1000 < duration:
                # Fill screen with dark background
                overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 200))
                self.screen.blit(overlay, (0, 0))
                
                # Display image
                self.screen.blit(image, (x, y))
                
                # Pulsating effect for text
                passed_time = (pygame.time.get_ticks() - start_time) / 1000
                # Use math.sin instead of pygame.math.sin
                pulse = abs(math.sin(passed_time * 5))
                text_color = (255, int(pulse * 150), int(pulse * 150))
                
                text = font.render("PAO MODE ACTIVATED!", True, text_color)
                self.screen.blit(text, text_rect)
                
                # Draw "press any button to continue" text
                continue_font = pygame.font.Font(None, 30)
                continue_text = continue_font.render("Press any button to continue", True, (200, 200, 200))
                continue_rect = continue_text.get_rect(center=(self.width // 2, self.height - 40))
                self.screen.blit(continue_text, continue_rect)
                
                # Process events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                        # Allow skipping with any button press
                        if passed_time > 1.0:  # Prevent accidental skipping
                            running = False
                
                # Update display
                pygame.display.flip()
                pygame.time.delay(30)
            
        except Exception as e:
            print(f"Error displaying Pao image: {e}")
            import traceback
            traceback.print_exc()
            # Continue without displaying image