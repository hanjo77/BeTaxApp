#!/usr/bin/env python
# -*- coding: utf-8 -*-  

SERVER = "46.101.17.239"
PORT = 1883
TAG = "presence"

import os
import gps
import socket
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(TAG)

# Callback function for coordinates
def cb_coordinates(data):
    coordinates = '{"latitude":' + str(data.lat) + ',"longitude":' + str(data.lon) + '}'
    client.publish(TAG, coordinates, qos=0, retain=False)

# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

if __name__ == "__main__":
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(SERVER, PORT);

    while True:
        try:
            report = session.next()
            # Wait for a 'TPV' report and display the current time
            # To see all report data, uncomment the line below
            print report
            if report['class'] == 'TPV':
                if hasattr(report, 'lat'):
                    cb_coordinates(report)
        except KeyError:
            pass
        except KeyboardInterrupt:
            quit()
        except StopIteration:
            session = None
            print "GPSD has terminated"

