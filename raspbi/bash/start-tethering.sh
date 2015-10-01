#!/bin/sh

/etc/init.d/bluetooth restart;
sleep 10;
# pand -c 00:61:71:D3:76:83 -role PANU --persist 30
pand --role PANU --search;
echo "test";