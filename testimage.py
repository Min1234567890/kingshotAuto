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
import pygetwindow as gw

windows = gw.getWindowsWithTitle('wosmin') + gw.getWindowsWithTitle('WOSMIN')
window_index = 0  # Index of the window to activate
# Set up logging
logging.basicConfig(filename='test.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')

# Function to search for images on the screen and click on them if found
def search_and_click(images, threshold=0.8, click_delay=6, killswitch_key='q'):
    # Set the template matching method
    global screenshot
    method = cv2.TM_CCOEFF_NORMED

    while 1:
        #minimize_cmd_window()  # Minimize the command prompt window

        # Capture the screen image
        screenshot = pyautogui.screenshot()
        screenshot = screenshot.crop((0, 0, 560, 1000))
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
            #logging.info(f"'{image_path}'  '{result}'")
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
            

        time.sleep(1)

    logging.info("Exiting the loop.")

# Main function to execute the script
def main():
    # List of image paths to search for on the screen
    # Replace these with the paths to your actual images
    image_paths = [
        #r"C:\Users\LENOVO\Pictures\Screenshots\help.png",
        #r"C:\Users\LENOVO\Pictures\Screenshots\store.png",
        #r"C:\Users\LENOVO\Pictures\Screenshots\quitchat.png",
        #r"C:\Users\LENOVO\Pictures\Screenshots\shopquit.png",
        #r"C:\Users\LENOVO\Pictures\Screenshots\next.png",
        #r"C:\Users\LENOVO\Pictures\Screenshots\meat2.png",
        #r"C:\Users\LENOVO\Pictures\Screenshots\claim.png",
        r"C:\Users\LENOVO\Pictures\Screenshots\completed.png",
        #r"C:\Users\LENOVO\Pictures\Screenshots\backpack.png",
        #r"C:\Users\LENOVO\Pictures\Screenshots\contribution.png",

        # Add more image paths as needed
    ]
    # Call the function with the list of image paths and optional parameters
    #search_and_click(image_paths)
    SpecialClick(['I','I'], [1.5,1.5])
    pyautogui.moveTo(522,768)
    pyautogui.dragTo(70,768,duration = 1)
    SpecialClick(['B','F','G','1','2','E'], [1.5,1.5,2.5,1.5,1.5,1.5])

def SpecialClick(keypress,delay):
    global window_index
    if windows:
        try:
            windows[window_index].activate()
        except Exception:
            print("Ok")
        time.sleep(1)
  
        for key,delayclick in zip(keypress,delay):
            time.sleep(delayclick)
            pyautogui.press(key)



# Entry point of the script
if __name__ == "__main__":
    main()