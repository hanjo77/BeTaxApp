#!/usr/bin/env python
# -*- coding: utf-8 -*-  

HOST = "localhost"
PORT = 4223
UID_NFC = "oDB"
UID_GPS = "qGf"

import os
import gps
import socket
import paho.mqtt.client as mqtt
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_nfc_rfid import NFCRFID

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("presence")

# The callback for when a PUBLISH message is received from the server.
# def on_message(client, userdata, msg):
    # print(msg.topic+" "+str(msg.payload))

# Callback function for coordinates
def cb_coordinates(data):
    driver_id = os.getenv('DRIVER_ID', '')
    if driver_id != '':
        coordinates = '{"time":"' + data.time + '", "car":"' + socket.gethostname() + '", "driver":"' + driver_id + '","gps":{"latitude":' + str(data.lat) + ',"longitude":' + str(data.lon) + '}}'
        # print(coordinates)
        client.publish("presence", coordinates, qos=0, retain=False)

# Callback function for state changed callback
def cb_state_changed(state, idle, nfc):
    # Cycle through all types
    if idle:
        global tag_type
        tag_type = (tag_type + 1) % 3
        nfc.request_tag_id(tag_type)

    if state == nfc.STATE_REQUEST_TAG_ID_READY:
        ret = nfc.get_tag_id()
        id = ('-'.join(map(str, ret.tid[:ret.tid_length])))
        os.environ["DRIVER_ID"] = id
        # client.publish("presence", id, qos=0, retain=False)
        print(id + " got connected")


# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

if __name__ == "__main__":
    
    client = mqtt.Client()
    client.on_connect = on_connect
#    client.on_message = on_message

    client.connect("hanjo.synology.me", 1883);

    tag_type = 0

    ipcon = IPConnection() # Create IP connection
    nfc = NFCRFID(UID_NFC, ipcon) # Create device object
    # gps = GPS(UID_GPS, ipcon) # Create device object

    ipcon.connect(HOST, PORT) # Connect to brickd
    # Don't use device before ipcon is connected

    # Register state changed callback to function cb_state_changed
    nfc.register_callback(nfc.CALLBACK_STATE_CHANGED, 
                          lambda x, y: cb_state_changed(x, y, nfc))

    nfc.request_tag_id(nfc.TAG_TYPE_MIFARE_CLASSIC)

    while True:
        try:
            report = session.next()
            # Wait for a 'TPV' report and display the current time
            # To see all report data, uncomment the line below
            # print report
            if report['class'] == 'TPV':
                if hasattr(report, 'lat'):
                    # os.system('clear') #clear the terminal (optional)
                    cb_coordinates(report)
        except KeyError:
            pass
        except KeyboardInterrupt:
            quit()
        except StopIteration:
            session = None
            print "GPSD has terminated"

    ipcon.disconnect()


