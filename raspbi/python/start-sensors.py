#!/usr/bin/env python
# -*- coding: utf-8 -*-  

HOST = "localhost"
PORT = 4223
UID_NFC = "oDB"
UID_GPS = "qGf"

import os
import socket
import paho.mqtt.client as mqtt
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_nfc_rfid import NFCRFID
from tinkerforge.bricklet_gps import GPS

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("presence")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("hanjo.synology.me", 1883);

tag_type = 0

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
        print(id)

# Callback function for coordinates
def cb_coordinates(latitude, ns, longitude, ew, pdop, hdop, vdop, epe):
    driver_id = os.getenv('DRIVER_ID', '')
    if driver_id != '':
        coordinates = '{"car":"' + socket.gethostname() + '", "driver":"' + driver_id + '","gps":{"latitude":' + str(latitude/1000000.0) + ',"longitude":' + str(longitude/1000000.0) + '}}'
        print(coordinates)
        client.publish("presence", coordinates, qos=0, retain=False)

if __name__ == "__main__":
    ipcon = IPConnection() # Create IP connection
    nfc = NFCRFID(UID_NFC, ipcon) # Create device object
    gps = GPS(UID_GPS, ipcon) # Create device object

    ipcon.connect(HOST, PORT) # Connect to brickd
    # Don't use device before ipcon is connected

    # Set Period for coordinates callback to 10s (10000ms)
    # Note: The callback is only called every second if the 
    #       coordinates have changed since the last call!
    gps.set_coordinates_callback_period(10000)

    # Register coordinates callback to function cb_coordinates
    gps.register_callback(gps.CALLBACK_COORDINATES, cb_coordinates)

    # Register state changed callback to function cb_state_changed
    nfc.register_callback(nfc.CALLBACK_STATE_CHANGED, 
                          lambda x, y: cb_state_changed(x, y, nfc))

    nfc.request_tag_id(nfc.TAG_TYPE_MIFARE_CLASSIC)

    while True:
        # Do nothing
        r = True
    # raw_input('Press key to exit\n') # Use input() in Python 3
    ipcon.disconnect()


