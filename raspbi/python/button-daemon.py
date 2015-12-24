# EasyCabTracker Button listener
#

#Imports
import RPi.GPIO as GPIO
import time
import os
from subprocess import call
import ledbuttons
from daemon import runner
from lockfile import LockTimeout

#constants
CLICK_TIMEOUT = 2

class ButtonListener():

    def __init__(self):
        """ Initializes daemon """
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/buttond/buttond.log'
        self.stderr_path = '/var/log/buttond/buttond-error.log'
        self.pidfile_path =  '/var/run/buttond/buttond.pid'
        self.pidfile_timeout = 5
        self.oldtime = time.time()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(ledbuttons.BUTTON_GPIO, GPIO.IN)
        GPIO.remove_event_detect(ledbuttons.BUTTON_GPIO)
        GPIO.add_event_detect(ledbuttons.BUTTON_GPIO, GPIO.RISING, bouncetime=900, callback=self.cb_button)
        while True:
            pass

    def cb_button(self, channel):
        if GPIO.event_detected(ledbuttons.BUTTON_GPIO):
            if (time.time()-self.oldtime) > CLICK_TIMEOUT:          
                print 'pressed'           
                self.oldtime = time.time()
                if os.path.exists("/var/run/easycabd"):
                    call(['service', 'easycabd', 'stop'])
                    new_name = os.path.join('/usr/local/python/', 'block')         
                    new_file = open(new_name, "w")
                    new_file.write('')
                    new_file.close()
                else:
                    call(['service', 'easycabd', 'start'])
                    call(['rm', '/usr/local/python/block'])

buttonListener = ButtonListener()
daemon_runner = runner.DaemonRunner(buttonListener)

try:
    daemon_runner.do_action()

except LockTimeout:
    print 'Error: could not aquire lock, will restart daemon'
