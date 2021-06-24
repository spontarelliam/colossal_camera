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
day_of_year = str(datetime.datetime.today().year) + "_" + str(datetime.datetime.now().timetuple().tm_yday)
working_dir = os.path.join('/home/pi/Pictures', day_of_year)

GPIO.setmode(GPIO.BCM)
statusLED = 26
flashLED = 19
button= 23
camera = PiCamera()
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.load_host_keys(os.path.expanduser(os.path.join("/home/pi", ".ssh", "known_hosts")))

def get_date():
    """
    Get time from displaypi as it has a RTC.
    """
    (si,so,se) = ssh.exec_command('date +%Y%m%d')
    readList = so.readlines()
    print(readList)
    os.system("date +%Y%m%d -s "+ readList[0])

def prep_directory():
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
	
    # make dir remotely
    sftp = ssh.open_sftp()
    try:
        sftp.stat(working_dir)
    except FileNotFoundError:
        sftp.mkdir(working_dir)
    sftp.close()

def take_pic():
    print("taking picture")
    camera.rotation = 180
    filename = 'Cheers-'+datetime.datetime.now().strftime("%y-%m-%d-%s")+'.jpg'
    GPIO.output(flashLED, 1)
    camera.capture(os.path.join(working_dir, filename))
    GPIO.output(flashLED, 0)
    logfile.writelines("picture taken\n")
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
    except Exception as e:
        print("failed to send. red led")
        print(e)

        
def main():
    GPIO.setup(flashLED, GPIO.OUT, initial=0)

    # startup sequence
    for i in range(5):
        GPIO.output(flashLED, 1)
        time.sleep(0.3)
        GPIO.output(flashLED, 0)
        time.sleep(0.3)
            
    
    print("starting camera")
    logfile.writelines("camera started at {} on the {} day of year\n".format(datetime.datetime.now(), day_of_year))


    try:
        # dns not working
        print("connecting to displaypi")
        ssh.connect("displaypi", username="pi", password="cheers")
        print("connected")
        logfile.writelines("connected to displaypi\n")
    except paramiko.SSHException:
        print("Connection to displaypi Failed")
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    get_date()
    prep_directory()
    
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
        logfile.writelines(str(e))
        GPIO.output(statusLED, 0)
        GPIO.output(flashLED, 0)
        GPIO.cleanup()
        ssh.close()
        logfile.close()
        
