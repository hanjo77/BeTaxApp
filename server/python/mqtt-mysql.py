#!/usr/bin/env python
# -*- coding: utf-8 -*-  

import paho.mqtt.client as mqtt
import mysql.connector as mysql
import datetime
import json

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("presence")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("Hallo")
    cnx = mysql.connect(user='root', host='127.0.0.1', database='test')
    cursor = cnx.cursor()
    taxi = json.loads(msg.payload)
    test = str(taxi['car'])
    query = "INSERT INTO test (test) VALUES ('" + test + "')"
    cursor.execute(query)
    cnx.commit()
    cursor.close()
    cnx.close()
    print(msg.topic+" "+str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("hanjo.synology.me", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()