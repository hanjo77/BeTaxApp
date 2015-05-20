#!/bin/sh

NETWORK="$(ifconfig bnep0 | grep 'inet addr')"

if [ -z "${NETWORK}" ]
then
        /etc/init.d/networking restart
fi

echo $(grep -Fxq "latitude" /var/log/sensor-daemon/sensor-daemon.log)
if [ ! $(grep -Fxq "latitude" /var/log/sensor-daemon/sensor-daemon.log) ]
then
    service sensor-daemon restart
fi

ERRORSIZE = $(du -k /var/log/sensor-daemon/sensor-daemon-error.log | cut -f 1)

if [ $ERRORSIZE > 50 ]
then
	service sensor-daemon restart
fi