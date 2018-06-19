#!/usr/bin/env python
# search picture direction
# if new image appears, display for 5 seconds
# Then put that image in the mosaic
# then display the mosaic until new image
import cv2
import os


def check_log(filename):
    with open("display.log", "r") as f:
        lines = f.readlines()
        for line in lines:
            if filename == line.strip():
                return 1
    return 0



while True:
    for dirpath, dnames, fnames in os.walk("~/Pictures"):
        for f in fnames:
            if f.endswith(".jpg"):
                if not check_log(f):
                    print("file not in log")
                    cv2.imshow("picure", "~/Pictures/"+f)
                    cv2.waitKey(5000)
                    cv2.destroyAllWindows()
                    # cvSetWindowProperty("main_win", CV_WINDOW_FULLSCREEN, CV_WINDOW_FULLSCREEN);
                else:
                    cv2.imshow("mosaic", "mosaic.jpg")
                    cv2.waitKey(5000)
                    cv2.destroyAllWindows()
