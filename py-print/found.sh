#!/bin/bash

SYSPATH=/sys/bus/usb/devices/
VENDOR=04b8
PRODUCT=0e15
cd $SYSPATH

for device in ./*; do
  if [ "$(cat "$device/idVendor" 2>/dev/null)" == "$VENDOR" ] && [ "$(cat "$device/idProduct" 2>/dev/null)" == "$PRODUCT" ]; then
#	echo "found $device"
#	echo 0 > "$device/authorized"
#	echo 1 > "$device/authorized"
	echo  /dev/bus/usb/001/00$(cat $device/devnum)
  fi
done
