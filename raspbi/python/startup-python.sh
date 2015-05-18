#!/bin/sh

gpsd /dev/ttyACM0 -F /var/run/gpsd.sock
/usr/bin/python /usr/local/python/start-sensors.py &

exit 0