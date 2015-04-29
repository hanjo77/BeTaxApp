#!/bin/sh

NETWORK="$(ifconfig bnep0 | grep 'inet addr')"
if [ -z "${NETWORK}" ]; then
        /etc/init.d/networking restart
fi
