#!/bin/bash
set -x
for fname in *.py
do
    ampy --port /dev/ttyUSB0 put $fname
done
