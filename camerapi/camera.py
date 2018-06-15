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

GPIO.setmode(GPIO.BCM)
camera = PiCamera()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))

def take_pic():
    print("taking picture")
    camera.rotation = 180
    filename = 'Cheers-'+datetime.datetime.now().strftime("%y-%m-%d-%s")+'.jpg'
    camera.capture('/home/pi/Pictures/'+filename)
    return filename

    
def send_pic(filename):
    print("sending picture")
    try:
        sftp = ssh.open_sftp()
        sftp.put('/home/pi/Pictures/'+filename, '/home/pi/Pictures/'+filename)
        print("Sent!")
        sftp.close()
    except:
        print("failed to send. red led")

        
def main():
    button=18


    try:
        ssh.connect("displaypi", username="pi", password="cheers2018")
        print("connected")
    except paramiko.SSHException:
        print("Connection to displaypi Failed")
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    try:
        while True:
            print("waiting for button press")
            GPIO.wait_for_edge(button, GPIO.FALLING)
            filename = take_pic()
            send_pic(filename)
    except KeyboardInterrupt:
        GPIO.cleanup()
        ssh.close()
    GPIO.cleanup()


if __name__ == "__main__":
    main()
