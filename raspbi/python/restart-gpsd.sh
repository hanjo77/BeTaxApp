#!/bin/sh

if pgrep gpsd;
then killall gpsd;
fi
gpsd /dev/ttyACM0 -F /var/run/gpsd.sock

exit 0