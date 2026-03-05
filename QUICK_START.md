# Quick Start Guide - Userbot Message Sending

## What Was Fixed

The userbot message sending feature ("Mijoz: [Name]" messages) has been enhanced with:
- Better error handling
- Duplicate prevention
- Improved debug output
- Rate limiting

## How to Test

### Step 1: Start the Bot
```bash
python main.py
```

### Step 2: Send a Test Message
Send a message to any monitored group that contains a passenger keyword:
- "kerak" (need)
- "ketish kerak" (need to go)
- "olib keting" (pick me up)
- "yo'lovchi kerak" (need a passenger)
- "borish kerak" (need to go)
- "ketmoqchiman" (I want to go)

### Step 3: Check the Results

**In the group, you should see:**
1. Bot API message (with order number, user name, message, phone)
2. Userbot message (with "Mijoz: [Name]")

**In the console, you should see:**
```
✅ User ID olindi: [user_id]
🔍 Userbot Debug: user_id=[user_id], user_name=[name]
📤 Userbot xabari tayyorlandi: Mijoz: <a href='tg://user?id=[user_id]'>[name]</a>
📤 Buyurtma guruhiga yuborilmoqda: -1003417191538
✅ Userbot orqali buyurtma guruhiga yuborildi: Mijoz [name] (Message ID: [id])
```

## If It Doesn't Work

### Check 1: Is the bot running?
```bash
# You should see:
# ✅ USERBOT MUVAFFAQIYATLI ISHGA TUSHDI!
```

### Check 2: Are groups loaded?
```bash
# You should see:
# 📊 Kuzatilayotgan guruhlar: [number]
```

### Check 3: Is the message being captured?
```bash
# You should see:
# ✅ User ID olindi: [user_id]
```

### Check 4: Are there error messages?
Look for messages starting with:
- `❌ Userbot buyurtma guruhiga yuborishda xatolik:`
- `❌ Userbot guruhga yuborishda xatolik:`

If you see these, share the error message for debugging.

## Common Issues

| Issue | Solution |
|-------|----------|
| No "Mijoz" message | Check console for errors, verify userbot permissions |
| Duplicate messages | Verify ORDER_GROUP_ID is not in monitored_groups |
| Wrong user name | Check that sender has first_name attribute |
| Messages not appearing | Check group settings, verify userbot is member |

## Debug Output Meanings

| Message | Meaning |
|---------|---------|
| `🔍 Userbot Debug:` | Userbot message sending started |
| `📤 Userbot xabari tayyorlandi:` | Message formatted successfully |
| `📤 Buyurtma guruhiga yuborilmoqda:` | Attempting to send to ORDER_GROUP |
| `✅ Userbot orqali ... yuborildi:` | Message sent successfully |
| `❌ Userbot ... xatolik:` | Error sending message |

## Files to Review

- `main.py` - Main implementation (lines 703-750)
- `USERBOT_DEBUG_GUIDE.md` - Detailed debugging guide
- `CHANGES_SUMMARY.md` - Summary of changes
- `IMPLEMENTATION_COMPLETE.md` - Complete documentation

## Test Script

To test userbot connectivity independently:
```bash
python test_userbot_send.py
```

This will:
1. Connect the userbot
2. Verify authorization
3. Send a test message to ORDER_GROUP_ID
4. Report success or failure

## Need Help?

1. Check the console output for error messages
2. Review the USERBOT_DEBUG_GUIDE.md
3. Run test_userbot_send.py to verify connectivity
4. Share error messages for further debugging

---

**Status**: ✅ Ready for testing
**Last Updated**: 2026-03-05
