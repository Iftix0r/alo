#!/bin/bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$DIR/bot.log"
PID_FILE="$DIR/bot.pid"

if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "✅ Bot allaqachon ishlamoqda (PID: $(cat $PID_FILE))"
    exit 0
fi

cd "$DIR"
nohup python3 bot.py >> "$LOG" 2>&1 &
echo $! > "$PID_FILE"
echo "🚀 Bot ishga tushdi (PID: $!)"
echo "📄 Log: $LOG"
