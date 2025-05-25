import pygame
import sys
import config

try:
    import gpiod

    IS_RASPBERRY_PI = True
except ImportError:
    IS_RASPBERRY_PI = False


class GPIOHandler:
    def __init__(self):
        self.chip = None
        self.lines = {}
        self.last_states = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "fire": False,
            "mode": False,
            "rotate": False,
        }

        if IS_RASPBERRY_PI:
            self.setup()

    def setup(self):
        try:
            # Try to open the GPIO chip for Pi 5
            self.chip = gpiod.Chip("gpiochip4")

            # Pin to button name mapping using config
            pin_button_map = {
                config.PIN_UP: "up",
                config.PIN_DOWN: "down",
                config.PIN_LEFT: "left",
                config.PIN_RIGHT: "right",
                config.PIN_FIRE: "fire",
                config.PIN_MODE: "mode",
                config.PIN_ROTATE: "rotate",
            }

            for pin, button_name in pin_button_map.items():
                line = self.chip.get_line(pin)
                line.request(
                    consumer=f"paoer-ship-{button_name}", type=gpiod.LINE_REQ_DIR_IN
                )
                self.lines[pin] = line

        except Exception as e:
            if config.ENABLE_DEBUG_PRINTS:
                print(f"Error setting up GPIO: {e}")
            if self.chip:
                self.chip.close()
                self.chip = None

    def cleanup(self):
        if self.chip:
            self.chip.close()
            self.chip = None

    def get_button_states(self):
        actions = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "fire": False,
            "mode": False,
            "rotate": False,
        }

        if not IS_RASPBERRY_PI or not self.chip:
            # Fallback to keyboard input
            keys = pygame.key.get_pressed()

            current_key_states = {
                "up": keys[config.INPUT_MOVE_UP],
                "down": keys[config.INPUT_MOVE_DOWN],
                "left": keys[config.INPUT_MOVE_LEFT],
                "right": keys[config.INPUT_MOVE_RIGHT],
                "fire": keys[config.INPUT_FIRE],
                "mode": keys[config.INPUT_MODE],
                "rotate": keys[config.INPUT_ROTATE],
            }

            # Register a press when the state changes from released to pressed
            for button in actions:
                if current_key_states[button] and not self.last_states[button]:
                    actions[button] = True
                elif not current_key_states[button]:
                    actions[button] = False

            self.last_states = current_key_states.copy()
            return actions

        try:
            pin_button_map = {
                config.PIN_UP: "up",
                config.PIN_DOWN: "down",
                config.PIN_LEFT: "left",
                config.PIN_RIGHT: "right",
                config.PIN_FIRE: "fire",
                config.PIN_MODE: "mode",
                config.PIN_ROTATE: "rotate",
            }

            for pin, button_name in pin_button_map.items():
                if pin not in self.lines:
                    continue

                # (active LOW with pull-up)
                line = self.lines[pin]
                # buttons with pull-up resistors, 0 means pressed
                current_state = line.get_value() == 0

                # register a press when the state changes from released to pressed
                if current_state and not self.last_states[button_name]:
                    actions[button_name] = True

                self.last_states[button_name] = current_state

        except Exception as e:
            if config.ENABLE_DEBUG_PRINTS:
                print(f"Error reading GPIO: {e}")

        return actions


__all__ = ["GPIOHandler", "IS_RASPBERRY_PI"]
