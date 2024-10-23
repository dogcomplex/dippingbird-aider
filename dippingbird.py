import time
import os
import threading
import pygame
from pywinauto import Application, Desktop
from PIL import Image, ImageSequence
import signal
import sys
import re
import random
import atexit
import subprocess

APP_TITLE = "Administrator: Command Prompt - python  -m aider"
RUN_EVERY = 3  # seconds

REEVALUATION_MESSAGE = "Let's take a step back and re-evaluate if what we're doing makes sense. We might be getting in a loop here. Let's do something a little more out of left field instead."
REEVALUATION_CHANCE = 0.1

FORCE_EXIT_DELAY = 5  # seconds

GIF_PATH = 'dippingbird.gif'
DISABLE_GIF = False  # Set to True to disable the GIF display
WINDOW_SIZE = (300, 300)
FRAME_RATE = 60


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
        print("Listing relevant windows:")
        windows = Desktop(backend="win32").windows()
        search_terms = ["command", "prompt", "aider"]
        
        filtered_windows = [
            w for w in windows
            if any(term.lower() in w.window_text().lower() for term in search_terms)
        ]
        
        for w in filtered_windows:
            print(f"Window Title: '{w.window_text()}'")

    except Exception as e:
        print(f"Error listing windows: {e}")

def force_exit(signum, frame):
    print("\nForce exiting the script...")
    os._exit(1)

def handle_sigint(signum, frame):
    print("\nCTRL+C detected! Stopping the script...")
    cleanup()
    # Set a timer for force exit after FORCE_EXIT_DELAY seconds
    signal.signal(signal.SIGALRM, force_exit)
    signal.alarm(FORCE_EXIT_DELAY)
    sys.exit(0)

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
    last_check = -interval
    while not should_exit and not stop_event.is_set():
        try:
            # Check the command output every second
            if stop_event.wait(1):  # Wait for 1 second or until stop_event is set
                break
            rounded_time = round(time.time() - start_time)
            if rounded_time > last_check + interval:
                app = Application().connect(title_re=f"^{re.escape(APP_TITLE)}.*")
                window = app.window(title_re=f"^{re.escape(APP_TITLE)}.*")
                # occasionally send a prompt to get out of loops:
                if random.random() < REEVALUATION_CHANCE:
                    window.send_keystrokes(REEVALUATION_MESSAGE + "{ENTER}")
                else:
                    window.send_keystrokes("y{ENTER}")
                print(f"{rounded_time}  y...")
                last_check = rounded_time
            time.sleep(1)
        except Exception as e:
            print(f"Error sending keys: {e}")
            time.sleep(60)

class DippingBirdGIF:
    def __init__(self):
        self.screen = None
        self.frames = []
        self.durations = []
        self.current_frame = 0
        self.frame_time = 0
        self.clock = pygame.time.Clock()

    def setup(self):
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Dipping Bird")

        if not os.path.exists(GIF_PATH):
            print(f"Error: '{GIF_PATH}' not found.")
            return False

        gif = Image.open(GIF_PATH)
        self.durations = [frame.info['duration'] for frame in ImageSequence.Iterator(gif)]
        self.frames = [pygame.image.fromstring(frame.convert("RGBA").tobytes(), frame.size, "RGBA") for frame in ImageSequence.Iterator(gif)]
        return True

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        self.screen.fill((255, 255, 255))

        frame = self.frames[self.current_frame]
        duration = self.durations[self.current_frame]

        frame_rect = frame.get_rect(center=(WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2))
        self.screen.blit(frame, frame_rect)

        pygame.display.flip()

        self.frame_time += self.clock.tick(FRAME_RATE)
        if self.frame_time > duration:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.frame_time = 0

        return True

def cleanup():
    global should_exit
    should_exit = True
    stop_event.set()
    pygame.quit()
    print("Cleanup complete.")

def main():
    global should_exit
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)
    atexit.register(cleanup)

    # Initialize pygame in the main thread
    if not DISABLE_GIF:
        pygame.init()

    key_thread = threading.Thread(target=send_keys_if_match, daemon=True)
    key_thread.start()

    if not DISABLE_GIF:
        dipping_bird = DippingBirdGIF()
        if not dipping_bird.setup():
            cleanup()
            return

    try:
        while not should_exit and not stop_event.is_set():
            if not DISABLE_GIF:
                if not dipping_bird.update():
                    break
                if stop_event.wait(1/60):  # Wait for 1/60 second or until stop_event is set
                    break
            else:
                if stop_event.wait(1):  # Wait for 1 second or until stop_event is set when GIF is disabled
                    break
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected, exiting...")
    finally:
        cleanup()
        key_thread.join(timeout=2)
        print("Key thread terminated.")
        # Force exit after cleanup
        os._exit(0)

if __name__ == "__main__":
    # if called with --help, run inspect_controls
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        inspect_controls()
    else:
        main()
