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
import dbus
import json
from lockfile import LockTimeout
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_nfc_rfid import NFCRFID
from daemon import runner
from subprocess import call
from datetime import datetime

# Configuration constants
SERVER_HOSTNAME = "46.101.17.239"
MQTT_PORT = 1883
NFC_BRICKLET_ID = 246
GPS_TIMEOUT = 10 # Has to be larger than GPS_INTERVAL
GPS_INTERVAL = 5
tag_type = 0

# Constructor
class EasyCabListener():
    # Initializes daemon
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/easycabd/easycabd.log'
        self.stderr_path = '/var/log/easycabd/easycabd-error.log'
        self.pidfile_path =  '/var/run/easycabd/easycabd.pid'
        self.pidfile_timeout = 5
        self.update_time = time.time();
        self.nfc_uid = ""
        self.online = False
        self.subscribed = False
        self.client = []
        try:
            os.remove("/root/session_id")
        except:
            print("session_id not found")

    def date_handler(self, obj):
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj

    # Callback function for coordinates
    def cb_coordinates(self, data):
        driver_id = os.getenv('DRIVER_ID', '')
        phone_mac_addr = os.getenv('PHONE_MAC_ADDR', '')
        session_id = 0

        try:
            file = open('/root/session_id', 'r')
            os.environ["SESSION_ID"] = file.read()
            session_id = int(os.environ["SESSION_ID"])
        except Exception, e:
            call(["/root/check-network.sh", ">", "/dev/null"])

        if driver_id != '':
            if session_id <= 0:
                json_data = json.dumps({
                    'car': socket.gethostname(),
                    'driver': driver_id,
                    'phone': phone_mac_addr
                })
                print(json_data + " sent to topic 'session'\n")
                self.mqtt_publish("session", json_data)
            else:
                json_data = json.dumps({
                    'session': session_id,
                    'time': datetime.now(),
                    'car': socket.gethostname(),
                    'driver': driver_id,
                    'phone': phone_mac_addr,
                    'gps':{
                        'latitude': str(data.lat),
                        'longitude': str(data.lon)
                    }
                }, default=self.date_handler)
                print(json_data + " sent to topic 'presence'\n")
                self.mqtt_publish("presence", json_data)

    # Callback function for RFID reader state changed callback
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
                # print(id + " got connected\n")
            # GPS does not want to talk with us, often happens on boot - will restart myself (the daemon) and be back in a minute...
            if (time.time() - self.update_time) > GPS_TIMEOUT:
                print "Restart GPSD\n"
                call(["service", "easycabd", "restart"])
    
    def mqtt_publish(self, topic, message):
        if not hasattr(self.client, 'publish'):
            self.client = mqtt.Client()
            self.client.connect(SERVER_HOSTNAME, MQTT_PORT, keepalive=100)
        self.client.publish(topic, message, qos=0, retain=True)

    # Starts GPS listener
    def start_gps(self):
        try:
            self.session = gps.gps("localhost", "2947")
            self.session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
            pass
        except Exception, e:
            call(["service", "easycabd", "restart"])
            pass

    # Updated the mac address of the connected phone
    def update_phone_mac_addr(self):
        try:
            bus = dbus.SystemBus()
            manager = dbus.Interface(bus.get_object('org.bluez', '/'), 'org.bluez.Manager')
            adapterPath = manager.DefaultAdapter()
            adapter = dbus.Interface(bus.get_object('org.bluez', adapterPath), 'org.bluez.Adapter')
            for devicePath in adapter.ListDevices():
                device = dbus.Interface(bus.get_object('org.bluez', devicePath),'org.bluez.Device')
                deviceProperties = device.GetProperties()
                os.environ["PHONE_MAC_ADDR"] = deviceProperties["Address"]
        except Exception, e:
            print "phone mac not retrieved: " + str(e)   

    # Checks internet connection - returns true when connected, false when offline
    def internet_on(self):
        try:
            response = urllib2.urlopen('http://' + SERVER_HOSTNAME + "/data")
            self.update_phone_mac_addr()
            return True

        except urllib2.URLError as err:
            print err
            return False

    # Print incoming enumeration
    def cb_enumerate(self, uid, connected_uid, position, hardware_version, firmware_version, device_identifier, enumeration_type):
        if device_identifier == NFC_BRICKLET_ID:
            self.nfc_uid = uid

    # Run, daemon, run - Go for the main method
    def run(self):
        # Start GPS listener
        self.start_gps()

        # Create IP connection for Tinkerforge and load NFC
        ipcon = IPConnection()
        ipcon.connect("localhost", 4223) # Connect to brickd
        # Don't use device before ipcon is connected

        ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)

        while self.nfc_uid == "":
            ipcon.enumerate()

        # Register state changed callback for NFC sensor to function cb_state_changed
        nfc = NFCRFID(self.nfc_uid, ipcon)
        nfc.register_callback(nfc.CALLBACK_STATE_CHANGED, lambda x, y: self.cb_state_changed(x, y, nfc))
        nfc.request_tag_id(nfc.TAG_TYPE_MIFARE_CLASSIC)

        while True:
            # Do your magic now - it's the main loop!           
            try:
                if not self.internet_on():
                    print "offline"
                    call(["/root/check-network.sh", ">", "/dev/null"])
                    time.sleep(5)
                    self.update_phone_mac_addr()
                # Read GPS report and send it if we found a "lat" key
                report = self.session.next()
                valid = False;

                if report:
                    if hasattr(report, 'lat'):
                        if round(time.time() - self.update_time, 0) >= GPS_INTERVAL:
                            self.update_time = time.time()
                            self.cb_coordinates(report)
                        valid = True

                # GPS does not want to talk with us, often happens on boot - will restart myself (the daemon) and be back in a minute...
                if (time.time() - self.update_time) > GPS_TIMEOUT:
                    self.update_time = time.time()
                    call(["service", "easycabd", "restart"])
                    print "Restart GPSD"

            except KeyError:
                print KeyError
                call(["service", "easycabd", "restart"])
                pass

            except KeyboardInterrupt:
                quit()

            except StopIteration:
                print "GPSD Stopped " + str(self.update_time)
                call(["service", "easycabd", "restart"])

easyCabListener = EasyCabListener()
daemon_runner = runner.DaemonRunner(easyCabListener)

try:
    daemon_runner.do_action()
except LockTimeout:
    print "Error: couldn't aquire lock, will restart daemon"
    call(["service", "easycabd", "restart"])


