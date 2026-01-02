import cv2
import numpy as np
import pyautogui
import threading
import time
import keyboard
import os
import logging
import pygetwindow as gw

# Global variables
killswitch_activated = False
Rally_activated = False
Rally_activated2 = False
Farm_activated = True
window_index = 0

class WindowTitleFilter(logging.Filter):
    def filter(self, record):
        global windows, window_index
        try:
            if 'windows' in globals() and windows:
                if 0 <= window_index < len(windows):
                    record.window_title = windows[window_index].title
                else:
                    record.window_title = "Unknown"
            else:
                record.window_title = "No Window"
        except Exception:
            record.window_title = "Error"
        return True

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(window_title)s - %(levelname)s - %(message)s')
logging.getLogger().addFilter(WindowTitleFilter())

windows = gw.getWindowsWithTitle('wosmin') + gw.getWindowsWithTitle('WOSMIN')
if windows:
    for win in windows:
        try:
            win.moveTo(1, 1)
            logging.info(f"Window '{win.title}' moved to (0, 0)")
        except Exception as e:
            logging.error(f"Failed to move window '{win.title}': {e}")

# Move console window
console_windows = gw.getWindowsWithTitle('KingShotAutoConsole')
if console_windows:
    try:
        console_windows[0].moveTo(650, 0)
        logging.info("Console window moved to (650, 0)")
    except Exception as e:
        logging.error(f"Failed to move console window: {e}")

# Constants
SCREEN_CROP = (0, 0, 622, 1080)
TM_METHOD = cv2.TM_CCOEFF_NORMED

def match_and_handle(screen_gray, template, threshold, on_match, region=None):
    """
    Find matches of template in screen_gray above threshold, call on_match(x, y) for each match.
    If region is provided, limit the search to that rectangle within screen_gray.

    region: Optional tuple (x1, y1, x2, y2) specifying inclusive-exclusive bounds in the cropped screen coordinates.
    """
    # Apply region of interest if provided
    x_offset = 0
    y_offset = 0
    search_area = screen_gray
    if region is not None:
        x1, y1, x2, y2 = region
        # Ensure bounds are within the image dimensions
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(screen_gray.shape[1], x2)
        y2 = min(screen_gray.shape[0], y2)
        if x2 > x1 and y2 > y1:
            search_area = screen_gray[y1:y2, x1:x2]
            x_offset = x1
            y_offset = y1
        else:
            # Invalid region; fallback to full image
            search_area = screen_gray
            x_offset = 0
            y_offset = 0

    result = cv2.matchTemplate(search_area, template, TM_METHOD)
    loc = np.where(result >= threshold)
    if loc[0].size > 0:
        for pt in zip(*loc[::-1]):
            x = x_offset + pt[0] + template.shape[1] // 2
            y = y_offset + pt[1] + template.shape[0] // 2
            on_match(x, y)
            break
        return True
    return False

