#!/bin/bash
ARDUINO=~/software/archives/arduino-1.8.5/arduino
#
PORT=$(ls /dev/ttyACM*)
$ARDUINO -v --upload rssi-antenna-tracker.ino --board arduino:avr:leonardo --port $PORT
