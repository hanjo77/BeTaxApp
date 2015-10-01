#!/bin/sh

if pgrep "gpsd"
then
	killall gpsd
	rm /var/run/gpsd.sock
fi

gpsd /dev/ttyACM0 -F /var/run/gpsd.sock

exit 0