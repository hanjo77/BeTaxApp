#!/bin/sh

if pgrep "easycabd"
then
	killall check-network.sh
	rm /var/run/gpsd.sock
fi