# To kick off the script, run the following from the python directory:
#   PYTHONPATH=`pwd` python testdaemon.py start

#standard python libs
import time
import os
import socket
import paho.mqtt.client as mqtt
import gps
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_nfc_rfid import NFCRFID
from daemon import runner
from subprocess import call

HOST = "localhost"
PORT = 4223
UID_NFC = "oDB"
UID_GPS = "qGf"
tag_type = 0


class EasyCabSensorListener():

    # Callback function on MQTT connection
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.client.subscribe("presence")

    # Callback function for coordinates
    def cb_coordinates(self, data):
        driver_id = os.getenv('DRIVER_ID', '')
        if driver_id != '':
            coordinates = '{"time":"' + data.time + '", "car":"' + socket.gethostname() + '", "driver":"' + driver_id + '","gps":{"latitude":' + str(data.lat) + ',"longitude":' + str(data.lon) + '}}'
            print(coordinates)
            self.client.publish("presence", coordinates, qos=0, retain=False)

    # Callback function for state changed callback
    def cb_state_changed(self, state, idle, nfc):
        # Cycle through all types"
        if idle:
            global tag_type
            tag_type = (tag_type + 1) % 3
            nfc.request_tag_id(tag_type)

        if state == nfc.STATE_REQUEST_TAG_ID_READY:
            ret = nfc.get_tag_id()
            id = ('-'.join(map(str, ret.tid[:ret.tid_length])))
            os.environ["DRIVER_ID"] = id
            print(id + " got connected")
        
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/sensor-daemon/sensor-daemon.log'
        self.stderr_path = '/var/log/sensor-daemon/sensor-daemon-error.log'
        self.pidfile_path =  '/var/run/sensor-daemon/sensor-daemon.pid'
        self.pidfile_timeout = 5
        self.client = []
        self.session = []

    def start_gps(self):
        self.session = gps.gps("localhost", "2947")
        self.session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

    def run(self):
        # Load MQTT client      
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.connect("hanjo.synology.me", 1883);
 
        self.start_gps()

        # Create IP connection for Tinkerforge and load NFC
        ipcon = IPConnection()
        ipcon.connect(HOST, PORT) # Connect to brickd
        # Don't use device before ipcon is connected

        # Register state changed callback to function cb_state_changed
        nfc = NFCRFID(UID_NFC, ipcon)
        nfc.register_callback(nfc.CALLBACK_STATE_CHANGED, lambda x, y: self.cb_state_changed(x, y, nfc))
        nfc.request_tag_id(nfc.TAG_TYPE_MIFARE_CLASSIC)

        while True:
            # Main code goes here ...
            try:
                report = self.session.next()
                # Wait for a 'TPV' report and display the current time
                # To see all report data, uncomment the line below
                # print report
                if hasattr(report, 'lat'):
                    self.cb_coordinates(report)
                # else:
                    # call(["/root/restart-gpsd.sh"])
                    # self.start_gps()
            except KeyError:
                pass
            except KeyboardInterrupt:
                quit()
            except StopIteration:
                # call(["gpsd", "/dev/ttyUSB0", "-F", "/var/run/gpsd.sock"])
                print "Restart GPSD"
            time.sleep(5)

easyCabSensorListener = EasyCabSensorListener()
daemon_runner = runner.DaemonRunner(easyCabSensorListener)
daemon_runner.do_action()