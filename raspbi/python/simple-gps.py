#! /usr/bin/python
# coding=utf-8
# Written by Dan Mandle http://dan.mandle.me September 2012
# License: GPL 2.0

import os
import gps
import json
# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

while True:
    try:
        report = session.next()
        # Wait for a 'TPV' report and display the current time
        # To see all report data, uncomment the line below
        # print report
        if report['class'] == 'TPV':
            if hasattr(report, 'time'):
                os.system('clear') #clear the terminal (optional)
                print 'Latitude:  ' + str(report.lat) + '°\n' \
                    + 'Longitude: ' + str(report.lon) + '°\n'\
                    + 'Altitude:  ' + str(report.alt) + ' m';
    except KeyError:
        pass
    except KeyboardInterrupt:
        quit()
    except StopIteration:
        session = None
        print "GPSD has terminated"

