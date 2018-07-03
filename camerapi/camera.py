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
day_of_year = str(datetime.datetime.now().timetuple().tm_yday)
working_dir = os.path.join('/home/pi/Pictures', day_of_year)

GPIO.setmode(GPIO.BCM)
statusLED = 26
flashLED = 19
camera = PiCamera()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.load_host_keys(os.path.expanduser(os.path.join("/home/pi", ".ssh", "known_hosts")))


def take_pic():
    print("taking picture")
    camera.rotation = 180
    filename = 'Cheers-'+datetime.datetime.now().strftime("%y-%m-%d-%s")+'.jpg'
    GPIO.output(flashLED, 1)
    camera.capture(os.path.join(working_dir, filename))
    logfile.writelines("picture taken\n")
    GPIO.output(flashLED, 0)
    return filename

    
def send_pic(filename):
    print("sending picture")
    try:
        sftp = ssh.open_sftp()
        sftp.put(os.path.join(working_dir,filename), os.path.join(working_dir,filename))
        sftp.put('/home/pi/camera.log', '/home/pi/camera.log')
        sftp.close()
        print(filename+" was sent!")
        logfile.writelines("picture sent\n")
    except:
        print("failed to send. red led")

        
def main():

    GPIO.setup(flashLED, GPIO.OUT, initial=0)
    
    print("starting camera")
    logfile.writelines("camera started at {}\n".format(datetime.datetime.now()))
    button=18

    try:
        # dns not working
        # ssh.connect("displaypi", username="pi", password="cheers2018")
        ssh.connect("192.168.4.1", username="pi", password="cheers2018")
        print("connected")
        logfile.writelines("connected to displaypi\n")
    except paramiko.SSHException:
        print("Connection to displaypi Failed")
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    try:
        while True:
            print("waiting for button press")
            GPIO.wait_for_edge(button, GPIO.FALLING)
            logfile.writelines("button pressed\n")
            filename = take_pic()
            send_pic(filename)
    except KeyboardInterrupt:
        GPIO.output(statusLED, 0)
        GPIO.cleanup()
        ssh.close()
        logfile.close()

    GPIO.output(statusLED, 0)
    GPIO.cleanup()


if __name__ == "__main__":
    try:
        GPIO.setup(statusLED, GPIO.OUT, initial=1)
        main()
    except Exception as e:
        print(e)
        logfile.writelines(e)
        GPIO.output(statusLED, 0)
        GPIO.output(flashLED, 0)
        GPIO.cleanup()
        ssh.close()
        logfile.close()
        
