import pygame
import os
import random

class SoundManager:
    """
    Handles game sound effects and music with playlist support
    """
    def __init__(self, sound_dir="src/sounds"):
        """
        Initialize the sound manager.

        Args:
            sound_dir (str): Directory containing sound files
        """
        # Initialize Pygame mixer with specific settings
        try:
            pygame.mixer.pre_init(44100, -16, 2, 2048)  # Set audio parameters
            pygame.mixer.init()
            print("Pygame mixer initialized successfully")
        except Exception as e:
            print(f"Error initializing pygame mixer: {e}")

        # Store sound directory
        self.sound_dir = sound_dir
        self.background_music_dir = os.path.join(self.sound_dir, "background_music")

        # Initialize sounds dictionary
        self.sounds = {}

        # Initialize playlist
        self.playlist = []
        self.current_track_index = 0
        self.is_playing = False
        self.shuffle_mode = False
        self.repeat_mode = False 

        # Special music modes
        self.pao_mode = False
        self.pao_music_path = None

        # Set up music end event
        self.MUSIC_END_EVENT = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.MUSIC_END_EVENT)

        # Try to load sounds
        try:
            # Game sounds
            self.sounds["fire"] = self._load_sound("fire.mp3")
            self.sounds["hit"] = self._load_sound("hit.mp3")
            self.sounds["miss"] = self._load_sound("miss.mp3")
            self.sounds["ship_sunk"] = self._load_sound("ship-sunk.mp3")

            # Menu navigation sounds
            self.sounds["navigate_up"] = self._load_sound("navigate_up.mp3")
            self.sounds["navigate_down"] = self._load_sound("navigate_down.mp3")
            self.sounds["accept"] = self._load_sound("accept.mp3")
            self.sounds["back"] = self._load_sound("back.mp3")

            # Load background music playlist
            self._load_music_playlist()

        except Exception as e:
            print(f"Warning: Could not load sounds: {e}")

        # Try fallbacks for menu sounds if not available
        self._setup_fallback_sounds()

        # Set sound volumes
        for sound_name, sound in self.sounds.items():
            if sound:
                sound.set_volume(0.7)

        # Set music volume
        pygame.mixer.music.set_volume(0.5)

        # Check if mixer is working
        if pygame.mixer.get_init():
            print(f"Mixer initialized with: {pygame.mixer.get_init()}")
        else:
            print("ERROR: Mixer not initialized!")

    def _load_sound(self, filename):
        """
        Load a sound file from the sounds directory
        """
        path = os.path.join(self.sound_dir, filename)
        try:
            if os.path.exists(path):
                sound = pygame.mixer.Sound(path)
                print(f"Successfully loaded sound: {filename}")
                return sound
            else:
                print(f"Warning: Sound file not found: {path}")
        except Exception as e:
            print(f"Error loading sound {filename}: {e}")
        return None

    def _setup_fallback_sounds(self):
        """Setup fallback sounds for navigation"""
        if "navigate_up" not in self.sounds or self.sounds["navigate_up"] is None:
            if os.path.exists(os.path.join(self.sound_dir, "navigate.mp3")):
                self.sounds["navigate_up"] = self._load_sound("navigate.mp3")
                print("Using navigate sound as fallback for navigate_up")
            elif "fire" in self.sounds and self.sounds["fire"] is not None:
                self.sounds["navigate_up"] = self.sounds["fire"]
                print("Using fire sound as fallback for navigate_up")

        if "navigate_down" not in self.sounds or self.sounds["navigate_down"] is None:
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

    def _load_music_playlist(self):
        """
        Load all music files from the background music directory into a playlist
        """
        print(f"Looking for music files in: {self.background_music_dir}")

        # Look for music files in the background music directory
        music_extensions = ['.mp3', '.ogg', '.wav']

        # First, check for background.mp3 in the main sounds directory
        background_file = os.path.join(self.sound_dir, "background.mp3")
        if os.path.exists(background_file):
            self.playlist.append(background_file)
            print(f"Added main background music: {background_file}")

        # Add all music files from background music directory
        if os.path.exists(self.background_music_dir):
            files = os.listdir(self.background_music_dir)
            print(f"Files found in directory: {files}")

            for file in files:
                if any(file.lower().endswith(ext) for ext in music_extensions):
                    full_path = os.path.join(self.background_music_dir, file)
                    self.playlist.append(full_path)
                    print(f"Added to playlist: {file}")

                    # Check for special Pao mode music
                    if 'pao' in file.lower() or 'special' in file.lower():
                        self.pao_music_path = full_path
                        print(f"Found special Pao mode music: {file}")
        else:
            print(f"Background music directory does not exist: {self.background_music_dir}")

        # If no special Pao music was found, use the first track or a fallback
        if not self.pao_music_path and self.playlist:
            self.pao_music_path = self.playlist[0]
            print("Using first track as Pao mode music")

        print(f"Total music files loaded: {len(self.playlist)}")

    def play_sound(self, sound_name):
        """
        Play a sound by name
        """
        if sound_name in self.sounds and self.sounds[sound_name]:
            try:
                self.sounds[sound_name].play()
                print(f"Playing sound: {sound_name}")
            except Exception as e:
                print(f"Error playing sound {sound_name}: {e}")
                # Try to reinitialize mixer if sound fails
                try:
                    pygame.mixer.quit()
                    pygame.mixer.init()
                    print("Reinitialized mixer after sound failure")
                except:
                    pass

    def start_background_music(self):
        """Start playing background music playlist"""
        if not self.playlist:
            print("No music files found in playlist")
            return

        print("Starting background music...")
        self.is_playing = True
        self.pao_mode = False
        self.play_next_track()

    def toggle_shuffle(self):
        """Toggle shuffle mode for the playlist"""
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode and self.playlist:
            # Shuffle the playlist
            random.shuffle(self.playlist)
        elif not self.shuffle_mode and self.playlist:
            # Sort the playlist back to original order (by filename)
            self.playlist.sort()
        print(f"Shuffle mode: {'ON' if self.shuffle_mode else 'OFF'}")
        return self.shuffle_mode
    
    def toggle_repeat(self):
        """Toggle repeat mode for the playlist"""
        self.repeat_mode = not self.repeat_mode
        print(f"Repeat mode: {'ON' if self.repeat_mode else 'OFF'}")
        return self.repeat_mode
    
    def get_shuffle_state(self):
        """Get current shuffle state"""
        return self.shuffle_mode
    
    def get_repeat_state(self):
        """Get current repeat state"""
        return self.repeat_mode

    def play_next_track(self):
        """Play the next track in the playlist"""
        if not self.playlist:
            print("No tracks in playlist to play")
            return

        # If in Pao mode, only play the Pao music
        if self.pao_mode:
            if self.pao_music_path:
                try:
                    pygame.mixer.music.load(self.pao_music_path)
                    pygame.mixer.music.play(-1)  # Loop the Pao music
                    print(f"Playing Pao mode music: {os.path.basename(self.pao_music_path)}")
                except Exception as e:
                    print(f"Error playing Pao music: {e}")
                    # Try to reinitialize
                    try:
                        pygame.mixer.quit()
                        pygame.mixer.init()
                        pygame.mixer.music.load(self.pao_music_path)
                        pygame.mixer.music.play(-1)
                        print("Reinitialized mixer and retried playing Pao music")
                    except Exception as e2:
                        print(f"Still failed after reinit: {e2}")
            return

        # Normal playlist playback
        try:
            current_track = self.playlist[self.current_track_index]
            print(f"Attempting to play: {current_track}")

            # Try to load and play the track
            pygame.mixer.music.load(current_track)
            pygame.mixer.music.play()

            # Check if music is actually playing
            if pygame.mixer.music.get_busy():
                print(f"Successfully playing: {os.path.basename(current_track)}")
            else:
                print(f"Music loaded but not playing: {os.path.basename(current_track)}")
                # Try alternative approach
                pygame.mixer.music.play(0)  # Explicitly play once

            # Move to next track for next time
            self.current_track_index = (self.current_track_index + 1) % len(self.playlist)
            
            # Handle playlist end and repeat mode
            if self.current_track_index == 0 and not self.repeat_mode:
                # If we've played through the whole playlist and repeat is off, stop
                self.is_playing = False
                print("Playlist ended, not repeating")
                return

        except Exception as e:
            print(f"Error playing music: {e}")
            print(f"Track that failed: {self.playlist[self.current_track_index]}")

            # Try to reinitialize and play next track
            try:
                pygame.mixer.quit()
                pygame.mixer.init()
                print("Reinitialized mixer after music failure")
            except:
                pass

            # Try next track if this one fails
            self.current_track_index = (self.current_track_index + 1) % len(self.playlist)
            if self.playlist and self.current_track_index != 0:  # Avoid infinite recursion
                self.play_next_track()

    def handle_music_end_event(self, event):
        """
        Handle the music end event to play the next track
        """
        if event.type == self.MUSIC_END_EVENT and self.is_playing:
            print("Music ended, playing next track")
            self.play_next_track()

    def stop_background_music(self):
        """Stop background music"""
        self.is_playing = False
        self.pao_mode = False
        try:
            pygame.mixer.music.stop()
            print("Background music stopped")
        except Exception as e:
            print(f"Error stopping background music: {e}")

    def start_pao_mode(self):
        """Start playing special Pao mode music"""
        print("Starting Pao mode music...")
        self.pao_mode = True
        self.is_playing = True
        try:
            if self.pao_music_path:
                pygame.mixer.music.load(self.pao_music_path)
                pygame.mixer.music.play(-1)  # Loop the Pao music
                print(f"Started Pao mode music: {os.path.basename(self.pao_music_path)}")
            else:
                print("No special Pao music found")
        except Exception as e:
            print(f"Error starting Pao mode music: {e}")

    def end_pao_mode(self):
        """End Pao mode and return to normal playlist"""
        print("Ending Pao mode, returning to normal playlist")
        self.pao_mode = False
        if self.is_playing:
            self.play_next_track()

    def pause_background_music(self):
        """Pause background music"""
        try:
            pygame.mixer.music.pause()
            print("Background music paused")
        except Exception as e:
            print(f"Error pausing background music: {e}")

    def unpause_background_music(self):
        """Unpause background music"""
        try:
            pygame.mixer.music.unpause()
            print("Background music unpaused")
        except Exception as e:
            print(f"Error unpausing background music: {e}")

    def set_volume(self, volume):
        """
        Set volume for all sounds
        """
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(volume)

    def set_music_volume(self, volume):
        """
        Set volume for background music
        """
        pygame.mixer.music.set_volume(volume)
        print(f"Music volume set to: {volume}")

    def is_music_playing(self):
        """Check if music is currently playing"""
        return pygame.mixer.music.get_busy()

    def get_music_volume(self):
        """Get current music volume"""
        return pygame.mixer.music.get_volume()

    def get_sfx_volume(self):
        """Get current SFX volume"""
        if self.sounds:
            # Return volume of first sound as representative
            for sound in self.sounds.values():
                if sound:
                    return sound.get_volume()
        return 0.7  # Default if no sounds loaded