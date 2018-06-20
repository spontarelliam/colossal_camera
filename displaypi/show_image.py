#!/usr/bin/env python3
# The purpose of this program is to allow asynchronous operation of the camerapi and displaypi
# It checks an image directory for new images and displays them if they're believed to be new
# Then after a delay it will display the existing mosaic image until a new picture appears.

import cv2
import os, sys
import time
import datetime

image_dir = "/home/pi/Pictures/"
logfile = "/home/pi/colossal_camera/displaypi/display.log"
lastfile=''
start_time = time.time() -5
newfile = False

def check_log(filename):
    with open(logfile, "r") as f:
        lines = f.readlines()
        for line in lines:
            if filename == line.strip():
                return 1
    return 0

def add_log(filename):
    with open(logfile, "a") as f:
        f.writelines(filename+"\n")

while True:
    files = os.listdir(image_dir)
    if sorted(files)[-1] != lastfile: # give file time to fully transfer
        time.sleep(1)
    lastfile = sorted(files)[-1]

    if time.time() > (start_time + 5):
        print(time.time())
        start_time = time.time()
        
        for filename in sorted(files):
            if not check_log(filename):
                print("file not in log")
                print(filename)
                newfile = True
                add_log(filename)
                img = cv2.imread(image_dir + filename)
                cv2.destroyWindow("mosaic")
                cv2.namedWindow("photo", cv2.WND_PROP_FULLSCREEN)
                cv2.setWindowProperty("photo",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
                cv2.imshow("photo", img)
                cv2.waitKey(1000)
                break
            newfile = False

        if not newfile:
            print("mosaic")
            mosaic = cv2.imread("dj_ed-mosaic_20.jpg")
            cv2.destroyWindow("photo")
            cv2.namedWindow("mosaic", cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty("mosaic",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
            cv2.imshow("mosaic", mosaic)
            cv2.waitKey(1000)
