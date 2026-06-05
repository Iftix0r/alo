from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat
import asyncio
import aiohttp
import os
import json
import sqlite3
import re
import logging
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('userbot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ORDER_GROUP_ID = int(os.getenv('ORDER_GROUP_ID'))
FAST_GROUP_ID = int(os.getenv('FAST_GROUP_ID', '0'))

# Barcha ishlaydigan clientlar
active_clients = {}  # phone -> TelegramClient


@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect('zakazlar.db', timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def load_accounts():
    try:
        with open('accounts.json', 'r') as f:
            return json.load(f)
    except:
        return []


def save_accounts(accounts):
    with open('accounts.json', 'w') as f:
        json.dump(accounts, f, indent=2)


def load_groups():
    try:
        with open('groups.json', 'r') as f:
            data = json.load(f)
            return [g for g in data if isinstance(g, int)] if isinstance(data, list) else []
    except:
        return []


def save_groups(groups):
    with open('groups.json', 'w') as f:
        json.dump(groups, f, indent=2)


def load_keywords_from_db():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT word FROM keywords WHERE type = ?', ('passenger',))
            passenger_words = [row[0] for row in cursor.fetchall()]
            cursor.execute('SELECT word FROM keywords WHERE type = ?', ('driver',))
            driver_words = [row[0] for row in cursor.fetchall()]
            return {"passenger": passenger_words, "driver": driver_words}
    except Exception as e:
        logger.error(f"Keywords yuklashda xatolik: {e}")
        return {"passenger": [], "driver": []}


def init_database():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, user_name TEXT, username TEXT, phone TEXT,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS zakazlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT, order_number INTEGER,
            user_id INTEGER, user_type TEXT, message TEXT,
            group_name TEXT, group_id INTEGER,
            sana DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS blocked_users (
            user_id INTEGER PRIMARY KEY,
            blocked_date DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL,
            word TEXT NOT NULL, sana DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(type, word))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS order_groups (
            group_id INTEGER PRIMARY KEY, group_name TEXT,
            added_date DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            added_date DATETIME DEFAULT CURRENT_TIMESTAMP)''')

        # order_number ustunini tekshirish
        cursor.execute("PRAGMA table_info(zakazlar)")
        columns = [c[1] for c in cursor.fetchall()]
        if 'order_number' not in columns:
            cursor.execute('ALTER TABLE zakazlar ADD COLUMN order_number INTEGER')

        # Default kalit so'zlar
        cursor.execute('SELECT COUNT(*) FROM keywords WHERE type = ?', ('passenger',))
        if cursor.fetchone()[0] == 0:
            for w in ["kerak", "ketish kerak", "olib keting", "yo'lovchi kerak", "borish kerak", "ketmoqchiman"]:
                cursor.execute('INSERT OR IGNORE INTO keywords (type, word) VALUES (?, ?)', ('passenger', w))

        cursor.execute('SELECT COUNT(*) FROM keywords WHERE type = ?', ('driver',))
        if cursor.fetchone()[0] == 0:
            for w in ["ketaman", "boraman", "olib ketaman", "haydovchiman", "mashina bor", "taksi"]:
                cursor.execute('INSERT OR IGNORE INTO keywords (type, word) VALUES (?, ?)', ('driver', w))

        conn.commit()
        logger.info("Database initialized")


def is_user_blocked(user_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM blocked_users WHERE user_id = ?', (user_id,))
            return cursor.fetchone() is not None
    except:
        return False


def save_user_and_zakaz(user_id, user_name, username, phone, user_type, message, group_name, group_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO users
            (user_id, user_name, username, phone, first_seen, last_seen)
            VALUES (?, ?, ?, ?,
                COALESCE((SELECT first_seen FROM users WHERE user_id = ?), CURRENT_TIMESTAMP),
                CURRENT_TIMESTAMP)''', (user_id, user_name, username, phone, user_id))
        cursor.execute('SELECT COALESCE(MAX(order_number), 0) + 1 FROM zakazlar')
        next_num = cursor.fetchone()[0]
        cursor.execute('''INSERT INTO zakazlar (order_number, user_id, user_type, message, group_name, group_id)
            VALUES (?, ?, ?, ?, ?, ?)''', (next_num, user_id, user_type, message, group_name, group_id))
        cursor.execute('''DELETE FROM zakazlar WHERE id NOT IN (
            SELECT id FROM zakazlar ORDER BY sana DESC LIMIT 50)''')
        conn.commit()
        return next_num


def is_fast_message(text):
    if not text or len(text) >= 60:
        return False
    emoji_pattern = re.compile(
        u"[\U0001F300-\U0001FFFF\U00002600-\U000027BF\U0001F900-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]+",
        re.UNICODE)
    return not emoji_pattern.search(text)


async def auto_discover_groups(client):
    """Berilgan client uchun guruhlarni topib groups.json ga saqlash"""
    monitored = set(load_groups())
    me = await client.get_me()
    logger.info(f"Guruhlar yuklanmoqda: @{me.username or me.id}")
    try:
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            group_id = None
            if isinstance(entity, Channel) and getattr(entity, 'megagroup', False):
                group_id = int(f"-100{entity.id}") if entity.id > 0 else entity.id
            elif isinstance(entity, Chat) and not getattr(entity, 'broadcast', False):
                group_id = -entity.id if entity.id > 0 else entity.id
            else:
                continue
            if group_id and group_id != ORDER_GROUP_ID and group_id < 0:
                monitored.add(group_id)
    except Exception as e:
        logger.error(f"Guruh topishda xatolik: {e}")

    save_groups(list(monitored))
    logger.info(f"Jami {len(monitored)} guruh saqlandi")
    return list(monitored)


async def send_order_to_groups(message_text, buttons, base_text):
    """Zakaz xabarini ORDER_GROUP_ID va FAST_GROUP_ID ga yuborish"""
    payload = {
        "chat_id": ORDER_GROUP_ID,
        "text": message_text,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": buttons} if buttons else None
    }
    async with aiohttp.ClientSession() as session:
        resp = await session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)
        if resp.status != 200:
            err = await resp.text()
            logger.error(f"Guruhga yuborishda xatolik: {resp.status} - {err}")

    if FAST_GROUP_ID and is_fast_message(base_text):
        fast_payload = {**payload, "chat_id": FAST_GROUP_ID}
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=fast_payload)


