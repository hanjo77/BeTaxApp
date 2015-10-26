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
import os
import socket
import paho.mqtt.client as mqtt
import gps
import json
from daemon import runner
from subprocess import call

# Configuration constants
SERVER_HOSTNAME = "46.101.17.239"
MQTT_PORT = 1883
NFC_BRICKLET_ID = 246
GPS_TIMEOUT = 10 # Has to be larger than GPS_INTERVAL
GPS_INTERVAL = 5
tag_type = 0

# Callback function on MQTT connection
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.will_set("presence", '{ "disconnected": "' + socket.gethostname() + '" }', qos=0, retain=True);
    client.subscribe("session/" + socket.gethostname())
    print "subscribed to session/" + socket.gethostname()

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    try:
        print msg.payload + " received on topic " + msg.topic
        os.environ["SESSION_ID"] = str(data['session_id'])
        file = open("/root/session_id", "w")
        file.write(os.getenv('SESSION_ID'))
        file.close()
        print("received session ID: " + os.getenv('SESSION_ID'))
    except AttributeError, e:
        print(str(e))

def mqtt_publish(topic, message):
    if hasattr(client, 'publish'):
        client.publish(topic, message, qos=0, retain=True)

client = mqtt.Client()
client.on_message = on_message
client.on_connect = on_connect
client.connect(SERVER_HOSTNAME, MQTT_PORT, keepalive=100)
client.loop_forever()


