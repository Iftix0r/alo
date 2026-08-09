#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_ACTIVATE="${VENV_ACTIVATE:-/home/host7905/virtualenv/husniddin/3.11/bin/activate}"

cd "$DIR" || exit 1
source "$VENV_ACTIVATE"

if ! pgrep -f "python3.* bot\.py" > /dev/null 2>&1; then
    nohup python3 bot.py >> "$DIR/bot.log" 2>&1 &
    disown
fi

if ! pgrep -f "python3.* main\.py" > /dev/null 2>&1; then
    nohup python3 main.py >> "$DIR/userbot.log" 2>&1 &
    disown
fi
