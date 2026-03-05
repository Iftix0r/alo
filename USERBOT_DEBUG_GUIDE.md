# Userbot Message Sending Debug Guide

## Problem
Userbot messages ("Mijoz: [Name]") are not being sent to groups despite the bot API messages working correctly.

## Changes Made

### 1. Enhanced Error Handling
- Added `traceback.print_exc()` to print full stack traces for debugging
- Added exception type information (`type(e).__name__`) to error messages
- Added more granular debug print statements

### 2. Debug Output
The following debug information is now printed:
```
🔍 Userbot Debug: user_id={user_id}, user_name={user_name}
🔍 Userbot Debug: user_id > 0 = {user_id > 0}
📤 Userbot xabari tayyorlandi: {userbot_message}
📤 Buyurtma guruhiga yuborilmoqda: {ORDER_GROUP_ID}
✅ Userbot orqali buyurtma guruhiga yuborildi: Mijoz {user_name} (Message ID: {result.id})
```

### 3. Code Structure
The userbot message sending code is properly placed:
- Inside the main `try` block that handles message processing
- AFTER the bot API message sending section
- AFTER the "Qo'shimcha guruhlar" (additional groups) section
- In its own try-except block for error isolation

## Testing Steps

### Step 1: Run the bot
```bash
python main.py
```

### Step 2: Send a test message
Send a message to one of the monitored groups that contains a passenger keyword (e.g., "kerak", "ketish kerak", etc.)

### Step 3: Check the output
Look for the debug messages:
- If you see `🔍 Userbot Debug:` messages, the code is being reached
- If you see `📤 Userbot xabari tayyorlandi:`, the message is being prepared
- If you see `📤 Buyurtma guruhiga yuborilmoqda:`, the send attempt is being made
- If you see `✅ Userbot orqali buyurtma guruhiga yuborildi:`, the message was sent successfully
- If you see `❌ Userbot buyurtma guruhiga yuborishda xatolik:`, there's an error

### Step 4: Check for error messages
If there's an error, you should see:
- The error type (e.g., `ChannelPrivateError`, `ChatWriteForbiddenError`, etc.)
- The full error message
- A Python traceback

## Possible Issues and Solutions

### Issue 1: Permission Denied
**Error**: `ChatWriteForbiddenError` or `ChannelPrivateError`
**Solution**: The userbot account doesn't have permission to send messages in the group. Make sure:
- The userbot account is a member of the group
- The userbot account is not restricted
- The group settings allow the userbot to send messages

### Issue 2: Invalid Chat ID
**Error**: `ValueError` or `TypeError` related to chat ID
**Solution**: The chat ID format might be incorrect. Verify:
- The group IDs in `groups.json` are in the correct format (-100XXXXXXXXX)
- The ORDER_GROUP_ID in `.env` is correct

### Issue 3: Client Not Connected
**Error**: `ConnectionError` or similar
**Solution**: The Telethon client might not be properly connected. Check:
- The userbot session is valid
- The API credentials are correct
- The internet connection is stable

### Issue 4: Silent Failure
**Symptom**: No error messages, but messages not appearing
**Solution**: This could be due to:
- Messages being sent to the wrong group
- Messages being deleted by group settings
- Rate limiting (Telegram limits message sending)

## Next Steps

1. Run the bot and send a test message
2. Check the console output for debug messages
3. If you see error messages, share them for further debugging
4. If messages are being sent but not appearing, check group settings
5. If the code is not being reached, there might be an issue with the handler function

## Test Script

A test script `test_userbot_send.py` has been created to test userbot message sending independently:

```bash
python test_userbot_send.py
```

This will:
1. Connect the userbot
2. Verify it's authorized
3. Send a test message to ORDER_GROUP_ID
4. Report success or failure

## Code Location

The userbot message sending code is in `main.py` at approximately line 703-750.

Key variables:
- `user_id`: The ID of the user who sent the message
- `user_name`: The name of the user
- `userbot_message`: The formatted message to send
- `ORDER_GROUP_ID`: The main order group ID
- `monitored_groups`: List of groups to send messages to
