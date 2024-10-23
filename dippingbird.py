import time
import os
import threading
import pygame
from pywinauto import Application
from PIL import Image, ImageSequence
import signal
import sys
import re
import random

APP_TITLE = "Administrator: Command Prompt - python  -m aider"
GIF_PATH = 'dippingbird.gif'
RUN_EVERY = 5  # seconds

# Event to manage thread termination
stop_event = threading.Event()

# Global flag for stopping
should_exit = False

def list_open_windows():
    print("Listing all open windows:")
    windows = Desktop(backend="win32").windows()
    for w in windows:
        print(f"Window Title: '{w.window_text()}'")

# Connect to the command prompt window
def inspect_controls():
    try:
        windows = list_open_windows()
        
        app = Application().connect(title_re=f"^{re.escape(APP_TITLE)}.*")
        window = app.window(title_re=f"^{re.escape(APP_TITLE)}.*")
        
        # Print all the control identifiers to understand the structure
        window.print_control_identifiers()
    except Exception as e:
        print(f"Error connecting to window: {e}")


def handle_sigint(signum, frame):
    global should_exit
    print("\nCTRL+C detected! Stopping the script...")
    should_exit = True
    stop_event.set()
    pygame.quit()  # Ensure pygame closes
    sys.exit(0)

import subprocess


# Check if the cmd output matches either the "> " or "[Yes]:"
def check_cmd_output():
    try:
        # Connect to the window
        app = Application().connect(title_re=f"^{re.escape(APP_TITLE)}.*")
        window = app.window(title_re=f"^{re.escape(APP_TITLE)}.*")
        
        # Access the text control inside the command prompt window
        text_control = window.child_window(control_type="Edit")  # The command prompt text area is usually an "Edit" control
        
        # Get the window text
        window_text = text_control.wrapper_object().texts()
        
        # Join all the window text lines into one string
        cmd_output = "\n".join(window_text).strip()
        
        # Print the last 20 lines for debugging
        print("\n".join(window_text[-20:]).strip())
        
        # Check if the command ends with "> " or "[Yes]:"
        if re.search(r"> *$", cmd_output) or cmd_output.endswith("[Yes]:"):
            return True
    except Exception as e:
        print(f"Error reading window: {e}")
    return False


def send_keys_if_match():
    global should_exit
    start_time = time.time()
    interval = RUN_EVERY
    last_check = -interval # skip to the first check
    while not should_exit:
        try:
            rounded_time = round(time.time() - start_time)
            # Check the command output every second
            if rounded_time > last_check + interval:
                # if check_cmd_output():
                app = Application().connect(title_re=f"^{re.escape(APP_TITLE)}.*")
                window = app.window(title_re=f"^{re.escape(APP_TITLE)}.*")
                # occasionally send a prompt to get out of loops:
                # random 1/10 chance:
                if random.random() < 0.1:
                    message = "Let's take a step back and re-evaluate if what we're doing makes sense.  We might be getting in a loop here.  Let's do something a little more out of left field instead."
                    window.send_keystrokes(message + "{ENTER}")
                else:
                    window.send_keystrokes("y{ENTER}")
                print(f"{rounded_time}  y...")
                # else:
                #    print(f"{rounded_time}  zzzz.....")
                last_check = rounded_time
            time.sleep(1)
        except Exception as e:
            print(f"Error sending keys: {e}")
            time.sleep(60)
            #break

def play_dipping_bird_gif():
    global should_exit
    pygame.init()

    # Set up the display
    screen = pygame.display.set_mode((300, 300))  # Adjust size as needed
    pygame.display.set_caption("Dipping Bird")

    if not os.path.exists(GIF_PATH):
        print(f"Error: '{GIF_PATH}' not found.")
        stop_event.set()
        return

    # Open the GIF
    gif = Image.open(GIF_PATH)

    # Get the duration of each frame
    durations = [frame.info['duration'] for frame in ImageSequence.Iterator(gif)]
    frames = [pygame.image.fromstring(frame.convert("RGBA").tobytes(), frame.size, "RGBA") for frame in ImageSequence.Iterator(gif)]

    clock = pygame.time.Clock()
    current_frame = 0
    frame_time = 0
    running = True

    while running and not should_exit:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                should_exit = True
                stop_event.set()

        # Clear the screen
        screen.fill((255, 255, 255))  # White background

        # Get the current frame and its duration
        frame = frames[current_frame]
        duration = durations[current_frame]

        # Center the frame
        frame_rect = frame.get_rect(center=(150, 150))
        screen.blit(frame, frame_rect)

        pygame.display.flip()

        # Move to the next frame after the duration has passed
        frame_time += clock.tick(60)
        if frame_time > duration:
            current_frame = (current_frame + 1) % len(frames)  # Loop the GIF
            frame_time = 0

    pygame.quit()

# Create and manage threads for both tasks
def main():
    global should_exit
    
    # Register the SIGINT handler for CTRL+C
    signal.signal(signal.SIGINT, handle_sigint)

    gif_thread = threading.Thread(target=play_dipping_bird_gif, daemon=True)
    key_thread = threading.Thread(target=send_keys_if_match, daemon=True)
    
    gif_thread.start()
    key_thread.start()

    # Keep checking for the stop_event and join the threads when it is set
    try:
        while not should_exit:
            time.sleep(0.1)  # Check every 100ms for responsiveness

        gif_thread.join()
        key_thread.join()
        print("Both threads terminated.")
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected, exiting...")
        stop_event.set()
        pygame.quit()
        sys.exit(0)

if __name__ == "__main__":
    main()
