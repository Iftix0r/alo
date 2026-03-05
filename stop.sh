#!/bin/bash

# Userbot va Bot to'xtarish skripti
# Foydalanish: ./stop.sh

# Ranglar
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Botni to'xtarish
stop_bot() {
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}🛑 BOT VA USERBOT TO'XTATILMOQDA...${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo ""
    
    if [ ! -f "bot.pid" ]; then
        echo -e "${YELLOW}⚠️  bot.pid fayli topilmadi${NC}"
        echo -e "${YELLOW}Bot allaqachon to'xtatilgan bo'lishi mumkin${NC}"
        
        # Barcha Python jarayonlarini topish va to'xtarish
        echo -e "${BLUE}🔍 Barcha Python jarayonlarini qidirilmoqda...${NC}"
        
        PIDS=$(pgrep -f "python3 main.py\|python3 bot.py" || true)
        
        if [ -z "$PIDS" ]; then
            echo -e "${GREEN}✅ Hech qanday Python jarayoni topilmadi${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}Topilgan jarayonlar: $PIDS${NC}"
        kill $PIDS 2>/dev/null || true
        sleep 1
        
        # Kuchli to'xtarish
        kill -9 $PIDS 2>/dev/null || true
        
        echo -e "${GREEN}✅ Jarayonlar to'xtatildi${NC}"
        return 0
    fi
    
    # PID larni o'qish
    PIDS=$(cat bot.pid)
    
    if [ -z "$PIDS" ]; then
        echo -e "${YELLOW}⚠️  bot.pid faylida PID topilmadi${NC}"
        rm -f bot.pid
        return 0
    fi
    
    echo -e "${BLUE}📋 To'xtatilayotgan jarayonlar:${NC}"
    
    # Har bir PID ni to'xtarish
    for PID in $PIDS; do
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}   Jarayon to'xtatilmoqda (PID: $PID)...${NC}"
            
            # Yumshoq to'xtarish
            kill $PID 2>/dev/null || true
            
            # 3 soniya kutish
            sleep 3
            
            # Agar hali ishga tushgan bo'lsa, kuchli to'xtarish
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${YELLOW}   Kuchli to'xtarish...${NC}"
                kill -9 $PID 2>/dev/null || true
            fi
            
            echo -e "${GREEN}   ✅ Jarayon to'xtatildi${NC}"
        else
            echo -e "${YELLOW}   ⚠️  Jarayon topilmadi (PID: $PID)${NC}"
        fi
    done
    
    # PID faylini o'chirish
    rm -f bot.pid
    
    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ BARCHA JARAYONLAR TO'XTATILDI!${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
}

# Status tekshirish
check_status() {
    echo ""
    echo -e "${BLUE}📊 Jarayonlar statusi:${NC}"
    
    RUNNING=$(pgrep -f "python3 main.py\|python3 bot.py" | wc -l)
    
    if [ $RUNNING -eq 0 ]; then
        echo -e "${GREEN}✅ Barcha jarayonlar to'xtatilgan${NC}"
    else
        echo -e "${YELLOW}⚠️  Hali ham $RUNNING ta jarayon ishga tushgan${NC}"
        pgrep -f "python3 main.py\|python3 bot.py" -a
    fi
}

# Loglarni tozalash (ixtiyoriy)
cleanup_logs() {
    if [ "$1" == "--clean-logs" ]; then
        echo ""
        echo -e "${BLUE}🧹 Loglar tozalanmoqda...${NC}"
        
        if [ -d "logs" ]; then
            rm -f logs/*.log
            echo -e "${GREEN}✅ Loglar tozalandi${NC}"
        fi
    fi
}

# Asosiy skript
main() {
    stop_bot
    check_status
    cleanup_logs "$1"
    
    echo ""
    echo -e "${BLUE}💡 Qayta ishga tushirish uchun:${NC}"
    echo -e "   ./start.sh"
}

# Skriptni ishga tushirish
main "$@"
