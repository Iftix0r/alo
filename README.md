# 🚕 Taksi Zakaz Bot

Telegram guruhlardan yo'lovchi zakazlarini avtomatik yig'ib, buyurtma guruhiga yuboruvchi bot.

## ⚙️ Qanday ishlaydi

- **Userbot** (`main.py`) — Telegram guruhlarni kuzatadi, yo'lovchi so'zlarini aniqlaydi va zakazni formatlaydi
- **Bot** (`bot.py`) — Admin panel, statistika, so'z boshqaruvi va taksi zakaz qabul qilish

## 🚀 O'rnatish

```bash
pip install -r requirements.txt
```

`.env` fayl yarating:

```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
ORDER_GROUP_ID=-100xxxxxxxxxx
ADMIN_IDS=123456789
```

Ishga tushirish:

```bash
python bot.py
```

> `bot.py` avtomatik ravishda `main.py` (userbot) ni ham ishga tushiradi.

## 📋 Asosiy imkoniyatlar

| Funksiya | Tavsif |
|---|---|
| 🔍 Guruh kuzatuvi | Akkauntdagi barcha guruhlarni avtomatik topadi |
| 🙋 Yo'lovchi aniqlash | Kalit so'zlar orqali yo'lovchi/haydovchini farqlaydi |
| 🚫 Bloklash | Spam foydalanuvchilarni bloklash va xabarini o'chirish |
| 📊 Statistika | Zakazlar, guruhlar va foydalanuvchilar statistikasi |
| 🔎 Qidiruv | Ism yoki ID orqali zakaz qidirish |

## 🤖 Admin buyruqlari (userbot)

```
/add_group -100xxx   — Guruh qo'shish
/remove_group -100xxx — Guruh o'chirish
/groups              — Guruhlar ro'yxati
/block 123456        — Foydalanuvchini bloklash
/unblock 123456      — Blokdan chiqarish
/blocked             — Bloklangan ro'yxat
```

## 🗄️ Ma'lumotlar bazasi

SQLite (`zakazlar.db`) — foydalanuvchilar, zakazlar, kalit so'zlar, bloklangan foydalanuvchilar.

## 📦 Texnologiyalar

- [Telethon](https://github.com/LonamiWebs/Telethon) — Userbot
- [aiogram](https://github.com/aiogram/aiogram) — Bot
- SQLite — Ma'lumotlar bazasi
# Userbor_global
