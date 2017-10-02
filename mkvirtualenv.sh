#!/usr/bin/env bash

DIR="$(dirname $0)"
if [ "$DIR" = "." ]; then
    DIR="$(pwd)"
fi

VIRTUALENVROOT="${1:-.virtualenvroot}"
VIBER_VIRTUALENV="$VIRTUALENVROOT/viber"
mkdir -p "$VIRTUALENVROOT"
virtualenv --no-site-packages "$VIBER_VIRTUALENV"
cat <<EOF > "$DIR/.virtualenvrc"
#
# Viber environment variables.
#
export VIBER_DIR="$DIR"
export VIBER_VIRTUALENV="$VIBER_VIRTUALENV"
source "$VIBER_VIRTUALENV/bin/activate"
export PYTHONPATH="$DIR"
if [ -z "\$VIBER_CONF" ]; then
    export VIBER_CONF=/etc/viber/bot-command.conf
fi
EOF

source "$DIR/.virtualenvrc"
pip install -r "$DIR/requirements.txt"

ln -s "$VIBER_VIRTUALENV" "$DIR/.virtualenv"

echo ""
echo "Viber Bot virtualenv created:"
echo ""
echo "source \"$DIR/.virtualenvrc\""
echo ""
