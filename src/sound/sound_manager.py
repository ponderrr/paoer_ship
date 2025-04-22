import pygame
import os

class SoundManager:
    """
    Handles game sound effects and music
    """
    def __init__(self, sound_dir="src/sounds"): 
        """
        Initialize the sound manager.
        
        Args:
            sound_dir (str): Directory containing sound files
        """
        # Initialize Pygame mixer
        pygame.mixer.init()
        
        # Store sound directory
        self.sound_dir = sound_dir
        
        # Initialize sounds dictionary
        self.sounds = {}
        
        # Try to load sounds
        try:
            self.sounds["fire"] = self._load_sound("fire.mp3")
            self.sounds["hit"] = self._load_sound("hit.mp3")
            self.sounds["miss"] = self._load_sound("miss.mp3")
            self.sounds["ship_sunk"] = self._load_sound("ship-sunk.mp3")  
            self._load_background_music("background.mp3")
        except Exception as e:
            print(f"Warning: Could not load sounds: {e}")
            
        # Set sound volumes
        for sound_name, sound in self.sounds.items():
            if sound:
                sound.set_volume(0.7)
                
        # Set music volume
        pygame.mixer.music.set_volume(0.5)
    
    def _load_sound(self, filename):
        """
        Load a sound file from the sounds directory
        
        Args:
            filename (str): Sound file name
            
        Returns:
            pygame.mixer.Sound or None: The loaded sound or None if error
        """
        path = os.path.join(self.sound_dir, filename)
        try:
            if os.path.exists(path):
                return pygame.mixer.Sound(path)
            else:
                print(f"Warning: Sound file not found: {path}")
        except Exception as e:
            print(f"Error loading sound {filename}: {e}")
        return None
    
    def _load_background_music(self, filename):
        """
        Load background music file
        
        Args:
            filename (str): Music file name
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        path = os.path.join(self.sound_dir, filename)
        try:
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                return True
            else:
                print(f"Warning: Music file not found: {path}")
        except Exception as e:
            print(f"Error loading music {filename}: {e}")
        return False
        
    def play_sound(self, sound_name):
        """
        Play a sound by name
        
        Args:
            sound_name (str): Name of the sound to play
        """
        if sound_name in self.sounds and self.sounds[sound_name]:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"Error playing sound {sound_name}: {e}")

    def start_background_music(self):
        """Start playing background music on loop"""
        try:
            pygame.mixer.music.play(-1)  # loop indefinitely
        except Exception as e:
            print(f"Error playing background music: {e}")

    def stop_background_music(self):
        """Stop background music"""
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            print(f"Error stopping background music: {e}")
            
    def pause_background_music(self):
        """Pause background music"""
        try:
            pygame.mixer.music.pause()
        except Exception as e:
            print(f"Error pausing background music: {e}")
            
    def unpause_background_music(self):
        """Unpause background music"""
        try:
            pygame.mixer.music.unpause()
        except Exception as e:
            print(f"Error unpausing background music: {e}")
            
    def set_volume(self, volume):
        """
        Set volume for all sounds
        
        Args:
            volume (float): Volume level (0.0 to 1.0)
        """
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(volume)
                
    def set_music_volume(self, volume):
        """
        Set volume for background music
        
        Args:
            volume (float): Volume level (0.0 to 1.0)
        """
        pygame.mixer.music.set_volume(volume)