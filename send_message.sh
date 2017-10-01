#!/usr/bin/env bash

if [ ! -f ".venv" ]; then
    echo "ERROR: Virtual environment has not been created."
    exit 1
fi

source .venv

./send_message.py $*