def make_handler(client):
    """Har bir client uchun alohida handler yaratish"""

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.action is not None:
            return
        if not event.is_group and not event.is_private:
            return
        if event.is_group and event.chat_id == ORDER_GROUP_ID:
            return

        monitored_groups = load_groups()
        if event.is_group and event.chat_id not in monitored_groups:
            return

        me = await client.get_me()
        bot_id = int(BOT_TOKEN.split(':')[0])

        if event.sender_id in (me.id, bot_id):
            return

        try:
            sender = await event.get_sender()
        except:
            sender = None

        if sender and getattr(sender, 'is_bot', False):
            return

        if event.message.fwd_from:
            return

        text_content = event.text or ""
        if not text_content.strip():
            return

        lines = [l.strip() for l in text_content.splitlines() if l.strip()]
        base_text = lines[-1] if lines else text_content

        keywords = load_keywords_from_db()
        text_lower = base_text.lower()

        if any(w.lower() in text_lower for w in keywords['driver']):
            return
        if not any(w.lower() in text_lower for w in keywords['passenger']):
            return

        user_id = sender.id if sender else 0
        user_name = ""
        username = ""
        phone = ""
        user_info = "Foydalanuvchi"

        if sender:
            user_name = f"{sender.first_name or ''}".strip()
            if getattr(sender, 'last_name', None):
                user_name += f" {sender.last_name}"
            username = getattr(sender, 'username', '') or ''
            phone = getattr(sender, 'phone', '') or ''
            user_info = f"<a href='tg://user?id={sender.id}'>{user_name or 'Nomaʼlum'}</a>"

        chat = None
        try:
            chat = await event.get_chat()
        except:
            pass

        chat_title = getattr(chat, 'title', 'Nomaʼlum guruh') or 'Nomaʼlum guruh'
        is_blocked = is_user_blocked(user_id)
        save_user_and_zakaz(user_id, user_name.strip(), username, phone,
                            '🙋♂️ Yolovchi', text_content, chat_title, event.chat_id)

        if is_blocked:
            try:
                await event.delete()
            except Exception as e:
                logger.error(f"Bloklangan xabar o'chirishda xatolik: {e}")
            return

        # Kontakt ma'lumotlari
        user_details_parts = []
        if username:
            user_details_parts.append(f"🤙 @{username}")
        if phone:
            user_details_parts.append(f"☎️ +{phone}")
        user_details = "\n".join(user_details_parts)

        # Telefon raqam xabar matnidan
        phone_patterns = [r'\+998\d{9}', r'998\d{9}', r'\d{9}']
        phones = []
        for pattern in phone_patterns:
            phones = re.findall(pattern, text_content)
            if phones:
                break

        # Havola yaratish
        message_link = "#"
        group_url = None
        if chat:
            chat_id_str = str(chat.id)
            if chat_id_str.startswith('-100'):
                num = chat_id_str[4:]
                message_link = f"https://t.me/c/{num}/{event.id}"
                group_url = f"https://t.me/c/{num}"
            elif getattr(chat, 'username', None):
                message_link = f"https://t.me/{chat.username}/{event.id}"
                group_url = f"https://t.me/{chat.username}"

        # Xabar matni
        parts = [f"👤 {user_info}", f"💬 {base_text.strip()}"]
        if user_details:
            parts.append(user_details)
        message_text = "\n\n".join(parts)

        # Tugmalar
        buttons = []
        first_row = []
        if message_link != "#":
            first_row.append({"text": "💬 Xabar", "url": message_link})
        if group_url:
            first_row.append({"text": f"🫂 {chat_title[:20]}", "url": group_url})
        if first_row:
            buttons.append(first_row)

        phone_str = None
        if phones:
            p = phones[0].replace(' ', '').replace('-', '')
            if p.startswith('998'):
                p = '+' + p
            elif not p.startswith('+998'):
                p = '+998' + p
            phone_str = p
        elif phone:
            phone_str = f"+{phone}"

        if phone_str:
            buttons.append([{"text": f"📞 {phone_str}", "url": f"https://onmap.uz/tel/{phone_str}"}])

        if user_id:
            buttons.append([{"text": "✍️ Mijozga yozish", "callback_data": f"reply_user_{user_id}"}])
            buttons.append([{"text": "🚫 Bloklash", "callback_data": f"block_{user_id}"}])

        await send_order_to_groups(message_text, buttons, base_text)

    @client.on(events.ChatAction)
    async def chat_action_handler(event):
        me = await client.get_me()
        if event.chat_id == ORDER_GROUP_ID:
            return
        monitored = load_groups()
        if (event.user_left or event.user_kicked) and event.user_id == me.id:
            if event.chat_id in monitored:
                monitored.remove(event.chat_id)
                save_groups(monitored)
        if (event.user_joined or event.user_added) and event.user_id == me.id:
            if event.chat_id not in monitored:
                monitored.append(event.chat_id)
                save_groups(monitored)


