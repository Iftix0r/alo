#!/usr/bin/env python3
"""
Userbot message sending test script
"""
import asyncio
from telethon import TelegramClient
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
ORDER_GROUP_ID = int(os.getenv('ORDER_GROUP_ID'))

client = TelegramClient('userbot', API_ID, API_HASH)

async def test_send():
    await client.connect()
    
    if not await client.is_user_authorized():
        print("❌ Userbot authorized emas!")
        return
    
    me = await client.get_me()
    print(f"✅ Userbot authorized: {me.first_name} (@{me.username})")
    
    # Test message
    test_message = "🧪 Test: Userbot message sending test"
    
    try:
        print(f"📤 Sending test message to {ORDER_GROUP_ID}...")
        result = await client.send_message(ORDER_GROUP_ID, test_message)
        print(f"✅ Message sent successfully! Message ID: {result.id}")
    except Exception as e:
        print(f"❌ Error sending message: {type(e).__name__}: {e}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_send())
