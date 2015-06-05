#!/usr/bin/env python

import mosquitto
import json

__author__    = 'Jan-Piet Mens <jpmens()gmail.com>, Ben Jones <ben.jones12()gmail.com>'
__copyright__ = 'Copyright 2014 Jan-Piet Mens'

topic = 'presence'

def on_message(mosq, userdata, msg):
    try:
        data = msg.payload
    except:
        print "Can't decode payload"
    try:
        f = open('positions', 'w')
        f.write(str(msg.payload))
        f.close()
    except Exception, e:
        print "Can't write file: %s" % str(e)

mqttc = mosquitto.Mosquitto()
mqttc.on_message = on_message

mqttc.connect("localhost", 1883, 600)
mqttc.subscribe(topic, 0)

mqttc.loop_forever()
