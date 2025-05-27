import pygame
import sys
import config
from src.ui.ship_placement_screen import ShipPlacementScreen


def game_mode_select(screen, gpio_handler, sound_manager, game_screen_func):
    """
    Screen to select game mode (AI or Player) and AI difficulty

    Args:
        screen: Pygame display surface
        gpio_handler: GPIO handler for button inputs
        sound_manager: Sound manager instance
        game_screen_func: Function to launch the main game screen
    """
    width = screen.get_width()
    height = screen.get_height()

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 28)

    options = ["VS AI", "VS Player"]
    current_option = 0
    current_difficulty = 0
    show_difficulty = False

    running = True
    while running:
        screen.fill(config.selected_background_color)
        title_text = font.render("Select Game Mode", True, config.WHITE)
        title_rect = title_text.get_rect(center=(width // 2, 80))
        screen.blit(title_text, title_rect)

        for i, option in enumerate(options):
            color = config.LIGHT_BLUE if i == current_option else config.WHITE
            option_text = font.render(option, True, color)
            option_rect = option_text.get_rect(center=(width // 2, 180 + i * 60))
            screen.blit(option_text, option_rect)

            if i == current_option:
                rect = pygame.Rect(
                    option_rect.left - 10,
                    option_rect.top - 5,
                    option_rect.width + 20,
                    option_rect.height + 10,
                )
                pygame.draw.rect(screen, color, rect, 2, border_radius=5)

        if current_option == 0:
            difficulty_title = small_font.render(
                "Select Difficulty:", True, config.WHITE
            )
            screen.blit(difficulty_title, (width // 2 - 100, 320))

            for i, diff in enumerate(config.AI_DIFFICULTIES):
                if diff == "Pao":
                    color = config.RED if i == current_difficulty else (255, 100, 100)
                else:
                    color = (
                        config.LIGHT_BLUE if i == current_difficulty else config.WHITE
                    )

                diff_text = small_font.render(diff, True, color)
                diff_rect = diff_text.get_rect(center=(width // 2, 360 + i * 40))
                screen.blit(diff_text, diff_rect)

                if i == current_difficulty:
                    rect = pygame.Rect(
                        diff_rect.left - 10,
                        diff_rect.top - 5,
                        diff_rect.width + 20,
                        diff_rect.height + 10,
                    )
                    pygame.draw.rect(screen, color, rect, 2, border_radius=5)

            if current_difficulty == 3:  # Pao mode
                warning_text = small_font.render(
                    "WARNING: Impossible difficulty!", True, config.RED
                )
                warning_rect = warning_text.get_rect(center=(width // 2, 520))
                screen.blit(warning_text, warning_rect)

        help_text = small_font.render(
            "Up/Down: Navigate | Fire: Select | Mode: Back", True, config.LIGHT_GRAY
        )
        screen.blit(help_text, (width // 2 - 190, height - 40))

        for event in pygame.event.get():
            sound_manager.handle_music_end_event(event)
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, config.INPUT_MODE]:
                    sound_manager.play_sound("back")
                    running = False
                elif event.key == config.INPUT_MOVE_UP:
                    if current_option == 0 and current_difficulty > 0:
                        current_difficulty -= 1
                        sound_manager.play_sound("navigate_up")
                    else:
                        old_option = current_option
                        current_option = (current_option - 1) % len(options)
                        current_difficulty = 0
                        if old_option != current_option:
                            sound_manager.play_sound("navigate_up")
                elif event.key == config.INPUT_MOVE_DOWN:
                    if (
                        current_option == 0
                        and current_difficulty < len(config.AI_DIFFICULTIES) - 1
                    ):
                        current_difficulty += 1
                        sound_manager.play_sound("navigate_down")
                    else:
                        old_option = current_option
                        current_option = (current_option + 1) % len(options)
                        current_difficulty = 0
                        if old_option != current_option:
                            sound_manager.play_sound("navigate_down")
                elif event.key in [pygame.K_RETURN, config.INPUT_FIRE]:
                    sound_manager.play_sound("accept")
                    ai_mode = current_option == 0
                    difficulty = (
                        config.AI_DIFFICULTIES[current_difficulty] if ai_mode else None
                    )

                    placement_screen = ShipPlacementScreen(
                        screen, gpio_handler, ai_mode, difficulty, sound_manager
                    )
                    player1_board, player2_board = placement_screen.run()
                    game_screen_func(ai_mode, difficulty, player1_board, player2_board)
                    running = False

        button_states = gpio_handler.get_button_states()

        if button_states["up"]:
            if current_option == 0 and current_difficulty > 0:
                current_difficulty -= 1
                sound_manager.play_sound("navigate_up")
            else:
                old_option = current_option
                current_option = (current_option - 1) % len(options)
                current_difficulty = 0
                if old_option != current_option:
                    sound_manager.play_sound("navigate_up")

        if button_states["down"]:
            if (
                current_option == 0
                and current_difficulty < len(config.AI_DIFFICULTIES) - 1
            ):
                current_difficulty += 1
                sound_manager.play_sound("navigate_down")
            else:
                old_option = current_option
                current_option = (current_option + 1) % len(options)
                current_difficulty = 0
                if old_option != current_option:
                    sound_manager.play_sound("navigate_down")

        if button_states["fire"]:
            sound_manager.play_sound("accept")
            ai_mode = current_option == 0
            difficulty = config.AI_DIFFICULTIES[current_difficulty] if ai_mode else None
            placement_screen = ShipPlacementScreen(
                screen, gpio_handler, ai_mode, difficulty, sound_manager
            )
            player1_board, player2_board = placement_screen.run()
            game_screen_func(ai_mode, difficulty, player1_board, player2_board)
            running = False

        if button_states["mode"]:
            sound_manager.play_sound("back")
            running = False

        pygame.display.flip()
        clock.tick(config.TARGET_FPS)
