#!/bin/bash

ps -f | grep $(pwd)/gigglebot.py | grep -v grep

if [ $? -ne 0 ]
then
  python3 $(pwd)/gigglebot.py &
fi
