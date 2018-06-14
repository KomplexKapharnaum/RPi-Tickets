#!/bin/bash

convert -size 576x1200 xc:white /tmp/blank.jpg
fuser -k $(/root/RPi-Tickets/py-print/found.sh)
/root/RPi-Tickets/py-print/reset.py
systemctl restart tickets