def load_templates():
    """Load and return all templates used by the script as a dict of grayscale images."""
    base_dir = os.path.join(os.path.dirname(__file__), 'gameplay')
    return {
        "marchqueue": cv2.imread(os.path.join(base_dir, "marchqueue.png"), cv2.IMREAD_GRAYSCALE),
        "online": cv2.imread(os.path.join(base_dir, "online.png"), cv2.IMREAD_GRAYSCALE),
        "completed": cv2.imread(os.path.join(base_dir, "completed.png"), cv2.IMREAD_GRAYSCALE),
        "heroadvance": cv2.imread(os.path.join(base_dir, "heroadvance.png"), cv2.IMREAD_GRAYSCALE),
        "contribution": cv2.imread(os.path.join(base_dir, "contribution.png"), cv2.IMREAD_GRAYSCALE),
        "good": cv2.imread(os.path.join(base_dir, "good.png"), cv2.IMREAD_GRAYSCALE),
        "free": cv2.imread(os.path.join(base_dir, "free.png"), cv2.IMREAD_GRAYSCALE),
        "idle": cv2.imread(os.path.join(base_dir, "idle.png"), cv2.IMREAD_GRAYSCALE),
        "world": cv2.imread(os.path.join(base_dir, "world.png"), cv2.IMREAD_GRAYSCALE),
        "conquest": cv2.imread(os.path.join(base_dir, "conquest.png"), cv2.IMREAD_GRAYSCALE),
        "conquest1": cv2.imread(os.path.join(base_dir, "conquest1.png"), cv2.IMREAD_GRAYSCALE),
        "conquest2": cv2.imread(os.path.join(base_dir, "conquest2.png"), cv2.IMREAD_GRAYSCALE),
        "help": cv2.imread(os.path.join(base_dir, "help.png"), cv2.IMREAD_GRAYSCALE),
        "back": cv2.imread(os.path.join(base_dir, "back.png"), cv2.IMREAD_GRAYSCALE),
        "fountain": cv2.imread(os.path.join(base_dir, "fountain.png"), cv2.IMREAD_GRAYSCALE),
        "rally": cv2.imread(os.path.join(base_dir, "rally.png"), cv2.IMREAD_GRAYSCALE),
        "rally2": cv2.imread(os.path.join(base_dir, "rally2.png"), cv2.IMREAD_GRAYSCALE),
    }

def grab_screen_gray():
    """Capture the screen, crop to the app region, and return a grayscale numpy array."""
    screenshot = pyautogui.screenshot()
    screenshot = screenshot.crop(SCREEN_CROP)
    screen_np = np.array(screenshot)
    return cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)


def safe_press(key):
    """
    Safely press a key, ensuring the target window is active and within bounds.
    Wraps pyautogui.press with error handling and logging.
    Returns False if the keypress was skipped, True if successful.
    """
    global windows, window_index
    try:
        # Verify window is still available and active
        if not windows:
            logging.warning(f"No windows available. Skipping keypress for key '{key}'.")
            return False
        
        if not (0 <= window_index < len(windows)):
            logging.warning(f"window_index {window_index} is out of bounds (0-{len(windows)-1}). Skipping keypress for key '{key}'.")
            return False
        
        try:
            windows[window_index].activate()
        except Exception as e:
            logging.warning(f"Could not activate window before keypress: {e}. Skipping keypress for key '{key}'.")
            return False
        
        # Perform the keypress
        pyautogui.press(key)
        return True
    except pyautogui.FailSafeException:
        logging.error("PyAutoGUI failsafe triggered (mouse moved to a corner). Aborting keypress.")
        return False
    except Exception as e:
        logging.exception(f"safe_press failed for key '{key}': {e}")
        return False


# Function to monitor the killswitch key
def monitor_killswitch(killswitch_key):
    global killswitch_activated
    global Rally_activated
    global Rally_activated2
    global Farm_activated
    while True:
        if keyboard.is_pressed(killswitch_key) or keyboard.is_pressed('Ctrl+C'):
            logging.info("Killswitch activated (Key or End). Exiting...")
            killswitch_activated = True
            # Force exit to ensure immediate termination if threads are stuck sleeping
            os._exit(0)
        if keyboard.is_pressed('r'):
            logging.info("Rally activated.")
            Rally_activated = not Rally_activated
        if keyboard.is_pressed('t'):
            logging.info("Rally 2 activated.")
            Rally_activated2 = not Rally_activated2
        if keyboard.is_pressed('f'):
            logging.info("Farm activated.")
            Farm_activated = not Farm_activated
        time.sleep(0.1)

