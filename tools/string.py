import os
import asyncio
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PasswordHashInvalid, PhoneNumberInvalid
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler
)
from config import API_ID, API_HASH
from database import db

# 🔥 Import Dynamic Starter
try:
    from tools.userbot import start_new_userbot
except ImportError:
    # Fallback agar import na ho paye
    async def start_new_userbot(uid): pass

sessions_col = db["userbot_sessions"] 
PHONE, OTP, PASSWORD = range(3)
temp_clients = {}
temp_data = {}

async def start_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🟢 **Number Bhejo** (Country Code ke sath)\nExample: `+919988776655`")
    return PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    phone_number = update.message.text.strip()
    msg = await update.message.reply_text(f"🔄 Connecting... `{phone_number}`")
    
    client = Client(f"session_{user_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
    await client.connect()
    
    temp_clients[user_id] = client
    temp_data[user_id] = {"phone": phone_number}

    try:
        sent_code = await client.send_code(phone_number)
        temp_data[user_id]["hash"] = sent_code.phone_code_hash
        await msg.edit_text("✅ **OTP Bhejo** (Space dekar)\nExample: `1 2 3 4 5`")
        return OTP
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")
        await client.disconnect()
        return ConversationHandler.END

async def receive_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    otp = update.message.text.replace(" ", "")
    client = temp_clients.get(user_id)
    phone = temp_data[user_id]["phone"]
    code_hash = temp_data[user_id]["hash"]
    msg = await update.message.reply_text("🔄 Verifying...")

    try:
        await client.sign_in(phone, code_hash, otp)
    except SessionPasswordNeeded:
        await msg.edit_text("🔐 **Password Bhejo** (2FA laga hai)")
        return PASSWORD
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")
        await client.disconnect()
        return ConversationHandler.END

    return await login_success(update, client, user_id, msg)

async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    password = update.message.text
    client = temp_clients.get(user_id)
    msg = await update.message.reply_text("🔄 Checking Password...")

    try:
        await client.check_password(password)
    except Exception as e:
        await msg.edit_text(f"❌ Wrong Password: {e}")
        await client.disconnect()
        return ConversationHandler.END
    
    return await login_success(update, client, user_id, msg)

async def login_success(update, client, user_id, msg):
    session_string = await client.export_session_string()
    me = await client.get_me()
    await client.disconnect()

    user_data = {
        "user_id": user_id,
        "first_name": me.first_name,
        "username": me.username,
        "session_string": session_string,
        "is_active": True
    }
    
    sessions_col.update_one({"user_id": user_id}, {"$set": user_data}, upsert=True)
    
    # Cleanup
    if user_id in temp_clients: del temp_clients[user_id]
    
    await msg.edit_text(f"🎉 **Login Successful!**\n\nConnected as: {me.first_name}\n🚀 **Userbot Starting Automatically...**")
    
    # 🔥 MAGIC LINE: Bina restart kiye Userbot Start!
    # Background task mein daal diya taaki bot atke nahi
    asyncio.create_task(start_new_userbot(user_id))
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in temp_clients:
        await temp_clients[user_id].disconnect()
        del temp_clients[user_id]
    await update.message.reply_text("🚫 Cancelled.")
    return ConversationHandler.END

def register_handlers(application: Application):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", start_login)],
        states={
            PHONE: [MessageHandler(filters.TEXT, receive_phone)],
            OTP: [MessageHandler(filters.TEXT, receive_otp)],
            PASSWORD: [MessageHandler(filters.TEXT, receive_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    
