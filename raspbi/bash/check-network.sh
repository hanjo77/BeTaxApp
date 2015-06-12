#!/bin/sh

if pgrep "check-network.sh"
then
	killall check-network.sh
	rm /var/run/gpsd.sock
fi

NETWORK="$(ifconfig bnep0 | grep 'inet addr')"

if [ -z "${NETWORK}" ]
then
    ifdown bnep0 && ifup bnep0
fi