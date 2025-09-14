# | Made by 2cz5 | https://github.com/2cz5 | Discord:2cz5 (for questions etc..)

import cv2
import numpy as np
import pyautogui
import threading
import time
import win32gui
import win32con
import keyboard
import os
import logging

# Global variable to indicate if the killswitch is activated
killswitch_activated = False
screenshot = pyautogui.screenshot()
windows = pyautogui.getWindowsWithTitle("wosmin")
Gathering_activated = False
army_activated = False
window_index = 0
#windows1 = pyautogui.getWindowsWithTitle("BlueStacks App Player1")
1

# Set up logging
logging.basicConfig(filename='clicker.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')

# Function to minimize the command prompt window (Windows-specific)
def minimize_cmd_window():
    try:
        # Find the command prompt window by its class name
        hwnd = win32gui.FindWindow("ConsoleWindowClass", None)
        if hwnd != 0:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
    except Exception as e:
        logging.error(f"Error minimizing command prompt window: {e}")

# Function to monitor the killswitch key
def monitor_killswitch(killswitch_key):
    global killswitch_activated
    while True:
        if keyboard.is_pressed(killswitch_key):
            logging.info("Killswitch activated.")
            killswitch_activated = True
            break
        time.sleep(0.1)

# Function to monitor the marchqueue empty
def monitor_marchqueue(click_delay):
    global killswitch_activated
    global windows
    global Gathering_activated
    global army_activated
    global window_index
    method = cv2.TM_CCOEFF_NORMED
    template = cv2.imread(r"C:\Users\LENOVO\Pictures\Screenshots\marchqueue.png", cv2.IMREAD_GRAYSCALE)
    templateonline = cv2.imread(r"C:\Users\LENOVO\Pictures\Screenshots\online.png", cv2.IMREAD_GRAYSCALE) 
    templatec = cv2.imread(r"C:\Users\LENOVO\Pictures\Screenshots\completed.png", cv2.IMREAD_GRAYSCALE)
    templatera = cv2.imread(r"C:\Users\LENOVO\Pictures\Screenshots\heroadvance.png", cv2.IMREAD_GRAYSCALE)  
    templatecontri = cv2.imread(r"C:\Users\LENOVO\Pictures\Screenshots\contribution.png", cv2.IMREAD_GRAYSCALE) 
    templategood = cv2.imread(r"C:\Users\LENOVO\Pictures\Screenshots\good.png", cv2.IMREAD_GRAYSCALE) 
    templatefree = cv2.imread(r"C:\Users\LENOVO\Pictures\Screenshots\free.png", cv2.IMREAD_GRAYSCALE) 

    window_index = 0    
    while True:
        if windows:
            try:
                windows[window_index].activate()
            except:
                print("Ok")

        time.sleep(3)

        #open wilderness
        delay = [1,3]
        key=["S","1"]
        SpecialClick(key,delay)        

        screenshot = pyautogui.screenshot()
        screenshot = screenshot.crop((0, 0, 622, 1080))
        screen_np = np.array(screenshot)
        screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)

        # Perform template matching for marching
        result = cv2.matchTemplate(screen_gray, template, method)
        # Get the location of matches above the specified threshold
        loc = np.where(result >= 0.9)
         # Click on the matched locations
        if loc[0].size > 0:
            Gathering_activated = True
            time.sleep(3)
            # additonal bread gathering
            #delay = [1.5,1.5,1.5,1.5,1.5,2.5,1.5,1.5]
            #key = ["I","left","left","O","F","G","6","E"]
            #SpecialClick(key,delay)

            # bread gathering
            delay = [1.5,1.5,1.5,1.5,1.5,2.5,1.5,1.5,1.5]
            key = ["I","left","left","B","F","G","1","2","E"]
            SpecialClick(key,delay)        

            # wood gathering
            delay = [1.5,1.5,1.5,1.5,1.5,2.5,1.5,1.5,1.5]
            key = ["I","left","left","O","F","G","1","2","E"]
            SpecialClick(key,delay)        

            # stone gathering
            delay = [1.5,1.5,1.5,1.5,1.5,2.5,1.5,1.5,1.5]
            key = ["I","left","left","N","F","G","1","2","E"]
            SpecialClick(key,delay)        

            # iron gathering
            delay = [1.5,1.5,1.5,1.5,1.5,2.5,1.5,1.5,1.5]
            key = ["I","left","left","L","F","G","1","2","E"]
            SpecialClick(key,delay)

            if windows[window_index].title == "wosmin":
                delay = [1.5,1.5,1.5,1.5,1.5,2.5,1.5,1.5,3]
                key = ["I","left","left","L","F","G","6","E","s"]
                SpecialClick(key,delay)
            
            logging.info(f"finished sending army")
            Gathering_activated = False        
        
        #Go to town page       
        delay = [0.5,2]
        key =["S","5"]
        SpecialClick(key,delay) 
        time.sleep(2)

        screenshot = pyautogui.screenshot()
        screenshot = screenshot.crop((0, 0, 622, 1080))
        screen_np = np.array(screenshot)
        screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)

        # Perform template online for cavalry inf archer
        result = cv2.matchTemplate(screen_gray, templatec, method)
        # Get the location of matches above the specified threshold
        loc = np.where(result >= 0.7)
         # Click on the matched locations
        if loc[0].size > 0:
            Gathering_activated = True
            time.sleep(3)
            for pt in zip(*loc[::-1]):
                # Calculate the center of the matched template
                x, y = pt[0] + templatec.shape[1] // 2, pt[1] + templatec.shape[0] // 2
                # Click on the center of the matched template
                pyautogui.click(x, y)
                pyautogui.moveTo(10,10)
                time.sleep(3)
                break
            delay = [3,1.5,1.5,1.5,1.5,1.5,1.5,3]
            key = ["9","g","a","s","s","t","esc","s"]
            SpecialClick(key,delay)
            Gathering_activated = False 
            continue

        #check for online gift here        
        delay = [0.5,2]
        key =["S","5"]
        SpecialClick(key,delay) 
        time.sleep(2)

        pyautogui.moveTo(201,694)
        pyautogui.dragTo(201,286,duration = 1)

        time.sleep(2)

        screenshot = pyautogui.screenshot()
        screenshot = screenshot.crop((0, 0, 622, 1080))
        screen_np = np.array(screenshot)
        screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)

        # Perform template online for online
        result = cv2.matchTemplate(screen_gray, templateonline, method)
        # Get the location of matches above the specified threshold
        loc = np.where(result >= 0.85)
         # Click on the matched locations
        if loc[0].size > 0:
            Gathering_activated = True
            for pt in zip(*loc[::-1]):
                # Calculate the center of the matched template
                x, y = pt[0] + templateonline.shape[1] // 2, pt[1] + templateonline.shape[0] // 2
                # Click on the center of the matched template
                pyautogui.click(x, y)
                pyautogui.moveTo(10,10)
                break
                # exit online claim
            delay =[1,1]
            key = ["s","s"]
            SpecialClick(key,delay)
            logging.info(f"Clicked on online ({x}, {y})")
            Gathering_activated = False
            continue

        # Perform template matching for hero advance
        result = cv2.matchTemplate(screen_gray, templatera, method)
        # Get the location of matches above the specified threshold
        loc = np.where(result >= 0.75)
        # Click on the matched locations
        if loc[0].size > 0:
            Gathering_activated = True
            for pt in zip(*loc[::-1]):
                # Calculate the center of the matched template
                x, y = pt[0] + templatera.shape[1] // 2, pt[1] + templatera.shape[0] // 2
                # Click on the center of the matched template
                pyautogui.click(x, y)
                pyautogui.moveTo(10,10)
                logging.info(f"Clicked on advance hero ({x}, {y})")
                time.sleep(3)
                break
            
            # recurit hero
            screenshot = pyautogui.screenshot()
            screenshot = screenshot.crop((0, 0, 622, 1080))
            screen_np = np.array(screenshot)
            screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
            result = cv2.matchTemplate(screen_gray, templatefree, method)
            loc = np.where(result >= 0.85)
            # Click on the matched locations
            if loc[0].size > 0:
                time.sleep(3)
                for pt in zip(*loc[::-1]):
                    # Calculate the center of the matched template
                    x, y = pt[0] + templatefree.shape[1], pt[1] + templatefree.shape[0]
                    # Click on the center of the matched template
                    pyautogui.click(x, y)
                    pyautogui.moveTo(10,10)
                    time.sleep(3)
                    break
                
                delay = [3,3,3,3]
                key = ["s","esc","esc","s"]
                SpecialClick(key,delay)        
                    
                logging.info(f"free recuilt ({x}, {y})")
                time.sleep(3)
            Gathering_activated = False
            continue
        
        # Perform template matching for contribution
        result = cv2.matchTemplate(screen_gray, templatecontri, method)
        # Get the location of matches above the specified threshold
        loc = np.where(result >= 0.85)
        # Click on the matched locations
        if loc[0].size > 0:
            Gathering_activated = True
            time.sleep(3)
            for pt in zip(*loc[::-1]):
                # Calculate the center of the matched template
                x, y = pt[0] + templatecontri.shape[1]//2, pt[1] + templatecontri.shape[0] // 2

                # Click on the center of the matched template
                pyautogui.click(x, y)
                pyautogui.moveTo(10,10)
                logging.info(f"contribution  ({x}, {y})")
                time.sleep(3)
                break
            # recurit hero
            delay = [3,3,3,3]
            key = ["e","n","esc","n"]
            SpecialClick(key,delay)        

            screenshot = pyautogui.screenshot()
            screenshot = screenshot.crop((0, 0, 622, 1080))
            screen_np = np.array(screenshot)
            screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
            result = cv2.matchTemplate(screen_gray, templategood, method)
            loc = np.where(result >= 0.85)
            # Click on the matched locations
            if loc[0].size > 0:
                time.sleep(3)
                for pt in zip(*loc[::-1]):
                    # Calculate the center of the matched template
                    x, y = pt[0] + templategood.shape[1], pt[1] + templategood.shape[0]
                    # Click on the center of the matched template
                    pyautogui.click(x, y)
                    pyautogui.moveTo(10,10)
                    time.sleep(3)
                    delay = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,3,3,3]
                    key = ["h","h","h","h","h","h","h","h","h","h","h","h","h","h","h","h","h","h","h","h","h","h","h","h","esc","esc","esc","s"]
                    SpecialClick(key,delay)        
                    logging.info(f"Clicked on good ({x}, {y}) 25 time")
                    time.sleep(3)
                    break
            Gathering_activated = False
            continue

        # Check if killswitch is activated after processing each image
        if killswitch_activated:
            break

        Gathering_activated = False    
        if (window_index == 0):
            window_index = 1
        else:
            window_index = 0
        time.sleep(30)        