# Function to monitor the marchqueue empty
def monitor_marchqueue(click_delay):
    global killswitch_activated
    global Rally_activated
    global Rally_activated2
    global Farm_activated
    global windows
    global window_index
    method = TM_METHOD
    templates = load_templates()

    window_index = 0    
    while True:
        if windows:
            try:
                windows[window_index].activate()
            except Exception:
                print("Ok")

        # Check if killswitch is activated after processing each image
        if killswitch_activated:
            break

        time.sleep(3)

        #open wilderness
        delay = [1,3]
        key=["S","1"]
        SpecialClick(key,delay)        
        screen_gray = grab_screen_gray()

        #always click on world
        def on_world(x, y):
            pyautogui.click(x, y)
            time.sleep(3)
            pyautogui.moveTo(10,10)
            logging.info(f"Clicked on world ({x}, {y})")
        if match_and_handle(screen_gray, templates["world"], 0.9, on_world):
            continue

        #always click on help
        def on_help(x, y):
            pyautogui.click(x, y)
            time.sleep(3)
            pyautogui.moveTo(10,10)
            logging.info(f"Clicked on help ({x}, {y})")
        if match_and_handle(screen_gray, templates["help"], 0.8, on_help):
            continue    

        #always click on back
        def on_back(x, y):
            pyautogui.click(x, y)
            time.sleep(3)
            pyautogui.moveTo(10,10)
            logging.info(f"Clicked on back ({x}, {y})")
        if match_and_handle(screen_gray, templates["back"], 0.7, on_back, region=(0, 0, 105, 117)):
            continue    

        # Perform template matching for marchqueue
        def on_marchqueue(x, y):
            time.sleep(3)
            # additonal bread gathering
            #delay = [1.5,1.5,1.5,1.5,1.5,2.5,1.5,1.5]
            #key = ["I","left","left","O","F","G","6","E"]
            #SpecialClick(key,delay)

            # bread gathering
            SpecialClick(['I','I'], [1.5,1.5])
            pyautogui.moveTo(522,768)
            pyautogui.dragTo(70,768,duration = 1)
            SpecialClick(['B','F','G','1','2','E'], [1.5,1.5,2.5,1.5,1.5,1.5])
            
            # wood gathering
            SpecialClick(['I','I'], [1.5,1.5])
            pyautogui.moveTo(522,768)
            pyautogui.dragTo(70,768,duration = 1)
            SpecialClick(["O","F","G","1","2","E"], [1.5,1.5,2.5,1.5,1.5,1.5])
            
            # stone gathering
            SpecialClick(['I','I'], [1.5,1.5])
            pyautogui.moveTo(522,768)
            pyautogui.dragTo(70,768,duration = 1)
            SpecialClick(["N","F","G","1","2","E"], [1.5,1.5,2.5,1.5,1.5,1.5])
            
            # iron gathering
            SpecialClick(['I','I'], [1.5,1.5])
            pyautogui.moveTo(522,768)
            pyautogui.dragTo(70,768,duration = 1)
            SpecialClick(["L","F","G","1","2","E","s"], [1.5,1.5,2.5,1.5,1.5,1.5,1.5])
            
            # SpecialClick(['I','I'], [1.5,1.5])
            # pyautogui.moveTo(522,768)
            # pyautogui.dragTo(70,768,duration = 1)
            # SpecialClick(["N","F","G","6","E","s"], [1.5,1.5,2.5,1.5,1.5,3])

            SpecialClick(['I','I'], [1.5,1.5])
            pyautogui.moveTo(522,768)
            pyautogui.dragTo(10,768,duration = 1)
            SpecialClick(["L","F","G","6","E","s"], [1.5,1.5,2.5,1.5,1.5,3])

            logging.info(f"finished sending army")
        if Farm_activated:
            match_and_handle(screen_gray, templates["marchqueue"], 0.9, on_marchqueue)
        
        # start to do rally
        if Rally_activated:
            def on_rally(x, y):
                time.sleep(1)
                pyautogui.moveTo(x, y)
                time.sleep(1)
                pyautogui.moveTo(10,10)
                SpecialClick(['I','I'], [1.5,1.5])
                pyautogui.moveTo(70,768)
                pyautogui.dragTo(522,768,duration = 1)
                SpecialClick(["o","f","9","u","7","e"], [1.5,2.5,1.5,1.5,1.5,1.5])
                logging.info(f"Clicked on rally ({x}, {y})")
            match_and_handle(screen_gray, templates["rally"], 0.7, on_rally,region=(108, 543, 280, 638))

        # start to do rally 2
        if Rally_activated2:
            def on_rally2(x, y):
                time.sleep(1)
                pyautogui.moveTo(x, y)
                time.sleep(1)
                pyautogui.moveTo(10,10)
                SpecialClick(['I','I'], [1.5,1.5])
                pyautogui.moveTo(70,768)
                pyautogui.dragTo(522,768,duration = 1)
                SpecialClick(["o","f","9","u","8","e"], [1.5,2.5,1.5,1.5,1.5,1.5])
                logging.info(f"Clicked on rally2 ({x}, {y})")
            match_and_handle(screen_gray, templates["rally2"], 0.8, on_rally2,region=(108, 581, 280, 639))
        #Go to town page
        delay = [0.5,2]
        key =["S","5"]
        SpecialClick(key,delay) 
        time.sleep(2)

        screen_gray = grab_screen_gray()

        # Perform template online for cavalry inf archer
        def on_completed(x, y):
            logging.info(f"Clicked on completed ({x}, {y})")
            time.sleep(3)
            pyautogui.click(x, y)
            pyautogui.moveTo(10,10)
            time.sleep(3)
            if windows[window_index].title == "wosmin" or windows[window_index].title == "WOSMIN":
                SpecialClick(["9","g","p","9","9","t","esc","s"], [3,1.5,1.5,1.5,1.5,1.5,1.5,3])
            else:
                SpecialClick(["9","g","a","9","9","t","esc","s"], [3,1.5,1.5,1.5,1.5,1.5,1.5,3])

        if match_and_handle(screen_gray, templates["completed"], 0.8, on_completed):
            continue

        # peform template matching for idle
        def on_idle(x, y):
            logging.info(f"Clicked on idle ({x}, {y})")
            time.sleep(3)
            pyautogui.click(x, y)
            pyautogui.moveTo(10,10)
            time.sleep(3)
            SpecialClick(["9","g","a","9","9","t","esc","s"], [3,1.5,1.5,1.5,1.5,1.5,1.5,3])
        if match_and_handle(screen_gray, templates["idle"], 0.8, on_idle, region=(129, 300, 294, 468) if windows[window_index].title == "wosmin" else (67, 459, 351, 646)):
            continue

        # check for conquest here
        def on_conquest(x, y):
            time.sleep(3)
            pyautogui.click(x, y)
            pyautogui.moveTo(10,10)
            time.sleep(3)
            # click on conquest 1
            screen_gray2 = grab_screen_gray()
            if match_and_handle(screen_gray2, templates["conquest1"], 0.9, lambda x2, y2: (pyautogui.click(x2, y2), pyautogui.moveTo(10,10), logging.info(f"Clicked on conquest1 ({x2}, {y2})"), time.sleep(3))):
                screen_gray2 = grab_screen_gray()
                match_and_handle(screen_gray2, templates["conquest2"], 0.9, lambda x2, y2: (pyautogui.click(x2, y2), pyautogui.moveTo(10,10), logging.info(f"Clicked on conquest2 ({x2}, {y2})"), time.sleep(3)))
                SpecialClick(["s","esc"], [1,1])
                time.sleep(3)
            logging.info(f"Clicked on conquest ({x}, {y})")
        # Limit conquest match to rectangle (58,990)-(104,1030)
        if match_and_handle(screen_gray, templates["conquest"], 0.8, on_conquest, region=(68, 946, 90, 966)):
            continue

        #check for online gift here
        delay = [0.5,2]
        key =["S","5"]
        SpecialClick(key,delay) 
        time.sleep(2)

        pyautogui.moveTo(201,694)
        pyautogui.dragTo(201,60,duration = 1)

        time.sleep(2)

        screen_gray = grab_screen_gray()

        # Perform template online for online
        def on_online(x, y):
            pyautogui.click(x, y)
            pyautogui.moveTo(10,10)
            SpecialClick(["s","s"], [1,1])
            logging.info(f"Clicked on online ({x}, {y})")
        if match_and_handle(screen_gray, templates["online"], 0.85, on_online):
            continue

        # Perform template fountain for online
        def on_fountain(x, y):
            pyautogui.click(x, y)
            pyautogui.moveTo(10,10)
            SpecialClick(["9","L","home"], [1,1,1])
            logging.info(f"Clicked on fountain ({x}, {y})")
        if match_and_handle(screen_gray, templates["fountain"], 0.85, on_fountain):
            continue

        # Perform template matching for heroadvance            
        def on_heroadvance(x, y):
            pyautogui.click(x, y)
            pyautogui.click(x, y)
            pyautogui.moveTo(10,10)
            logging.info(f"Clicked on advance hero ({x}, {y})")
            time.sleep(3)
            # recruit hero
            screen_gray2 = grab_screen_gray()
            def on_free(x2, y2):
                pyautogui.click(x2, y2)
                pyautogui.moveTo(10,10)
                time.sleep(3)
                SpecialClick(["s","esc","esc","s"], [3,3,3,3])
                logging.info(f"free recruit ({x2}, {y2})")
                time.sleep(3)
            match_and_handle(screen_gray2, templates["free"], 0.85, on_free)
        if match_and_handle(screen_gray, templates["heroadvance"], 0.75, on_heroadvance, region=(62, 296, 300, 532)):
            continue
 
        # Perform template matching for contribution
        def on_contribution(x, y):
            time.sleep(3)
            pyautogui.click(x, y)
            pyautogui.moveTo(10,10)
            logging.info(f"contribution  ({x}, {y})")
            time.sleep(3)
            SpecialClick(["e","n","esc","n"], [3,3,3,3])
            screen_gray2 = grab_screen_gray()
            def on_good(x2, y2):
                pyautogui.click(x2, y2)
                pyautogui.moveTo(10,10)
                time.sleep(3)
                SpecialClick(["h"]*24 + ["esc"]*3 + ["s"], [1]*24 + [3]*4)
                logging.info(f"Clicked on good ({x2}, {y2}) 25 time")
                time.sleep(3)
            match_and_handle(screen_gray2, templates["good"], 0.8, on_good)
        if match_and_handle(screen_gray, templates["contribution"], 0.85, on_contribution):
            continue

        # Check if killswitch is activated after processing each image
        if killswitch_activated:
            break

        if (window_index == 0):
            window_index = 1
        else:
            window_index = 0
        time.sleep(10)        

