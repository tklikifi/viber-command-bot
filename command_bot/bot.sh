#!/bin/bash

DIR="$(dirname $0)"

if [ ! -f "$DIR/../.venv" ]; then
    echo "ERROR: Virtual environment has not been created."
    exit 1
fi

source "$DIR/../.venv"

sudo "$VIBER_BOT_VENV/bin/uwsgi" --ini "$VIBER_BOT_DIR/command_bot/bot.ini" \
    --chdir "$VIBER_BOT_DIR" --virtualenv "$VIBER_BOT_VENV"
