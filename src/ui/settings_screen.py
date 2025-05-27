import pygame
import config
import sys

WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
LIGHT_BLUE = (80, 170, 255)
LIGHT_GRAY = (180, 180, 180)

def settings_screen(screen, gpio_handler, sound_manager):
    """
    Settings screen with volume controls, shuffle and repeat options
    
    Args:
        screen: Pygame display surface
        gpio_handler: GPIO handler for button inputs
        sound_manager: Sound manager instance
    """
    width = screen.get_width()
    height = screen.get_height()
    
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    
    music_volume = sound_manager.get_music_volume()
    sfx_volume = sound_manager.get_sfx_volume()
    shuffle_state = sound_manager.get_shuffle_state()
    repeat_state = sound_manager.get_repeat_state()
    
    settings_options = ["Music Volume", "SFX Volume", "Shuffle", "Repeat", "Back to Menu"]
    current_option = 0
    
    running = True
    while running:
        screen.fill(config.selected_background_color)
        
        title_text = font.render("Settings", True, WHITE)
        title_rect = title_text.get_rect(center=(width // 2, 80))
        screen.blit(title_text, title_rect)
        
        for i, option in enumerate(settings_options):
            color = LIGHT_BLUE if i == current_option else WHITE
            option_text = font.render(option, True, color)
            option_rect = option_text.get_rect(center=(width // 2, 180 + i * 60))
            screen.blit(option_text, option_rect)
            
            if i == current_option:
                rect = pygame.Rect(option_rect.left - 10, option_rect.top - 5,
                                 option_rect.width + 20, option_rect.height + 10)
                pygame.draw.rect(screen, color, rect, 2, border_radius=5)
        
        music_bar_x = width // 2 - 100
        music_bar_y = 180 + 30
        music_bar_width = 200
        music_bar_height = 10
        
        pygame.draw.rect(screen, LIGHT_GRAY, 
                        (music_bar_x, music_bar_y, music_bar_width, music_bar_height))
        pygame.draw.rect(screen, BLUE, 
                        (music_bar_x, music_bar_y, 
                         int(music_bar_width * music_volume), music_bar_height))
        pygame.draw.rect(screen, WHITE, 
                        (music_bar_x, music_bar_y, music_bar_width, music_bar_height), 2)
        
        volume_text = small_font.render(f"{int(music_volume * 100)}%", True, WHITE)
        volume_rect = volume_text.get_rect(center=(width // 2 + 150, music_bar_y + music_bar_height // 2))
        screen.blit(volume_text, volume_rect)
        
        sfx_bar_x = width // 2 - 100
        sfx_bar_y = 240 + 30
        sfx_bar_width = 200
        sfx_bar_height = 10
        
        pygame.draw.rect(screen, LIGHT_GRAY, 
                        (sfx_bar_x, sfx_bar_y, sfx_bar_width, sfx_bar_height))

        pygame.draw.rect(screen, BLUE, 
                        (sfx_bar_x, sfx_bar_y, 
                         int(sfx_bar_width * sfx_volume), sfx_bar_height))
        
        pygame.draw.rect(screen, WHITE, 
                        (sfx_bar_x, sfx_bar_y, sfx_bar_width, sfx_bar_height), 2)
        
        sfx_volume_text = small_font.render(f"{int(sfx_volume * 100)}%", True, WHITE)
        sfx_volume_rect = sfx_volume_text.get_rect(center=(width // 2 + 150, sfx_bar_y + sfx_bar_height // 2))
        screen.blit(sfx_volume_text, sfx_volume_rect)
        
        shuffle_color = (0, 255, 0) if shuffle_state else (255, 0, 0)
        shuffle_text = small_font.render(f"{'ON' if shuffle_state else 'OFF'}", True, shuffle_color)
        shuffle_rect = shuffle_text.get_rect(center=(width // 2 + 150, 300 + 10))
        screen.blit(shuffle_text, shuffle_rect)
        
        repeat_color = (0, 255, 0) if repeat_state else (255, 0, 0)
        repeat_text = small_font.render(f"{'ON' if repeat_state else 'OFF'}", True, repeat_color)
        repeat_rect = repeat_text.get_rect(center=(width // 2 + 150, 360 + 10))
        screen.blit(repeat_text, repeat_rect)
        
        help_text = small_font.render("Up/Down: Navigate | Left/Right: Adjust | Fire: Toggle/Select | Mode: Back", 
                                    True, LIGHT_GRAY)
        help_rect = help_text.get_rect(center=(width // 2, height - 40))
        screen.blit(help_text, help_rect)
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    current_option = (current_option - 1) % len(settings_options)
                    sound_manager.play_sound("navigate_up")
                elif event.key == pygame.K_DOWN:
                    current_option = (current_option + 1) % len(settings_options)
                    sound_manager.play_sound("navigate_down")
                elif event.key == pygame.K_LEFT:
                    if current_option == 0:  # Music volume
                        music_volume = max(0, music_volume - 0.05)
                        sound_manager.set_music_volume(music_volume)
                    elif current_option == 1:  # SFX volume
                        sfx_volume = max(0, sfx_volume - 0.05)
                        sound_manager.set_volume(sfx_volume)
                        sound_manager.play_sound("navigate_down")  # Test the volume
                elif event.key == pygame.K_RIGHT:
                    if current_option == 0:  # Music volume
                        music_volume = min(1.0, music_volume + 0.05)
                        sound_manager.set_music_volume(music_volume)
                    elif current_option == 1:  # SFX volume
                        sfx_volume = min(1.0, sfx_volume + 0.05)
                        sound_manager.set_volume(sfx_volume)
                        sound_manager.play_sound("navigate_up")  # Test the volume
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    if current_option == 2:  # Shuffle
                        shuffle_state = sound_manager.toggle_shuffle()
                        sound_manager.play_sound("accept")
                    elif current_option == 3:  # Repeat
                        repeat_state = sound_manager.toggle_repeat()
                        sound_manager.play_sound("accept")
                    elif current_option == 4:  # Back to menu
                        sound_manager.play_sound("back")
                        running = False
                elif event.key in [pygame.K_ESCAPE, pygame.K_TAB]:
                    sound_manager.play_sound("back")
                    running = False
        
        # GPIO button handling
        button_states = gpio_handler.get_button_states()
        
        if button_states['up']:
            current_option = (current_option - 1) % len(settings_options)
            sound_manager.play_sound("navigate_up")
            
        if button_states['down']:
            current_option = (current_option + 1) % len(settings_options)
            sound_manager.play_sound("navigate_down")
            
        if button_states['left']:
            if current_option == 0: 
                music_volume = max(0, music_volume - 0.05)
                sound_manager.set_music_volume(music_volume)
            elif current_option == 1: 
                sfx_volume = max(0, sfx_volume - 0.05)
                sound_manager.set_volume(sfx_volume)
                sound_manager.play_sound("navigate_down")  
                
        if button_states['right']:
            if current_option == 0: 
                music_volume = min(1.0, music_volume + 0.05)
                sound_manager.set_music_volume(music_volume)
            elif current_option == 1:  
                sfx_volume = min(1.0, sfx_volume + 0.05)
                sound_manager.set_volume(sfx_volume)
                sound_manager.play_sound("navigate_up") 
                
        if button_states['fire']:
            if current_option == 2:  
                shuffle_state = sound_manager.toggle_shuffle()
                sound_manager.play_sound("accept")
            elif current_option == 3:  
                repeat_state = sound_manager.toggle_repeat()
                sound_manager.play_sound("accept")
            elif current_option == 4:  
                sound_manager.play_sound("back")
                running = False
                
        if button_states['mode']:
            sound_manager.play_sound("back")
            running = False
        
        pygame.display.flip()
        clock.tick(30)