async def start_account(phone):
    """Saqlangan sessiondan clientni ishga tushirish"""
    session_name = f"session_{phone.replace('+', '')}"
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        logger.warning(f"Akaunt avtorizatsiya qilinmagan: {phone}")
        await client.disconnect()
        return None

    me = await client.get_me()
    logger.info(f"✅ Akaunt ulandi: {me.first_name} ({phone})")

    make_handler(client)
    await auto_discover_groups(client)

    active_clients[phone] = client
    return client


async def start_all_accounts():
    """Barcha saqlangan akauntlarni ishga tushirish"""
    accounts = load_accounts()
    if not accounts:
        logger.info("Ulangan akauntlar yo'q. Bot orqali qo'shing.")
        return

    tasks = []
    for acc in accounts:
        phone = acc.get('phone')
        if phone:
            tasks.append(start_account(phone))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    started = sum(1 for r in results if r is not None and not isinstance(r, Exception))
    logger.info(f"{started}/{len(accounts)} akaunt ishga tushdi")


async def main():
    print("=" * 50)
    print("🤖 MULTI-ACCOUNT USERBOT ISHGA TUSHMOQDA...")
    print("=" * 50)
    init_database()

    await start_all_accounts()

    accounts = load_accounts()
    if not accounts:
        print("⚠️  Hech qanday akaunt ulanmagan.")
        print("Bot orqali akaunt qo'shish uchun /accounts buyrug'ini yuboring.")

    # Barcha clientlarni bir vaqtda ishga tushirish
    if active_clients:
        print(f"✅ {len(active_clients)} ta akaunt faol")
        await asyncio.gather(*[c.run_until_disconnected() for c in active_clients.values()])
    else:
        # Akaunt bo'lmasa ham dastur ishlab turishi kerak
        await asyncio.sleep(float('inf'))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Userbot to'xtatildi")
