#!/bin/sh
#
# Synology DSM init script for easyCab server component
# Requires: python
#
# Configured Variables:
#
 
# Begin script
#
case "$1" in
start)
  /usr/bin/python /root/mqtt-easycab.py &
  printf "[%4s]\n" "done"
  ;;
stop)
  printf "%-30s" "Stopping easyCab"
  killall python
  printf "[%4s]\n" "done"
  ;;
*)
  echo "Usage: $0 {start|stop}"
  exit 1
esac
 
exit 0