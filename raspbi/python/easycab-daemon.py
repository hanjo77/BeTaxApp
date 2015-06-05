##
#
# easyCab daemon [easycabd]
#
# This daemon listens to an NFC sensor and a GPS USB receiver
# and sends the GPS data to a server using MQTT as soon as the user
# triggers the NFC sensor.
#
##

# import libs
import time
import os
import socket
import paho.mqtt.client as mqtt
import gps
import urllib2
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_nfc_rfid import NFCRFID
from daemon import runner
from subprocess import call

# Configuration constants
SERVER_HOSTNAME = "hanjo.synology.me"
UID_NFC = "oDB"
UID_GPS = "qGf"
GPS_TIMEOUT = 10;
tag_type = 0

# Constructor
class EasyCabListener():

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
            coordinates = ('{'
                '"time":"' + data.time + '",'
                '"car":"' + socket.gethostname() + '",'
                '"driver":"' + driver_id + '",'
                '"gps":{'
                    '"latitude":' + str(data.lat) + ','
                    '"longitude":' + str(data.lon) +
                '}'
            '}')
            print(coordinates)
            self.client.publish("presence", coordinates, qos=0, retain=False)

    # Callback function for state changed callback
    def cb_state_changed(self, state, idle, nfc):
        # Cycle through all types"
        if idle:
            global tag_type
            tag_type = (tag_type + 1) % 3
            nfc.request_tag_id(tag_type)

        # We found a tag, so we can start tracking
        if state == nfc.STATE_REQUEST_TAG_ID_READY:
            ret = nfc.get_tag_id()
            id = ('-'.join(map(str, ret.tid[:ret.tid_length])))
            # Set environment variable DRIVER_ID to NFC tag ID
            if not hasattr(os.environ, "DRIVER_ID") or os.environ["DRIVER_ID"] != id:
                os.environ["DRIVER_ID"] = id
                print(id + " got connected")
            # GPS does not want to talk with us, often happens on boot - will restart myself (the daemon) and be back in a minute...
            if (time.time() - self.update_time) > GPS_TIMEOUT:
                call(["service", "easycabd", "restart"])
                print "Restart GPSD"
    
    # Initializes daemon
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/easycabd/easycabd.log'
        self.stderr_path = '/var/log/easycabd/easycabd-error.log'
        self.pidfile_path =  '/var/run/easycabd/easycabd.pid'
        self.pidfile_timeout = 5
        self.client = []
        self.session = []
        self.update_time = time.time();

    # Starts GPS listener
    def start_gps(self):
        self.session = gps.gps("localhost", "2947")
        self.session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

    # Checks internet connection - returns true when connected, false when offline
    def internet_on(self):
        try:
            response = urllib2.urlopen('http://' + SERVER_HOSTNAME,timeout=1)
            return True

        except urllib2.URLError as err:
            pass

        return False

    # Run, daemon, run - Go for the main method
    def run(self):

        # Wait until we can connect - network may not be ready yet...
        while not self.internet_on():
            call(["/root/check-network.sh"])
            time.sleep(5)
            
        # Load MQTT client 
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.connect(SERVER_HOSTNAME, 1883)
 
        # Start GPS listener
        self.start_gps()

        # Create IP connection for Tinkerforge and load NFC
        ipcon = IPConnection()
        ipcon.connect("localhost", 4223) # Connect to brickd
        # Don't use device before ipcon is connected

        # Register state changed callback for NFC sensor to function cb_state_changed
        nfc = NFCRFID(UID_NFC, ipcon)
        nfc.register_callback(nfc.CALLBACK_STATE_CHANGED, lambda x, y: self.cb_state_changed(x, y, nfc))
        nfc.request_tag_id(nfc.TAG_TYPE_MIFARE_CLASSIC)

        while True:
            # Do your magic now - it's the main loop!
            try:
                # Read GPS report and send it if we found a "lat" key
                report = self.session.next()
                valid = False;
                if report:
                    if hasattr(report, 'lat'):
                        self.cb_coordinates(report)
                        valid = True
                        time.sleep(5);
                        self.update_time = time.time()


                # GPS does not want to talk with us, often happens on boot - will restart myself (the daemon) and be back in a minute...
                if (time.time() - self.update_time) > GPS_TIMEOUT:
                    call(["service", "easycabd", "restart"])
                    print "Restart GPSD"

            except KeyError:
                pass

            except KeyboardInterrupt:
                quit()

            except StopIteration:
                print "GPSD Stopped " + str(self.update_time)

# Create and execute an instance of this class
easyCabListener = EasyCabListener()
daemon_runner = runner.DaemonRunner(easyCabListener)
daemon_runner.do_action()