# Function to search for images on the screen and click on them if found
def search_and_click(images, threshold=0.95, click_delay=6, killswitch_key='q'):
    # Set the template matching method
    global screenshot
    method = cv2.TM_CCOEFF_NORMED

    # Start monitoring the killswitch key in a separate thread
    killswitch_thread = threading.Thread(target=monitor_killswitch, args=(killswitch_key,))
    killswitch_thread.start()

    farm_thread = threading.Thread(target=monitor_marchqueue, args=(30,))
    farm_thread.start()


def SpecialClick(keypress, delay):
    """
    Press a sequence of keys with specified delays, with boundary/safety checks.
    Uses safe_press to ensure window activation and proper error handling.
    """
    # Wait before starting keypresses to allow for window focus
    time.sleep(1)
  
    for key, delayclick in zip(keypress, delay):
        time.sleep(delayclick)
        safe_press(key)

# Main function to execute the script
def main():
    # List of image paths to search for on the screen
    # Replace these with the paths to your actual images
    base_dir = os.path.join(os.path.dirname(__file__), 'gameplay')
    image_paths = [
        os.path.join(base_dir, "help.png"),    
    ]

    # Call the function with the list of image paths and optional parameters
    search_and_click(image_paths)

# Entry point of the script
if __name__ == "__main__":
    main()
