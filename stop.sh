#!/bin/bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/bot.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "🛑 Bot to'xtatildi (PID: $PID)"
    else
        echo "⚠️  Process allaqachon to'xtatilgan"
    fi
    rm -f "$PID_FILE"
fi

pkill -f "python3 bot.py" 2>/dev/null
pkill -f "python3 main.py" 2>/dev/null
echo "✅ Barcha bot processlari to'xtatildi"
