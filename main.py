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


def load_groups():
    try:
        with open('groups.json', 'r') as f:
            data = json.load(f)
            return [g for g in data if isinstance(g, int)] if isinstance(data, list) else []
    except:
        return []


def save_groups(groups):
    with open('groups.json', 'w') as f:
        json.dump(list(set(groups)), f, indent=2)


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
            sana DATETIME DEFAULT CURRENT_TIMESTAMP)''')
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

        cursor.execute("PRAGMA table_info(zakazlar)")
        if 'order_number' not in [c[1] for c in cursor.fetchall()]:
            cursor.execute('ALTER TABLE zakazlar ADD COLUMN order_number INTEGER')

        cursor.execute('SELECT COUNT(*) FROM keywords WHERE type=?', ('passenger',))
        if cursor.fetchone()[0] == 0:
            for w in ["kerak", "ketish kerak", "olib keting", "yo'lovchi kerak", "borish kerak", "ketmoqchiman"]:
                cursor.execute('INSERT OR IGNORE INTO keywords (type, word) VALUES (?,?)', ('passenger', w))

        cursor.execute('SELECT COUNT(*) FROM keywords WHERE type=?', ('driver',))
        if cursor.fetchone()[0] == 0:
            for w in ["ketaman", "boraman", "olib ketaman", "haydovchiman", "mashina bor", "taksi"]:
                cursor.execute('INSERT OR IGNORE INTO keywords (type, word) VALUES (?,?)', ('driver', w))

        conn.commit()


def load_keywords():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT word FROM keywords WHERE type=?', ('passenger',))
            p = [r[0] for r in cursor.fetchall()]
            cursor.execute('SELECT word FROM keywords WHERE type=?', ('driver',))
            d = [r[0] for r in cursor.fetchall()]
            return {'passenger': p, 'driver': d}
    except:
        return {'passenger': [], 'driver': []}


def is_user_blocked(user_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM blocked_users WHERE user_id=?', (user_id,))
            return cursor.fetchone() is not None
    except:
        return False


def save_zakaz(user_id, user_name, username, phone, user_type, message, group_name, group_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO users
            (user_id, user_name, username, phone, first_seen, last_seen) VALUES
            (?, ?, ?, ?, COALESCE((SELECT first_seen FROM users WHERE user_id=?), CURRENT_TIMESTAMP), CURRENT_TIMESTAMP)''',
            (user_id, user_name, username, phone, user_id))
        cursor.execute('SELECT COALESCE(MAX(order_number),0)+1 FROM zakazlar')
        num = cursor.fetchone()[0]
        cursor.execute('''INSERT INTO zakazlar (order_number, user_id, user_type, message, group_name, group_id)
            VALUES (?,?,?,?,?,?)''', (num, user_id, user_type, message, group_name, group_id))
        cursor.execute('''DELETE FROM zakazlar WHERE id NOT IN
            (SELECT id FROM zakazlar ORDER BY sana DESC LIMIT 50)''')
        conn.commit()
        return num


def is_fast_message(text):
    if not text or len(text) >= 60:
        return False
    return not re.search(
        u"[\U0001F300-\U0001FFFF\U00002600-\U000027BF\U0001F900-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]+",
        text)


async def auto_discover_groups(client):
    monitored = set(load_groups())
    try:
        async for dialog in client.iter_dialogs():
            e = dialog.entity
            gid = None
            if isinstance(e, Channel) and getattr(e, 'megagroup', False):
                gid = int(f"-100{e.id}") if e.id > 0 else e.id
            elif isinstance(e, Chat) and not getattr(e, 'broadcast', False):
                gid = -e.id if e.id > 0 else e.id
            if gid and gid != ORDER_GROUP_ID and gid < 0:
                monitored.add(gid)
    except Exception as ex:
        logger.error(f"Guruh topishda xatolik: {ex}")
    save_groups(list(monitored))
    logger.info(f"Guruhlar yangilandi: {len(monitored)} ta")


async def send_to_groups(text, buttons, base_text):
    payload = {
        "chat_id": ORDER_GROUP_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": buttons} if buttons else None
    }
    async with aiohttp.ClientSession() as s:
        r = await s.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)
        if r.status != 200:
            logger.error(f"Xatolik: {r.status} - {await r.text()}")

    if FAST_GROUP_ID and is_fast_message(base_text):
        fast = {**payload, "chat_id": FAST_GROUP_ID}
        async with aiohttp.ClientSession() as s:
            await s.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=fast)


