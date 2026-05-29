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

pkill -f "python3 bot.py" 2>/dev/null
pkill -f "python3 main.py" 2>/dev/null
sleep 1

# Git pull
cd "$DIR"
echo "📥 Git pull..."
git pull origin main 2>&1 | tail -5

# Python cache tozalash
echo "🧹 Cache tozalanmoqda..."
find "$DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find "$DIR" -name "*.pyc" -delete 2>/dev/null
echo "✅ Cache tozalandi"

# Dependencylarni o'rnatish
echo "📦 pip install..."
pip install -r "$DIR/requirements.txt" -q
echo "✅ Paketlar o'rnatildi"

# Qayta ishga tushirish
nohup python3 bot.py >> "$DIR/bot.log" 2>&1 &
echo $! > "$PID_FILE"
echo "🔄 Bot qayta ishga tushdi (PID: $!)"
