#!/bin/bash

# Userbot va Bot ishga tushirish skripti
# Foydalanish: ./start.sh

set -e

# Ranglar
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Joriy direktoriyadagi fayllarni tekshirish
check_files() {
    echo -e "${BLUE}📋 Fayllarni tekshirish...${NC}"
    
    if [ ! -f "main.py" ]; then
        echo -e "${RED}❌ main.py topilmadi!${NC}"
        exit 1
    fi
    
    if [ ! -f "bot.py" ]; then
        echo -e "${RED}❌ bot.py topilmadi!${NC}"
        exit 1
    fi
    
    if [ ! -f ".env" ]; then
        echo -e "${RED}❌ .env topilmadi!${NC}"
        exit 1
    fi
    
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}❌ requirements.txt topilmadi!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Barcha fayllar topildi${NC}"
}

# Virtual environment tekshirish va yaratish
setup_venv() {
    echo -e "${BLUE}🔧 Virtual environment tekshirish...${NC}"
    
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}📦 Virtual environment yaratilmoqda...${NC}"
        python3 -m venv venv
        echo -e "${GREEN}✅ Virtual environment yaratildi${NC}"
    else
        echo -e "${GREEN}✅ Virtual environment allaqachon mavjud${NC}"
    fi
    
    # Virtual environment faollashtirish
    source venv/bin/activate
    
    # Paketlarni o'rnatish
    echo -e "${YELLOW}📥 Paketlarni o'rnatish...${NC}"
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Paketlar o'rnatildi${NC}"
}

# PID faylini tekshirish
check_running() {
    if [ -f "bot.pid" ]; then
        PID=$(cat bot.pid)
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${RED}❌ Bot allaqachon ishga tushgan (PID: $PID)${NC}"
            echo -e "${YELLOW}Avval stop.sh bilan to'xtating: ./stop.sh${NC}"
            exit 1
        else
            rm -f bot.pid
        fi
    fi
}

# Loglar uchun direktoriyadarni yaratish
setup_logs() {
    echo -e "${BLUE}📁 Log direktoriyadarni tekshirish...${NC}"
    
    if [ ! -d "logs" ]; then
        mkdir -p logs
        echo -e "${GREEN}✅ logs direktoriyadari yaratildi${NC}"
    fi
}

# Botni ishga tushirish
start_bot() {
    echo -e "${BLUE}🚀 Bot ishga tushmoqda...${NC}"
    
    # Virtual environment faollashtirish
    source venv/bin/activate
    
    # Bot va Userbot ni background da ishga tushirish
    nohup python3 main.py > logs/main.log 2>&1 &
    MAIN_PID=$!
    
    nohup python3 bot.py > logs/bot.log 2>&1 &
    BOT_PID=$!
    
    # PID larni saqlash
    echo "$MAIN_PID" > bot.pid
    echo "$BOT_PID" >> bot.pid
    
    sleep 2
    
    # Jarayonlar ishga tushganligini tekshirish
    if ps -p $MAIN_PID > /dev/null 2>&1 && ps -p $BOT_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Bot muvaffaqiyatli ishga tushdi!${NC}"
        echo -e "${GREEN}   Userbot PID: $MAIN_PID${NC}"
        echo -e "${GREEN}   Bot PID: $BOT_PID${NC}"
        echo ""
        echo -e "${BLUE}📊 Loglarni ko'rish:${NC}"
        echo -e "   Userbot: tail -f logs/main.log"
        echo -e "   Bot: tail -f logs/bot.log"
        echo ""
        echo -e "${BLUE}🛑 Botni to'xtarish:${NC}"
        echo -e "   ./stop.sh"
    else
        echo -e "${RED}❌ Bot ishga tushishda xatolik!${NC}"
        echo -e "${YELLOW}Loglarni tekshiring:${NC}"
        echo -e "   cat logs/main.log"
        echo -e "   cat logs/bot.log"
        exit 1
    fi
}

# Asosiy skript
main() {
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}🤖 USERBOT VA BOT ISHGA TUSHIRISH${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo ""
    
    check_files
    echo ""
    
    check_running
    echo ""
    
    setup_venv
    echo ""
    
    setup_logs
    echo ""
    
    start_bot
    echo ""
    
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ BARCHA JARAYONLAR ISHGA TUSHDI!${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
}

# Skriptni ishga tushirish
main
