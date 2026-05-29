#!/bin/bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/bot.pid"

# Eski processni to'xtatish
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "🛑 Bot to'xtatildi (PID: $PID)"
        sleep 2
    fi
    rm -f "$PID_FILE"
fi

# python3 bot.py va main.py processlarini ham o'ldirish
pkill -f "python3 bot.py" 2>/dev/null
pkill -f "python3 main.py" 2>/dev/null
sleep 1

# Qayta ishga tushirish
cd "$DIR"
nohup python3 bot.py >> "$DIR/bot.log" 2>&1 &
echo $! > "$PID_FILE"
echo "🔄 Bot qayta ishga tushdi (PID: $!)"
