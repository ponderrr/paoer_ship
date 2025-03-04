#!/usr/bin/env python3
# gpio_test.py - Test script for button input via GPIO

import time
import sys

try:
    import RPi.GPIO as GPIO
    print("RPi.GPIO module imported successfully")
except ImportError:
    print("RPi.GPIO module not found - are you running on a Raspberry Pi?")
    print("Run this script on your Raspberry Pi to test the buttons.")
    sys.exit(1)

# Define GPIO pins for buttons
PIN_UP = 17    # Pin 11
PIN_DOWN = 27  # Pin 13
PIN_LEFT = 22  # Pin 15
PIN_RIGHT = 23 # Pin 16
PIN_FIRE = 24  # Pin 18
PIN_MODE = 25  # Pin 22

# Map pin numbers to button names for easier reporting
PIN_TO_NAME = {
    PIN_UP: "UP",
    PIN_DOWN: "DOWN",
    PIN_LEFT: "LEFT",
    PIN_RIGHT: "RIGHT", 
    PIN_FIRE: "FIRE (Confirm)",
    PIN_MODE: "MODE (Back)"
}

def setup_gpio():
    """Set up GPIO pins for button input"""
    GPIO.setmode(GPIO.BCM)
    
    # Set up all pins as inputs with pull-up resistors
    for pin in PIN_TO_NAME.keys():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    print("GPIO pins initialized for button input")

def button_callback(channel):
    """Callback function for button press events"""
    button_name = PIN_TO_NAME.get(channel, f"Unknown pin {channel}")
    print(f"Button pressed: {button_name}")

def register_callbacks():
    """Set up event detection for all buttons"""
    for pin in PIN_TO_NAME.keys():
        # Detect falling edge (button press) with software debounce
        GPIO.add_event_detect(pin, GPIO.FALLING, callback=button_callback, bouncetime=200)
    
    print("Button callbacks registered - press buttons to test")

def main():
    """Main function to test GPIO button inputs"""
    try:
        setup_gpio()
        register_callbacks()
        
        print("\n=== Button Test ===")
        print("Press buttons to see output")
        print("Press Ctrl+C to exit")
        
        # Keep the script running
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nTest terminated by user")
    finally:
        GPIO.cleanup()
        print("GPIO resources cleaned up")

if __name__ == "__main__":
    main()