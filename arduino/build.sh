#!/bin/bash
ARDUINO=~/software/archives/arduino-1.8.5/arduino
# --upload --port /dev/ttyACM1 --board arduino:avr:leonardo 
$ARDUINO -v --verify rssi-antenna-tracker.ino --board arduino:avr:leonardo 
