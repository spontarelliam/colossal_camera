#!/usr/bin/env python3
# CameraPi
# Takes photo on button press, sends image to DisplayPi
# Adam Spontarelli
# May 2018

from picamera import PiCamera
import time
import RPi.GPIO as GPIO
import os
import paramiko
import datetime

logfile = open("/home/pi/camera.log","a")

GPIO.setmode(GPIO.BCM)
camera = PiCamera()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.load_host_keys(os.path.expanduser(os.path.join("/home/pi", ".ssh", "known_hosts")))

def take_pic():
    print("taking picture")
    camera.rotation = 180
    filename = 'Cheers-'+datetime.datetime.now().strftime("%y-%m-%d-%s")+'.jpg'
    camera.capture('/home/pi/Pictures/'+filename)
    logfile.writelines("picture taken")
    return filename

    
def send_pic(filename):
    print("sending picture")
    try:
        sftp = ssh.open_sftp()
        sftp.put('/home/pi/Pictures/'+filename, '/home/pi/Pictures/'+filename)
        sftp.put('/home/pi/camera.log', '/home/pi/camera.log')
        sftp.close()
        print(filename+" was sent!")
        logfile.writelines("picture sent")
    except:
        print("failed to send. red led")

        
def main():
    print("starting camera")
    logfile.writelines("camera started")
    button=18

    try:
        # dns not working
        # ssh.connect("displaypi", username="pi", password="cheers2018")
        ssh.connect("192.168.4.1", username="pi", password="cheers2018")
        print("connected")
        logfile.writelines("connected to displaypi")
    except paramiko.SSHException:
        print("Connection to displaypi Failed")
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    try:
        while True:
            print("waiting for button press")
            GPIO.wait_for_edge(button, GPIO.FALLING)
            logfile.writelines("button pressed")
            filename = take_pic()
            send_pic(filename)
    except KeyboardInterrupt:
        GPIO.cleanup()
        ssh.close()
        logfile.close()
    GPIO.cleanup()


if __name__ == "__main__":
    main()
