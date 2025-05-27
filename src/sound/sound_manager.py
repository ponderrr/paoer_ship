import pygame
import os
import random
import threading
import time
import math
import config


class SoundManager:
    """
    Handles game sound effects and music with single file looping support
    """

    def __init__(self, sound_dir=None):
        """
        Initialize the sound manager.

        Args:
            sound_dir (str): Directory containing sound files
        """
        if sound_dir is None:
            sound_dir = config.SOUND_DIR

        try:
            if os.uname().machine.startswith("aarch64") or "arm" in os.uname().machine:
                if config.ENABLE_DEBUG_PRINTS:
                    print("Detected Raspberry Pi, using specific audio settings")
                pygame.mixer.pre_init(
                    config.AUDIO_SAMPLE_RATE, -16, 2, config.AUDIO_BUFFER_SIZE_PI
                )
            else:
                pygame.mixer.pre_init(
                    config.AUDIO_SAMPLE_RATE, -16, 2, config.AUDIO_BUFFER_SIZE
                )

            pygame.mixer.init()
            if config.ENABLE_DEBUG_PRINTS:
                print("Pygame mixer initialized successfully")
        except Exception as e:
            if config.ENABLE_DEBUG_PRINTS:
                print(f"Error initializing pygame mixer: {e}")

        self.sound_dir = sound_dir
        self.background_music_path = config.BACKGROUND_MUSIC_PATH
        self.pao_music_path = config.PAO_MUSIC_PATH

        self.sounds = {}

        self.is_playing = False
        self.pao_mode = False

        self.monitor_thread = None

        try:
            # game sounds
            self.sounds["fire"] = self._load_sound("fire.mp3")
            self.sounds["hit"] = self._load_sound("hit.mp3")
            self.sounds["miss"] = self._load_sound("miss.mp3")
            self.sounds["ship_sunk"] = self._load_sound("ship-sunk.mp3")

            # menu navigation sounds
            self.sounds["navigate_up"] = self._load_sound("navigate_up.mp3")
            self.sounds["navigate_down"] = self._load_sound("navigate_down.mp3")
            self.sounds["accept"] = self._load_sound("accept.mp3")
            self.sounds["back"] = self._load_sound("back.mp3")

            self._load_music_paths()

        except Exception as e:
            if config.ENABLE_DEBUG_PRINTS:
                print(f"Warning: Could not load sounds: {e}")

        self._setup_fallback_sounds()

        for sound_name, sound in self.sounds.items():
            if sound:
                sound.set_volume(config.DEFAULT_SFX_VOLUME)

        pygame.mixer.music.set_volume(config.DEFAULT_MUSIC_VOLUME)

        if pygame.mixer.get_init() and config.ENABLE_DEBUG_PRINTS:
            print(f"Mixer initialized with: {pygame.mixer.get_init()}")

    def _load_sound(self, filename):
        """
        Load a sound file from the sounds directory
        """
        path = os.path.join(self.sound_dir, filename)
        try:
            if os.path.exists(path):
                sound = pygame.mixer.Sound(path)
                if config.ENABLE_DEBUG_PRINTS:
                    print(f"Successfully loaded sound: {filename}")
                return sound
            else:
                if config.ENABLE_DEBUG_PRINTS:
                    print(f"Warning: Sound file not found: {path}")
        except Exception as e:
            if config.ENABLE_DEBUG_PRINTS:
                print(f"Error loading sound {filename}: {e}")
        return None

    def _setup_fallback_sounds(self):
        """Setup fallback sounds for navigation"""
        if "navigate_up" not in self.sounds or self.sounds["navigate_up"] is None:
            if os.path.exists(os.path.join(self.sound_dir, "navigate.mp3")):
                self.sounds["navigate_up"] = self._load_sound("navigate.mp3")
                if config.ENABLE_DEBUG_PRINTS:
                    print("Using navigate sound as fallback for navigate_up")
            elif "fire" in self.sounds and self.sounds["fire"] is not None:
                self.sounds["navigate_up"] = self.sounds["fire"]
                if config.ENABLE_DEBUG_PRINTS:
                    print("Using fire sound as fallback for navigate_up")

        if "navigate_down" not in self.sounds or self.sounds["navigate_down"] is None:
            if os.path.exists(os.path.join(self.sound_dir, "navigate.mp3")):
                self.sounds["navigate_down"] = self._load_sound("navigate.mp3")
                if config.ENABLE_DEBUG_PRINTS:
                    print("Using navigate sound as fallback for navigate_down")
            elif "fire" in self.sounds and self.sounds["fire"] is not None:
                self.sounds["navigate_down"] = self.sounds["fire"]
                if config.ENABLE_DEBUG_PRINTS:
                    print("Using fire sound as fallback for navigate_down")

        if "accept" not in self.sounds or self.sounds["accept"] is None:
            if "hit" in self.sounds and self.sounds["hit"] is not None:
                self.sounds["accept"] = self.sounds["hit"]
                if config.ENABLE_DEBUG_PRINTS:
                    print("Using hit sound as fallback for accept")

        if "back" not in self.sounds or self.sounds["back"] is None:
            if "miss" in self.sounds and self.sounds["miss"] is not None:
                self.sounds["back"] = self.sounds["miss"]
                if config.ENABLE_DEBUG_PRINTS:
                    print("Using miss sound as fallback for back")

    def _load_music_paths(self):
        """
        Check if background music file exists and set up Pao music
        """
        if config.ENABLE_DEBUG_PRINTS:
            print(f"Looking for background music file: {self.background_music_path}")

        if os.path.exists(self.background_music_path):
            if config.ENABLE_DEBUG_PRINTS:
                print(f"Background music file found: {self.background_music_path}")
        else:
            if config.ENABLE_DEBUG_PRINTS:
                print(
                    f"Warning: Background music file not found at {self.background_music_path}"
                )

            # Try alternative paths
            try:
                project_root = config.BASE_DIR
                possible_paths = [
                    os.path.join(project_root, "sounds", "background.mp3"),
                    os.path.join(project_root, "src", "sounds", "background.mp3"),
                    os.path.join(project_root, "assets", "sounds", "background.mp3"),
                ]

                for path in possible_paths:
                    if os.path.exists(path):
                        self.background_music_path = path
                        if config.ENABLE_DEBUG_PRINTS:
                            print(f"Found background music at: {path}")
                        break
            except Exception as e:
                if config.ENABLE_DEBUG_PRINTS:
                    print(f"Error while searching for background music: {e}")

        # Look for Pao music
        if os.path.exists(self.pao_music_path):
            if config.ENABLE_DEBUG_PRINTS:
                print(f"Found Pao mode music at: {self.pao_music_path}")
        else:
            self.pao_music_path = self.background_music_path
            if config.ENABLE_DEBUG_PRINTS:
                print("Using regular background music for Pao mode")

    def play_sound(self, sound_name):
        """
        Play a sound by name
        """
        if sound_name in self.sounds and self.sounds[sound_name]:
            try:
                self.sounds[sound_name].play()
                if config.ENABLE_DEBUG_PRINTS:
                    print(f"Playing sound: {sound_name}")
            except Exception as e:
                if config.ENABLE_DEBUG_PRINTS:
                    print(f"Error playing sound {sound_name}: {e}")
                try:
                    pygame.mixer.quit()
                    pygame.mixer.init()
                    if config.ENABLE_DEBUG_PRINTS:
                        print("Reinitialized mixer after sound failure")
                except:
                    pass

    def _music_monitor_thread(self):
        """
        Monitor thread to check when music ends and restart if needed
        """
        while self.is_playing:
            try:
                if not pygame.mixer.music.get_busy() and not self.pao_mode:
                    time.sleep(0.5)
                    if not pygame.mixer.music.get_busy():
                        if config.ENABLE_DEBUG_PRINTS:
                            print("Music ended unexpectedly, restarting")
                        self.start_background_music()
                time.sleep(0.1)
            except Exception as e:
                if config.ENABLE_DEBUG_PRINTS:
                    print(f"Error in music monitor thread: {e}")
                time.sleep(1)

    def start_background_music(self):
        """Start playing background music in a loop"""
        if not os.path.exists(self.background_music_path):
            if config.ENABLE_DEBUG_PRINTS:
                print("No background music file found")
            return

        if config.ENABLE_DEBUG_PRINTS:
            print(f"Starting background music: {self.background_music_path}")
        try:
            self.is_playing = True
            self.pao_mode = False
            pygame.mixer.music.load(self.background_music_path)
            pygame.mixer.music.play(-1)
            if config.ENABLE_DEBUG_PRINTS:
                print("Background music started in loop mode")

            if self.monitor_thread is None or not self.monitor_thread.is_alive():
                self.monitor_thread = threading.Thread(
                    target=self._music_monitor_thread, daemon=True
                )
                self.monitor_thread.start()
                if config.ENABLE_DEBUG_PRINTS:
                    print("Started music monitor thread")
        except Exception as e:
            if config.ENABLE_DEBUG_PRINTS:
                print(f"Error starting background music: {e}")

    def toggle_shuffle(self):
        """Toggle shuffle mode (kept for compatibility, does nothing now)"""
        if config.ENABLE_DEBUG_PRINTS:
            print("Shuffle mode not applicable with single music file")
        return False

    def toggle_repeat(self):
        """Toggle repeat mode (kept for compatibility, always on now)"""
        if config.ENABLE_DEBUG_PRINTS:
            print("Repeat mode always on with single music file")
        return True

    def get_shuffle_state(self):
        """Get current shuffle state (kept for compatibility)"""
        return False

    def get_repeat_state(self):
        """Get current repeat state (kept for compatibility)"""
        return True

    def play_next_track(self):
        """Restart the background music (kept for compatibility)"""
        self.start_background_music()

    def handle_music_end_event(self, event):
        """Handle music end event (kept for compatibility)"""
        pass

    def stop_background_music(self):
        """Stop background music"""
        self.is_playing = False
        self.pao_mode = False
        try:
            pygame.mixer.music.stop()
            if config.ENABLE_DEBUG_PRINTS:
                print("Background music stopped")
        except Exception as e:
            if config.ENABLE_DEBUG_PRINTS:
                print(f"Error stopping background music: {e}")

    def start_pao_mode(self):
        """Start playing special Pao mode music"""
        if config.ENABLE_DEBUG_PRINTS:
            print("Starting Pao mode music...")
        self.pao_mode = True
        self.is_playing = True
        try:
            if self.pao_music_path:
                pygame.mixer.music.load(self.pao_music_path)
                pygame.mixer.music.play(-1)
                if config.ENABLE_DEBUG_PRINTS:
                    print(
                        f"Started Pao mode music: {os.path.basename(self.pao_music_path)}"
                    )
            else:
                if config.ENABLE_DEBUG_PRINTS:
                    print("No special Pao music found")
        except Exception as e:
            if config.ENABLE_DEBUG_PRINTS:
                print(f"Error starting Pao mode music: {e}")

    def end_pao_mode(self):
        """End Pao mode and return to normal music"""
        if config.ENABLE_DEBUG_PRINTS:
            print("Ending Pao mode, returning to normal music")
        self.pao_mode = False
        if self.is_playing:
            self.start_background_music()

    def pause_background_music(self):
        """Pause background music"""
        try:
            pygame.mixer.music.pause()
            if config.ENABLE_DEBUG_PRINTS:
                print("Background music paused")
        except Exception as e:
            if config.ENABLE_DEBUG_PRINTS:
                print(f"Error pausing background music: {e}")

    def unpause_background_music(self):
        """Unpause background music"""
        try:
            pygame.mixer.music.unpause()
            if config.ENABLE_DEBUG_PRINTS:
                print("Background music unpaused")
        except Exception as e:
            if config.ENABLE_DEBUG_PRINTS:
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
        if config.ENABLE_DEBUG_PRINTS:
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
            for sound in self.sounds.values():
                if sound:
                    return sound.get_volume()
        return config.DEFAULT_SFX_VOLUME

    def draw_now_playing(self, screen, x, y, font, width=300, height=50):
        """
        Draw a "Now Playing" display on screen
        """
        try:
            bg_rect = pygame.Rect(x, y, width, height)
            pygame.draw.rect(screen, (30, 30, 30), bg_rect, border_radius=5)
            pygame.draw.rect(screen, (100, 100, 100), bg_rect, 2, border_radius=5)

            if self.pao_mode:
                current_track = os.path.basename(self.pao_music_path)
                status = "PAO MODE"
            else:
                current_track = os.path.basename(self.background_music_path)
                status = "Now Playing"

            track_name = current_track.replace(".mp3", "").replace("_", " ").title()
            info_text = font.render(f"{status}: {track_name}", True, (200, 200, 200))

            text_rect = info_text.get_rect(center=(x + width // 2, y + height // 2))
            screen.blit(info_text, text_rect)

        except Exception as e:
            if config.ENABLE_DEBUG_PRINTS:
                print(f"Error drawing now playing display: {e}")
