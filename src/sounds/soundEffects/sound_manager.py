import pygame

class SoundManager:
    def __init__(self):
        # Initialize Pygame mixer.
        pygame.mixer.init()

        # Existing sounds dictionary
        self.sounds = {
            "hit": pygame.mixer.Sound("src/sounds/soundEffects/hit.mp3"),
            "miss": pygame.mixer.Sound("assets/sounds/miss.wav"),
            "ship_sunk": pygame.mixer.Sound("assets/sounds/ship_sunk.wav"),
            "button_press": pygame.mixer.Sound("assets/sounds/button_press.wav"),
            "fire": pygame.mixer.Sound("assets/sounds/fire.wav")
        }

        # Background music
        pygame.mixer.music.load("src/sounds/soundEffects/background.mp3")

    def play_sound(self, sound_name):
        
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

    def start_background_music(self):
        
        pygame.mixer.music.play(-1)  # loop indefinitely

    def stop_background_music(self):
       
        pygame.mixer.music.stop()
