# Deamon to automatically update EasyCab configuration when
# a USB flash drive with a "config.json" file is connected
#

#Imports
import functools
import os.path
import pyudev
import subprocess
import usb
import json
import time
from daemon import runner
from lockfile import LockTimeout

#Constants
CONFIG_PATH = '/usr/local/python'
FILE_NAME = 'config.json'

class FlashConfigListener():

    def __init__(self):
        """ Initializes daemon """
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/flashconfigd/flashconfigd.log'
        self.stderr_path = '/var/log/flashconfigd/flashconfigd-error.log'
        self.pidfile_path =  '/var/run/flashconfigd/flashconfigd.pid'
        self.pidfile_timeout = 5

    def run(self):
        """main method"""
        
        BASE_PATH = os.path.abspath(os.path.dirname(__file__))
        path = functools.partial(os.path.join, BASE_PATH)
        call = lambda x, *args: subprocess.call([path(x)] + list(args))

        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='usb')
        monitor.start()
        original_data = None

        try:
            os.chdir(CONFIG_PATH);
            with open(FILE_NAME) as original_data_file:
                original_data = json.load(original_data_file)
        except Exception as e:
            z = e
            print z

        if original_data:
            for device in iter(monitor.poll, None):
                '''
                One second timeout until device is mounted, then loop 
                through all USB devices and pass exception if file or device is not
                found
                '''
                time.sleep(2)
                for num in range(0,5):
                    try:
                        os.chdir('/media/usb' + str(num));
                        with open(FILE_NAME) as data_file:    
                            data = json.load(data_file)
                            for key, value in original_data.items():
                                if key in data:
                                    original_data[key] = data[key]
                            new_name = os.path.join(CONFIG_PATH, FILE_NAME)         
                            new_file = open(new_name, "w")
                            new_file.write(json.dumps(original_data))
                            new_file.close()
                            call(['service', 'easycabd', 'restart'])
                    except Exception as e:
                        pass
        while True:
            pass

flashConfigListener = FlashConfigListener()
daemon_runner = runner.DaemonRunner(flashConfigListener)

try:
    daemon_runner.do_action()

except LockTimeout:
    print 'Error: could not aquire lock, will restart daemon'

