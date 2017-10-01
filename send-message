#!/usr/bin/env bash

DIR="$(dirname $0)"

if [ ! -f "$DIR/.venv" ]; then
    echo "ERROR: Virtual environment has not been created."
    exit 1
fi

source "$DIR/.venv"

"$DIR/send_message.py" $*