# Function to search for images on the screen and click on them if found
def search_and_click(images, threshold=0.95, click_delay=6, killswitch_key='q'):
    # Set the template matching method
    global screenshot
    global Gathering_activated
    method = cv2.TM_CCOEFF_NORMED

    # Start monitoring the killswitch key in a separate thread
    killswitch_thread = threading.Thread(target=monitor_killswitch, args=(killswitch_key,))
    killswitch_thread.start()

    farm_thread = threading.Thread(target=monitor_marchqueue, args=(30,))
    farm_thread.start()

    while not killswitch_activated:
        #minimize_cmd_window()  # Minimize the command prompt window

        # if at gathering then don't check for any images for clicking
        if Gathering_activated == True:
            #logging.info(f"gathering_activated true")
            # Check if killswitch is activated after processing each image
            if killswitch_activated:
                break
            continue

        # Capture the screen image
        screenshot = pyautogui.screenshot()
        screenshot = screenshot.crop((0, 0, 622, 1080))
        screen_np = np.array(screenshot)
        screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)


        # Iterate through each image in the database
        for image_path in images:
            if not os.path.exists(image_path):
                logging.error(f"Image not found at '{image_path}'")
                continue  # Skip to the next image if the file doesn't exist

            # Load the image from the database
            template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

            # Perform template matching
            result = cv2.matchTemplate(screen_gray, template, method)

            # Get the location of matches above the specified threshold
            loc = np.where(result >= threshold)

            # Click on the matched locations
            if loc[0].size > 0:
                for pt in zip(*loc[::-1]):
                    # Calculate the center of the matched template
                    x, y = pt[0] + template.shape[1] // 2, pt[1] + template.shape[0] // 2

                    # Click on the center of the matched template
                    pyautogui.click(x, y)
                    pyautogui.moveTo(10,10)
                    if "help" in str(image_path):
                        time.sleep(0.1)
                    else:
                        logging.info(f"Clicked on {image_path} at ({x}, {y})")
                    continue
            time.sleep(1)  # Delay between clicks            
            
            # Check if killswitch is activated after processing each image
            if killswitch_activated:
                break

        # Check if killswitch is activated after processing all images
        if killswitch_activated:
            break

        time.sleep(1)

    logging.info("Exiting the loop.")

def SpecialClick(keypress,delay):
    global window_index
    if windows:
        try:
            windows[window_index].activate()
        except:
            print("Ok")
        
        time.sleep(3)
        for key,delayclick in zip(keypress,delay):
            time.sleep(delayclick)
            pyautogui.press(key)

# Main function to execute the script
def main():
    # List of image paths to search for on the screen
    # Replace these with the paths to your actual images
    image_paths = [
        r"C:\Users\LENOVO\Pictures\Screenshots\help.png",
        r"C:\Users\LENOVO\Pictures\Screenshots\quitchat.png",
        r"C:\Users\LENOVO\Pictures\Screenshots\shopquit.png",
        r"C:\Users\LENOVO\Pictures\Screenshots\alliance.png",
        r"C:\Users\LENOVO\Pictures\Screenshots\backpack.png",
        r"C:\Users\LENOVO\Pictures\Screenshots\world.png",

        # Add more image paths as needed
    ]


 


    # Call the function with the list of image paths and optional parameters
    search_and_click(image_paths)

# Entry point of the script
if __name__ == "__main__":
    main()
