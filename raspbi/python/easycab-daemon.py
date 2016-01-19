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
import paho.mqtt.client as mqtt
import gps
import urllib2
import json
import ledhandler
import os.path
import signal
from lockfile import LockTimeout
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_nfc_rfid import NFCRFID
from daemon import runner
from subprocess import call
from datetime import datetime
from uuid import getnode as get_mac
from Crypto import Random
from Crypto.Cipher import AES
import base64

# Configuration constants
NFC_BRICKLET_ID = 246
NFC_TAG_TYPE = 0
TOKEN_TYPE_DRIVER = 'DRIVER'
TOKEN_TYPE_TAXI = 'TAXI'


class EasyCabListener():
    """ Constructor """
    def __init__(self):
        """ Initializes daemon """
        self.stdin_path = '/dev/null'
        # self.stdout_path = '/var/log/easycabd/' + datetime.now().strftime('easycabd_%Y-%m-%d-%H-%M.log')
        # self.stderr_path = '/var/log/easycabd/' + datetime.now().strftime('easycabd-error_%Y-%m-%d-%H-%M.log')
        self.stdout_path = '/var/log/easycabd/easycabd.log'
        self.stderr_path = '/var/log/easycabd/easycabd-error.log'
        self.pidfile_path =  '/var/run/easycabd/easycabd.pid'
        self.block_file_path = '/block'
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
        self.led_handler = ledhandler.LedHandler()
        self.config = {}
        self.client_config = {}
        self.config_time = time.time()
        self.turn_off_leds()
        self.update_config()

    def restart_daemon(self):
        self.turn_off_leds()
        self.config = {}
        call(['service', 'easycabd', 'restart'])

    def turn_off_leds(self):
        self.led_handler.set_all_led_off()
        self.driver_token = ''
        self.taxi_token = ''
        self.phone_mac_addr = ''
        self.session_id = 0

    def date_handler(self, obj):
        """ Handler used to serialize datetime objects """
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj

    def cb_coordinates(self, data):
        """ Callback function for coordinates """
        self.update_session_id(self.taxi_token, self.driver_token, self.phone_mac_addr)

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
            self.mqtt_publish('presence', self.encrypt(json_data))

    def update_session_id(self, taxi_token, driver_token, phone_mac_addr):
        """ Gets session ID from HTTP request """
        if (time.time() - self.config_time) >= self.config['session_timeout']:
            session_id = 0
            url = ('http://' + 
                self.client_config['mqtt_url'] + 
                self.client_config['python_web_path'] +
                '/session/' + 
                phone_mac_addr + '/' +
                taxi_token + '/' + 
                driver_token + '/'
                )
            try:
                session = json.load(urllib2.urlopen(url))
                session_id = session['session_id']
                if self.session_id != session_id:
                    self.session_id = session_id
                    self.config_time = time.time()
                    print 'SESSION_ID = '+str(session_id)
            except Exception as e:
                if taxi_token != '':
                    print (url + ' call failed')
                    z = e
                    print z
                pass

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
                self.client_config['mqtt_url'] + 
                self.client_config['python_web_path'] +
                '/validate_token/' + 
                id + '/'
                );
            try:
                token = json.load(urllib2.urlopen(url))
                token_type = token['type'].upper()
                if token_type == TOKEN_TYPE_DRIVER and self.driver_token != id:
                    self.driver_token = id
                    self.led_handler.set_led_on(ledhandler.DRIVER_KEY)
                elif token_type == TOKEN_TYPE_TAXI and self.taxi_token != id:
                    self.taxi_token = id
                    self.led_handler.set_led_on(ledhandler.TAXI_KEY)
                print token_type+'_TOKEN = '+id
            except Exception as e:
                print 'Error in method cb_state_changed'
                print url + ' call failed'
                z = e
                print z
    
    def mqtt_publish(self, topic, message):
        """ Wrapper to publish messages over MQTT """
        if not hasattr(self.client, 'publish'):
            self.client = mqtt.Client()
            self.client.connect(self.client_config['mqtt_url'], self.client_config['mqtt_port'], keepalive=100)
        self.client.publish(topic, message, qos=0, retain=True)
        self.update_time = time.time()
        self.config_time = time.time()
        print message + ' published to ' + topic

    def start_gps(self):
        """ Starts GPS listener """
        try:
            self.session = gps.gps('localhost', '2947')
            self.session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
            pass
        except Exception:
            print 'Error in method start_gps'
            self.restart_daemon()
            pass

    def update_phone_mac_addr(self):
        """ Updates the mac address of the connected phone """
        try:
            mac_addr = ':'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))
            if (self.phone_mac_addr != mac_addr):
                url = ('http://' + 
                    self.client_config['mqtt_url'] + 
                    self.client_config['python_web_path'] +
                    '/validate_phone/' + 
                    mac_addr + '/'
                    );
                phone = json.load(urllib2.urlopen(url))
                if len(phone) > 0:
                    self.phone_mac_addr = mac_addr
                    self.led_handler.set_led_on(ledhandler.PHONE_KEY)
                else:
                    self.led_handler.set_led_off(ledhandler.PHONE_KEY) 
        except Exception as e:
            print 'Error in method update_phone_mac_addr'
            print Exception
            z = e
            print z
            pass

    def internet_on(self):
        """ Checks internet connection - returns true if connected, false if offline """
        try:
            response = urllib2.urlopen('http://www.google.com')
            self.led_handler.set_led_on(ledhandler.NETWORK_KEY)
            return True

        except Exception as e:
            print 'Error in method internet_on'
            print Exception
            z = e
            print z
            self.led_handler.set_led_off(ledhandler.NETWORK_KEY)
            return False

    def cb_enumerate(self, uid, connected_uid, position, hardware_version, firmware_version, device_identifier, enumeration_type):
        """ Print incoming enumeration """
        if device_identifier == NFC_BRICKLET_ID:
            self.nfc_uid = uid

    def update_config(self):
        os.chdir('/usr/local/python');
        with open('config.json') as data_file:    
            self.client_config = json.load(data_file)
        if self.internet_on():    
            self.update_phone_mac_addr()
            url = ('http://' +
                self.client_config['mqtt_url'] +
                self.client_config['python_web_path'] +
                '/app_config/'
                );
            try:
                self.config = json.load(urllib2.urlopen(url))
            except Exception as e:
                print 'Error in method update_config'
                print url + ' call failed'
                z = e
                print z

    def run(self):
        """ The main method """
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

        if os.path.exists(self.block_file_path):
            call(['rm', self.block_file_path])
            
        while True:
            # Do your magic now - it's the main loop!  
            if not os.path.exists(self.block_file_path):
                try:
                    if not self.internet_on():
                        print 'offline'
                        self.client = []
                        time.sleep(5)
                    else:
                        if (self.config == {}):
                            self.update_config()
                    if self.phone_mac_addr == '':
                        self.update_config()
                    # Read GPS report and send it if we found a 'lat' key
                    report = self.session.next()
                    valid = False;

                    if report:
                        if hasattr(report, 'lat'):
                            self.led_handler.set_led_on(ledhandler.GPS_KEY)
                            if round(time.time() - self.update_time, 0) >= self.config['position_update_interval']:
                                self.update_time = time.time()
                                self.cb_coordinates(report)
                            valid = True

                    # GPS does not want to talk with us, often happens on boot - will restart myself (the daemon) and be back in a minute...
                    if (time.time() - self.update_time) > (self.config['position_update_interval']*3):
                        self.update_time = time.time()
                        print 'Restart GPSD'
                        self.led_handler.set_led_off(ledhandler.GPS_KEY) 
                        call(['/root/restart-gpsd.sh'])

                except KeyError:
                    print KeyError
                    self.restart_daemon()

                except KeyboardInterrupt:
                    quit()

                except StopIteration:
                    print 'GPSD Stopped ' + str(self.update_time)
                    self.restart_daemon()

                except Exception as e:
                    print 'Error in method start_gps'
                    print Exception
                    z = e
                    print z
            else:
                self.turn_off_leds()

    def pad(self, data):
        """ Adds padding characters for encryption """
        length = 16 - (len(data) % 16)
        return data + chr(length)*length

    def unpad(self, data):
        """ Removes added padding characters for decryption """
        return data[:-ord(data[-1])]

    def encrypt(self, message):
        """ AES encrypts a string """
        IV = Random.new().read(16)
        aes = AES.new(self.config['encryption_key'], AES.MODE_CFB, IV, segment_size=128)
        return base64.b64encode(IV + aes.encrypt(self.pad(message)))

    def decrypt(self, encrypted):
        """ Decrypts an AES encrypted string """
        encrypted = base64.b64decode(encrypted)
        IV = encrypted[:16]
        aes = AES.new(self.config['encryption_key'], AES.MODE_CFB, IV, segment_size=128)
        return self.unpad(aes.decrypt(encrypted[16:]))

easyCabListener = EasyCabListener()
daemon_runner = runner.DaemonRunner(easyCabListener)

try:
    daemon_runner.do_action()

except LockTimeout:
    print 'Error: could not aquire lock, will restart daemon'
    call(['service', 'easycabd', 'restart'])


