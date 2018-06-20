#!/usr/bin/env python
import cv2
import os, sys
import time
lastfile=''
while True:
    files = os.listdir("/home/pi/Pictures/")
    if sorted(files)[-1] != lastfile: # give file time to fully transfer
        time.sleep(1)
    lastfile = sorted(files)[-1]
    print(lastfile)
    img = cv2.imread("/home/pi/Pictures/"+lastfile)
    cv2.imshow('img',img)
    cv2.waitKey(1)
cv2.destroyAllWindows()
