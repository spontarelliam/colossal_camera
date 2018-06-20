#!/usr/bin/env python3
# The purpose of this program is to allow asynchronous operation of the camerapi and displaypi
# It checks an image directory for new images and displays them if they're believed to be new
# Then after a delay it will display the existing mosaic image until a new picture appears.

import cv2
import os, sys
import time

image_dir = "/home/pi/Pictures/"
logfile = "/home/pi/colossal_camera/displaypi/display.log"

def check_log(filename):
    with open(logfile, "r") as f:
        lines = f.readlines()
        for line in lines:
            if filename == line.strip():
                return 1
    return 0

def add_log(filename):
    with open(logfile, "a") as f:
        f.writelines(filename)


lastfile=''
while True:
    files = os.listdir(image_dir)
    if sorted(files)[-1] != lastfile: # give file time to fully transfer
        time.sleep(1)
    lastfile = sorted(files)[-1]

    print(lastfile)

    if not check_log(lastfile):
        print("file not in log")
        add_log(lastfile)
        cv2.setWindowProperty("picture",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
        cv2.imshow("picture", image_dir+lastfile)
        cv2.waitKey(5000)
        cv2.destroyAllWindows()
        # cvSetWindowProperty("main_win", CV_WINDOW_FULLSCREEN, CV_WINDOW_FULLSCREEN);
    else:
        cv2.imshow("mosaic", "mosaic.jpg")
        cv2.waitKey(5000)
        cv2.destroyAllWindows()
