#!/usr/bin/env python
# -*- coding: utf-8 -*-  

import paho.mqtt.client as mqtt
import mysql.connector as mysql
import datetime
import json

def get_connection():
    return mysql.connect(user='easycab', password='raspberry', host='127.0.0.1', database='easycab')

def add_driver(token):
    driver_id = 0
    cnx = get_connection()
    cursor = cnx.cursor()
    try:
        cursor.execute("INSERT INTO data_driver (token) VALUES ('" + token + "')")
        driver_id = cursor.lastrowid
    except:
        driver_id = 0
    cnx.commit()
    cursor.close()
    cnx.close()    
    return driver_id

def get_driver(token):
    driver_id = 0
    cnx = get_connection()
    cursor = cnx.cursor()
    result = cursor.execute("SELECT id FROM data_driver WHERE token = '" + token + "'")
    for (id) in cursor:
        driver_id = id[0]
    cursor.close()
    cnx.close()    
    return driver_id

def add_taxi(name):
    taxi_id = 0
    cnx = get_connection()
    cursor = cnx.cursor()
    try:
        cursor.execute("INSERT INTO data_taxi (name) VALUES ('" + name + "')")
        driver_id = cursor.lastrowid
    except:
        taxi_id = 0
    cnx.commit()
    cursor.close()
    cnx.close()    
    return taxi_id

def get_taxi(name):
    taxi_id = 0
    cnx = get_connection()
    cursor = cnx.cursor()
    result = cursor.execute("SELECT id FROM data_taxi WHERE name = '" + name + "'")
    for (id) in cursor:
        taxi_id = id[0]
    cursor.close()
    cnx.close()    
    return taxi_id

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("presence")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    taxi = json.loads(msg.payload)
    try:
        cnx = get_connection()
        cursor = cnx.cursor()
        driver_id = get_driver(taxi['driver'])
        if driver_id <= 0:
            driver_id = add_driver(taxi['driver'])
        taxi_id = get_taxi(taxi['car'])
        if taxi_id <= 0:
            taxi_id = add_taxi(taxi['car'])
        query = "INSERT INTO data_position (taxi_id, driver_id, latitude, longitude, time) VALUES (%s, %s, %s, %s, %s)"
        parameters = (str(taxi_id), str(driver_id), str(taxi['gps']['latitude']), str(taxi['gps']['longitude']), datetime.datetime.now())
        try:
            cursor.execute(query, parameters)
            cnx.commit()
        except:
            print("error on query: " + query)
        cursor.close()
        cnx.close()
    except AttributeError, e:
        print(taxi)
        print(str(e))


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("46.101.17.239", 1883, 10)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()