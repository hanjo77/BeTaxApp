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
import httplib
import ledbuttons
from lockfile import LockTimeout
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_nfc_rfid import NFCRFID
from daemon import runner
from subprocess import call
from datetime import datetime
from uuid import getnode as get_mac

# Configuration constants
config = {}

SERVER_HOSTNAME = '46.101.17.239'
MQTT_PORT = 1883
NFC_BRICKLET_ID = 246
NFC_TAG_TYPE = 0
TOKEN_TYPE_DRIVER = 'DRIVER'
TOKEN_TYPE_TAXI = 'TAXI'
CONFIG_UPDATE_INTERVAL = 60


class EasyCabListener():
    """ Constructor """
    def __init__(self):
        """ Initializes daemon """
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/easycabd/easycabd.log'
        self.stderr_path = '/var/log/easycabd/easycabd-error.log'
        self.pidfile_path =  '/var/run/easycabd/easycabd.pid'
        self.pidfile_timeout = 5
        self.update_time = time.time();
        self.nfc_uid = ''
        self.online = False
        self.subscribed = False
        self.client = []
        self.driver_token = ''
        self.taxi_token = ''
        self.phone_mac_addr = ''
        self.session_id = 0
        self.ledbutton_handler = ledbuttons.LedButtonHandler()
        self.config_time = time.time()
        self.config = []


    def date_handler(self, obj):
        """ Handler used to serialize datetime objects """
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj

    def cb_coordinates(self, data):
        """ Callback function for coordinates """
        #session_id = self.get_session_id(self.taxi_token, self.driver_token, self.phone_mac_addr)

        if (self.taxi_token != '' and
            self.session_id > 0):
            json_data = json.dumps({
                'session': self.session_id,
                'time': datetime.now(),
                'gps':{
                    'latitude': str(data.lat),
                    'longitude': str(data.lon)
                }
            }, default=self.date_handler)
            self.mqtt_publish('presence', json_data)

    def get_session_id(self, taxi_token, driver_token, phone_mac_addr):
        """ Gets session ID from HTTP request """
        session_id = 0
        url = ('http://' + 
            SERVER_HOSTNAME + 
            '/data/session/' + 
            phone_mac_addr + '/' +
            taxi_token + '/' + 
            driver_token + '/'
            )
        try:
            session = json.load(urllib2.urlopen(url))
            session_id = session['session_id']
            if self.session_id != session_id:
                self.session_id = session_id
                print 'SESSION_ID = '+str(session_id)
        except Exception as e:
            if taxi_token != '':
                print (url + ' call failed')
                z = e
                print z
            pass
        return session_id

    def cb_state_changed(self, state, idle, nfc):
        """ Callback function for RFID reader state changed callback """
        # Cycle through all types'
        if idle:
            global NFC_TAG_TYPE
            NFC_TAG_TYPE = (NFC_TAG_TYPE + 1) % 3
            nfc.request_tag_id(NFC_TAG_TYPE)

        # We found a tag, so we can start tracking
        if state == nfc.STATE_REQUEST_TAG_ID_READY:
            ret = nfc.get_tag_id()
            d = [('%0.2X' % t) for t in ret.tid];
            id = (':'.join(d))
            # Set environment variable DRIVER_TOKEN to NFC tag ID
            url = ('http://' + 
                SERVER_HOSTNAME + 
                '/data/validate_token/' + 
                id + '/'
                );
            try:
                token = json.load(urllib2.urlopen(url))
                token_type = token['type'].upper()
                if token_type == TOKEN_TYPE_DRIVER and self.driver_token != id:
                    self.driver_token = id
                    self.ledbutton_handler.set_led_blink(ledbuttons.DRIVER_KEY, False)
                    print token_type+'_TOKEN = '+id
                elif token_type == TOKEN_TYPE_TAXI and self.taxi_token != id:
                    self.taxi_token = id
                    self.ledbutton_handler.set_led_blink(ledbuttons.TAXI_KEY, False)
                    print token_type+'_TOKEN = '+id
            except Exception as e:
                print url + ' call failed'
                z = e
                print z
    
    def mqtt_publish(self, topic, message):
        """ Wrapper to publish messages over MQTT """
        if not hasattr(self.client, 'publish'):
            self.client = mqtt.Client()
            self.client.connect(SERVER_HOSTNAME, MQTT_PORT, keepalive=100)
        self.client.publish(topic, message, qos=0, retain=True)
        print message + ' published to ' + topic

    def start_gps(self):
        """ Starts GPS listener """
        try:
            self.session = gps.gps('localhost', '2947')
            self.session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
            pass
        except Exception:
            call(['service', 'easycabd', 'restart'])
            pass

    def update_phone_mac_addr(self):
        """ Updates the mac address of the connected phone """
        try:
            mac_addr = ':'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))
            if (self.phone_mac_addr != mac_addr):
                url = ('http://' + 
                    SERVER_HOSTNAME + 
                    '/data/validate_phone/' + 
                    mac_addr + '/'
                    );
                phone = json.load(urllib2.urlopen(url))
                if len(phone) > 0:
                    self.phone_mac_addr = mac_addr
                    self.ledbutton_handler.set_led_blink(ledbuttons.PHONE_KEY, False)
        except Exception as e:
            print Exception
            z = e
            print z
            pass

    def internet_on(self):
        """ Checks internet connection - returns true when connected, false when offline """
        try:
            response = urllib2.urlopen('http://' + SERVER_HOSTNAME)
            self.update_phone_mac_addr()
            if self.ledbutton_handler.get_led_blink():
                self.ledbutton_handler.set_led_blink(ledbuttons.NETWORK_KEY, False)
            return True

        except Exception:
            self.ledbutton_handler.set_led_blink(ledbuttons.NETWORK_KEY, True)
            return False

    def cb_enumerate(self, uid, connected_uid, position, hardware_version, firmware_version, device_identifier, enumeration_type):
        """ Print incoming enumeration """
        if device_identifier == NFC_BRICKLET_ID:
            self.nfc_uid = uid

    def update_config(self):
        self.get_session_id(self.taxi_token, self.driver_token, self.phone_mac_addr)
        self.config_time = time.time()
        self.update_phone_mac_addr()
        url = ('http://' +
                SERVER_HOSTNAME +
                '/data/app_config/'
                );
        try:
            self.config = json.load(urllib2.urlopen(url))
        except Exception:
            print url + ' call failed'
            # z = e
            # print z

    def run(self):
        """ The main method """
        # Start LED and button listener
        ledbutton_thread = ledbuttons.LedButtonsListener(self.ledbutton_handler)
        ledbutton_thread.daemon = True
        ledbutton_thread.start()

        # Start GPS listener
        self.start_gps()

        # Create IP connection for Tinkerforge and load NFC
        ipcon = IPConnection()
        ipcon.connect('localhost', 4223) # Connect to brickd
        # Don't use device before ipcon is connected

        ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)

        while self.nfc_uid == '':
            ipcon.enumerate()

        # Register state changed callback for NFC sensor to function cb_state_changed
        nfc = NFCRFID(self.nfc_uid, ipcon)
        nfc.register_callback(nfc.CALLBACK_STATE_CHANGED, lambda x, y: self.cb_state_changed(x, y, nfc))
        nfc.request_tag_id(nfc.TAG_TYPE_MIFARE_CLASSIC)

        while True:
            # Do your magic now - it's the main loop!           
            try:
                if not self.internet_on():
                    print 'offline'
                    self.client = []
                    time.sleep(5)
                if (time.time() - self.config_time) >= CONFIG_UPDATE_INTERVAL:
                    self.update_config()
                # Read GPS report and send it if we found a 'lat' key
                if self.ledbutton_handler.is_tracking:
                    report = self.session.next()
                    #valid = False;

                    if report:
                        # if self.ledbutton_handler.get_led_blink(ledbuttons.GPS_KEY):
                        if hasattr(report, 'lat'):
                            self.ledbutton_handler.set_led_blink(ledbuttons.GPS_KEY, False)
                            if round(time.time() - self.update_time, 0) >= self.config['position_update_interval']:
                                self.update_time = time.time()
                                self.cb_coordinates(report)
                           # valid = True

                # GPS does not want to talk with us, often happens on boot - will restart myself (the daemon) and be back in a minute...
                if (time.time() - self.update_time) > (self.config['position_update_interval']*3):
                    self.update_time = time.time()
                    call(['service', 'easycabd', 'restart'])
                    print 'Restart GPSD'

            except KeyError:
                print KeyError
                call(['service', 'easycabd', 'restart'])

            except KeyboardInterrupt:
                quit()

            except StopIteration:
                print 'GPSD Stopped ' + str(self.update_time)
                call(['service', 'easycabd', 'restart'])

            except Exception:
                print Exception


easyCabListener = EasyCabListener()
daemon_runner = runner.DaemonRunner(easyCabListener)

try:
    daemon_runner.do_action()
except LockTimeout:
    print 'Error: could not aquire lock, will restart daemon'
    call(['service', 'easycabd', 'restart'])