def attach_handlers(client):
    @client.on(events.NewMessage(incoming=True))
    async def on_message(event):
        if event.action is not None:
            return
        if not event.is_group and not event.is_private:
            return
        if event.is_group and event.chat_id == ORDER_GROUP_ID:
            return
        if event.is_group and event.chat_id not in load_groups():
            return
        if event.message.fwd_from:
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

        text = event.text or ""
        if not text.strip():
            return

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        base = lines[-1] if lines else text

        kw = load_keywords()
        tl = base.lower()
        if any(w.lower() in tl for w in kw['driver']):
            return
        if not any(w.lower() in tl for w in kw['passenger']):
            return

        uid = sender.id if sender else 0
        uname = ""
        username = ""
        phone = ""
        user_link = "Foydalanuvchi"

        if sender:
            uname = (sender.first_name or "").strip()
            if getattr(sender, 'last_name', None):
                uname += f" {sender.last_name}"
            username = getattr(sender, 'username', '') or ''
            phone = getattr(sender, 'phone', '') or ''
            user_link = f"<a href='tg://user?id={uid}'>{uname or 'Nomaʼlum'}</a>"

        chat = None
        try:
            chat = await event.get_chat()
        except:
            pass

        chat_title = getattr(chat, 'title', 'Guruh') or 'Guruh'
        blocked = is_user_blocked(uid)
        save_zakaz(uid, uname.strip(), username, phone, '🙋♂️ Yolovchi', text, chat_title, event.chat_id)

        if blocked:
            try:
                await event.delete()
            except:
                pass
            return

        # Kontakt qatori
        details = []
        if username:
            details.append(f"🤙 @{username}")
        if phone:
            details.append(f"☎️ +{phone}")

        # Telefon raqam xabardan
        phones = []
        for pat in [r'\+998\d{9}', r'998\d{9}', r'0\d{9}']:
            phones = re.findall(pat, text)
            if phones:
                break

        # Havola
        msg_link = "#"
        grp_url = None
        if chat:
            cid = str(chat.id)
            if cid.startswith('-100'):
                num = cid[4:]
                msg_link = f"https://t.me/c/{num}/{event.id}"
                grp_url = f"https://t.me/c/{num}"
            elif getattr(chat, 'username', None):
                msg_link = f"https://t.me/{chat.username}/{event.id}"
                grp_url = f"https://t.me/{chat.username}"

        parts = [f"👤 {user_link}", f"💬 {base.strip()}"]
        if details:
            parts.append("\n".join(details))
        msg_text = "\n\n".join(parts)

        buttons = []
        row1 = []
        if msg_link != "#":
            row1.append({"text": "💬 Xabar", "url": msg_link})
        if grp_url:
            row1.append({"text": f"🫂 {chat_title[:20]}", "url": grp_url})
        if row1:
            buttons.append(row1)

        ph = None
        if phones:
            p = phones[0].replace(' ', '').replace('-', '')
            ph = ('+' + p) if p.startswith('998') else ('+998' + p if not p.startswith('+') else p)
        elif phone:
            ph = f"+{phone}"
        if ph:
            buttons.append([{"text": f"📞 {ph}", "url": f"https://onmap.uz/tel/{ph}"}])

        if uid:
            buttons.append([{"text": "✍️ Mijozga yozish", "callback_data": f"reply_user_{uid}"}])
            buttons.append([{"text": "🚫 Bloklash", "callback_data": f"block_{uid}"}])

        await send_to_groups(msg_text, buttons, base)

    @client.on(events.ChatAction)
    async def on_action(event):
        if event.chat_id == ORDER_GROUP_ID:
            return
        me = await client.get_me()
        groups = load_groups()
        if (event.user_left or event.user_kicked) and event.user_id == me.id:
            if event.chat_id in groups:
                groups.remove(event.chat_id)
                save_groups(groups)
        if (event.user_joined or event.user_added) and event.user_id == me.id:
            if event.chat_id not in groups:
                groups.append(event.chat_id)
                save_groups(groups)


async def start_client(phone):
    session = f"session_{phone.replace('+', '')}"
    client = TelegramClient(session, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        logger.warning(f"❌ Session yo'q: {phone} — bot orqali ulang")
        await client.disconnect()
        return None

    me = await client.get_me()
    logger.info(f"✅ Ulandi: {me.first_name} ({phone})")
    attach_handlers(client)
    await auto_discover_groups(client)
    return client


async def main():
    print("=" * 50)
    print("🤖 MULTI-ACCOUNT USERBOT ISHGA TUSHMOQDA")
    print("=" * 50)
    init_database()

    accounts = load_accounts()
    if not accounts:
        print("⚠️  Akaunt yo'q. Bot orqali qo'shing: 👤 Akauntlar → ➕")
        await asyncio.sleep(float('inf'))
        return

    clients = []
    for acc in accounts:
        phone = acc.get('phone')
        if phone:
            c = await start_client(phone)
            if c:
                clients.append(c)

    if not clients:
        print("⚠️  Hech qanday faol akaunt topilmadi. Bot orqali qayta ulang.")
        await asyncio.sleep(float('inf'))
        return

    print(f"✅ {len(clients)} ta akaunt ishga tushdi")
    await asyncio.gather(*[c.run_until_disconnected() for c in clients])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 To'xtatildi")
