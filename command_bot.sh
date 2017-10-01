#!/bin/bash

if [ ! -f ".venv" ]; then
    echo "ERROR: Virtual environment has not been created."
    exit 1
fi

source .venv

sudo "$VIBER_BOT_VENV/bin/uwsgi" --ini "command_bot/bot.ini" --chdir "$(pwd)" \
    --virtualenv "$VIBER_BOT_VENV"
