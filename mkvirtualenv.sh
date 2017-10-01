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
virtualenv --no-site-packages "$VENV/viber"
echo "export VIBER_DIR=\"$DIR\"" > .venv
echo "export VIBER_VENV=\"$VENV/viber\"" >> .venv
echo "source \"$VENV/viber/bin/activate\"" >> .venv
echo "export PYTHONPATH=\"$VIBER_DIR\"" >> .venv
source "$DIR/.venv"
pip install -r "$DIR/requirements.txt"

echo ""
echo "Viber Bot virtualenv created:"
echo ""
echo "source \"$DIR/.venv\""
echo ""
