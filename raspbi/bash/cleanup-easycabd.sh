#!/bin/sh

if pgrep "easycabd"
then
	killall easycabd
	rm /var/run/gpsd.sock
fi

/root/restart-gpsd.sh
