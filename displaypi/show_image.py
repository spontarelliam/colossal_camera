#!/usr/bin/env python3
# The purpose of this program is to allow asynchronous operation of the camerapi and displaypi
# It checks an image directory for new images and displays them if they're believed to be new
# Then after a delay it will display the existing mosaic image until a new picture appears.


import cv2
import os, sys
import time
import datetime

day_of_year = datetime.datetime.now().timetuple().tm_yday
image_dir = os.path.join("/home/pi/Pictures/", str(day_of_year))
mosaic_file = os.path.join("/home/pi/Pictures/", str(day_of_year), 'mosaic.jpg')

logfile = "/home/pi/colossal_camera/displaypi/display.log"
lastfile=''
start_time = time.time() -5
newfile = False
firstrun = True


def check_log(filename):
    """
    check if file already in log
    """
    with open(logfile, "r") as f:
        lines = f.readlines()
        for line in lines:
            if filename == line.strip():
                return 1
    return 0

def add_log(filename):
    with open(logfile, "a") as f:
        f.writelines(filename+"\n")

def check_file(filename):
    """
    Ensure that file has completed transfer by checking its size
    multiple times.
    """
    filesize=os.path.getsize(os.path.join(image_dir, filename))
    for i in range(10):
        if filesize == os.path.getsize(os.path.join(image_dir, filename)):
            print('filesize unchanged')
            return 1
        else:
            time.sleep(1)
    return 0
    

def main():
    """
    walk through all files in image_dir
    check if image has already been shown, if not, show it.
    if there are no new images to show, show the mosaic
    """
    
    if not os.path.exists(mosaic_file):
        print("{} mosaic image does not exist".format(mosaic_file))
        sys.exit()
                                 
    while True:
        if time.time() > (start_time + 7):
            print(time.time())
            start_time = time.time()
            files = os.listdir(image_dir)
            for filename in sorted(files):
                if not check_log(filename):
                    print("{} not in log".format(filename))
                    if not check_file(filename):
                        continue
                    newfile = True
                    add_log(filename)
                    img = cv2.imread(os.path.join(image_dir, filename))
    
                    cv2.namedWindow("photo", cv2.WND_PROP_FULLSCREEN)
                    cv2.setWindowProperty("photo",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
                    cv2.imshow("photo", img)
                    cv2.waitKey(1000)
                    cv2.destroyWindow("mosaic")
                    break
                newfile = False
    
            if not newfile:
                print("mosaic")
                mosaic = cv2.imread(mosaic_file)
                cv2.namedWindow("mosaic", cv2.WND_PROP_FULLSCREEN)
                cv2.setWindowProperty("mosaic",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
                cv2.imshow("mosaic", mosaic)
                cv2.waitKey(1000)
                cv2.destroyWindow("photo")
                start_time = start_time - 3
                if firstrun:
                    cv2.destroyWindow("mosaic")
                    firstrun = False

if __name__ == "__main__":
    main()
