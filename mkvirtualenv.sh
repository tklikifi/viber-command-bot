#!/usr/bin/env bash

DIR="$(dirname $0)"
if [ "$DIR" = "." ]; then
    DIR="$(pwd)"
fi

if [ -z "$1" ]; then
    echo "Usage: $0 virtual_env_dir"
    exit 1
fi

VENV="$1"
mkdir -p "$VENV"
virtualenv --no-site-packages "$VENV/viber-bot"
echo "export VIBER_BOT_DIR=\"$DIR\"" > .venv
echo "export VIBER_BOT_VENV=\"$VENV/viber-bot\"" >> .venv
echo "source \"$VENV/viber-bot/bin/activate\"" >> .venv
echo "export PYTHONPATH=\"$VIBER_BOT_DIR\"" >> .venv
source "$DIR/.venv"
pip install -r "$DIR/requirements.txt"

echo ""
echo "Viber Bot virtualenv created:"
echo ""
echo "source \"$DIR/.venv\""
echo ""
