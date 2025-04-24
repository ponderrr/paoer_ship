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
        # Game sounds
        self.sounds["fire"] = self._load_sound("fire.mp3")
        self.sounds["hit"] = self._load_sound("hit.mp3")
        self.sounds["miss"] = self._load_sound("miss.mp3")
        self.sounds["ship_sunk"] = self._load_sound("ship-sunk.mp3")
        
        # Menu navigation sounds - now with separate up/down
        self.sounds["navigate_up"] = self._load_sound("navigate_up.mp3")
        self.sounds["navigate_down"] = self._load_sound("navigate_down.mp3")
        self.sounds["accept"] = self._load_sound("accept.mp3")
        self.sounds["back"] = self._load_sound("back.mp3")
        
        self._load_background_music("background.mp3")
    except Exception as e:
        print(f"Warning: Could not load sounds: {e}")
    
    # Try fallbacks for menu sounds if not available
    if "navigate_up" not in self.sounds or self.sounds["navigate_up"] is None:
        # Try general navigate sound first
        if os.path.exists(os.path.join(self.sound_dir, "navigate.mp3")):
            self.sounds["navigate_up"] = self._load_sound("navigate.mp3")
            print("Using navigate sound as fallback for navigate_up")
        elif "fire" in self.sounds and self.sounds["fire"] is not None:
            self.sounds["navigate_up"] = self.sounds["fire"]
            print("Using fire sound as fallback for navigate_up")
    
    if "navigate_down" not in self.sounds or self.sounds["navigate_down"] is None:
        # Try general navigate sound first
        if os.path.exists(os.path.join(self.sound_dir, "navigate.mp3")):
            self.sounds["navigate_down"] = self._load_sound("navigate.mp3")
            print("Using navigate sound as fallback for navigate_down")
        elif "fire" in self.sounds and self.sounds["fire"] is not None:
            self.sounds["navigate_down"] = self.sounds["fire"]
            print("Using fire sound as fallback for navigate_down")
    
    if "accept" not in self.sounds or self.sounds["accept"] is None:
        if "hit" in self.sounds and self.sounds["hit"] is not None:
            self.sounds["accept"] = self.sounds["hit"]
            print("Using hit sound as fallback for accept")
    
    if "back" not in self.sounds or self.sounds["back"] is None:
        if "miss" in self.sounds and self.sounds["miss"] is not None:
            self.sounds["back"] = self.sounds["miss"]
            print("Using miss sound as fallback for back")
        
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