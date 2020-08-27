#!/bin/bash

ps -f | grep gigglebot.py | grep -v grep

if [ $? -ne 0 ]
then
python3 gigglebot.py &
fi
