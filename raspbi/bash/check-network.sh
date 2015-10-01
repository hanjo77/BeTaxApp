#!/bin/sh

if pgrep "check-network.sh"
then
	killall check-network.sh
	rm /var/run/gpsd.sock
fi

ERROR="$(ifconfig bnep0 | grep 'error')"
NETWORK="$(ifconfig bnep0 | grep 'inet addr')"

# There was an error, most possibly the network was not found because we have no thethered device so let's go back to tether

if [ -z "${ERROR}" ]
then
    ./start-tethering.sh
fi

# Restart the bluetooth network

if [ -z "${NETWORK}" ]
then
    ifdown bnep0 && ifup bnep0
fi