#!/bin/sh

['-c', 'id=$(shuf -i 1000-9999 -n 1);topic="press";while true;do timestamp=$(date "+%Y/%m/%d %H:%M:%S");pressure=$(shuf -i 0-10 -n 1);message="$timestamp Device:$id  Pressure:$pressure bar";pub -h 192.0.0.3 -t "$topic" -m "$message";echo "$timestamp";sleep $(shuf -i 3-5 -n 1);done']
