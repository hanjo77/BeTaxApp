#!/bin/sh

/etc/init.d/bluetooth restart
sleep 10
# Nexus 5
# pand -c 8C:3A:E3:FA:92:17 -role PANU --persist 30;
# iPhone
# pand -c 00:61:71:D3:76:83 -role PANU --persist 30;
# Windows Phone
# pand -c 0C:E7:25:54:98:2C -role PANU --persist 30;
# Auto
pand --role PANU --search --nosdp --persist 10;
