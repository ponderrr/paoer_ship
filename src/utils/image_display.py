import pygame
import os
import math


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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        image_path = os.path.join(project_root, "assets", "images", "pao.png")

        try:
            if not os.path.exists(image_path):
                print(f"Pao image not found at: {image_path}")
                alt_paths = [
                    os.path.join(project_root, "images", "pao.png"),
                    os.path.join(project_root, "src", "assets", "images", "pao.png"),
                    os.path.join(project_root, "pao.png"),
                ]

                for alt_path in alt_paths:
                    if os.path.exists(alt_path):
                        image_path = alt_path
                        print(f"Found pao image at: {alt_path}")
                        break
                else:
                    raise FileNotFoundError(
                        f"Could not find pao.png in any expected location"
                    )

            image = pygame.image.load(image_path)

            img_width, img_height = image.get_size()
            ratio = min(self.width / img_width, self.height / img_height)
            new_size = (int(img_width * ratio * 0.8), int(img_height * ratio * 0.8))
            image = pygame.transform.scale(image, new_size)

            x = (self.width - new_size[0]) // 2
            y = (self.height - new_size[1]) // 2

            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))

            font = pygame.font.Font(None, 48)
            text = font.render("PAO MODE ACTIVATED!", True, (255, 0, 0))
            text_rect = text.get_rect(center=(self.width // 2, y - 40))

            start_time = pygame.time.get_ticks()
            running = True

            while running and (pygame.time.get_ticks() - start_time) / 1000 < duration:
                overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 200))
                self.screen.blit(overlay, (0, 0))

                self.screen.blit(image, (x, y))

                passed_time = (pygame.time.get_ticks() - start_time) / 1000
                pulse = abs(math.sin(passed_time * 5))
                text_color = (255, int(pulse * 150), int(pulse * 150))

                text = font.render("PAO MODE ACTIVATED!", True, text_color)
                self.screen.blit(text, text_rect)

                continue_font = pygame.font.Font(None, 30)
                continue_text = continue_font.render(
                    "Press any button to continue", True, (200, 200, 200)
                )
                continue_rect = continue_text.get_rect(
                    center=(self.width // 2, self.height - 40)
                )
                self.screen.blit(continue_text, continue_rect)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif (
                        event.type == pygame.KEYDOWN
                        or event.type == pygame.MOUSEBUTTONDOWN
                    ):
                        if passed_time > 1.0:
                            running = False

                pygame.display.flip()
                pygame.time.delay(30)

        except Exception as e:
            print(f"Error displaying Pao image: {e}")
            import traceback

            traceback.print_exc()
