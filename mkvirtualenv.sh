#!/usr/bin/env bash

if [ -z "$1" ]; then
    VENV="$(pwd)/venv"
else
    VENV="$1"
fi
mkdir -p "$VENV"
virtualenv --no-site-packages "$VENV/viber-bot"
echo "export VIBER_BOT_VENV=\"$VENV/viber-bot\"" > .venv
echo "source \"$VENV/viber-bot/bin/activate\"" >> .venv
source .venv
pip install -r requirements.txt

echo ""
echo "Viber Bot virtualenv created:"
echo ""
echo "source .venv"
echo ""
