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
from database import db  # Ensure db is your MongoDB database object

# --- MONGODB COLLECTION ---
sessions_col = db["userbot_sessions"] 

# --- STATES ---
PHONE, OTP, PASSWORD = range(3)

# --- TEMP STORAGE (Login karte waqt data hold karne ke liye) ---
temp_clients = {}
temp_data = {}

async def start_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        "🟢 **Userbot Login Started**\n\n"
        "Apna **Phone Number** bhejo Country Code ke sath.\n"
        "Example: `+919876543210`"
    )
    return PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    phone_number = update.message.text.strip()
    
    msg = await update.message.reply_text(f"🔄 Connecting to Telegram servers... `{phone_number}`")

    # Pyrogram Client Create karo (Memory mein)
    client = Client(f"session_{user_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
    await client.connect()
    
    temp_clients[user_id] = client
    temp_data[user_id] = {"phone": phone_number}

    try:
        sent_code = await client.send_code(phone_number)
        temp_data[user_id]["hash"] = sent_code.phone_code_hash
        await msg.edit_text(
            "✅ **OTP Sent!**\n\n"
            "Please OTP enter karein format mein (space ke sath):\n"
            "Example: `1 2 3 4 5`"
        )
        return OTP
    except PhoneNumberInvalid:
        await msg.edit_text("❌ **Invalid Number!** /add dabakar dobara try karein.")
        await client.disconnect()
        return ConversationHandler.END
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

    msg = await update.message.reply_text("🔄 Verifying OTP...")

    try:
        await client.sign_in(phone, code_hash, otp)
    except SessionPasswordNeeded:
        await msg.edit_text("🔐 **2-Step Verification Detected!**\nApna Password bhejein:")
        return PASSWORD
    except (PhoneCodeInvalid, PasswordHashInvalid):
        await msg.edit_text("❌ **Wrong OTP!** Process Cancelled.")
        await client.disconnect()
        return ConversationHandler.END
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")
        await client.disconnect()
        return ConversationHandler.END

    # Agar password nahi hai toh direct success
    return await login_success(update, client, user_id, msg)

async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    password = update.message.text
    client = temp_clients.get(user_id)
    msg = await update.message.reply_text("🔄 Verifying Password...")

    try:
        await client.check_password(password)
    except Exception as e:
        await msg.edit_text(f"❌ **Wrong Password!** \nError: {e}")
        await client.disconnect()
        return ConversationHandler.END
    
    return await login_success(update, client, user_id, msg)

async def login_success(update, client, user_id, msg):
    # Session String Generate
    session_string = await client.export_session_string()
    me = await client.get_me()
    await client.disconnect()

    # MongoDB Save
    user_data = {
        "user_id": user_id,
        "first_name": me.first_name,
        "username": me.username,
        "session_string": session_string,
        "is_active": True
    }
    
    # Update if exists, else insert
    sessions_col.update_one({"user_id": user_id}, {"$set": user_data}, upsert=True)
    
    # Clean up temp memory
    if user_id in temp_clients: del temp_clients[user_id]
    if user_id in temp_data: del temp_data[user_id]

    await msg.edit_text(
        f"🎉 **Login Successful!**\n\n"
        f"Connected as: {me.first_name}\n"
        f"Session Saved to MongoDB via `string.py`.\n"
        f"ℹ️ _Bot restart hone par tumhara AI activate ho jayega._"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in temp_clients:
        await temp_clients[user_id].disconnect()
        del temp_clients[user_id]
    await update.message.reply_text("🚫 Process Cancelled.")
    return ConversationHandler.END

# --- HANDLER REGISTRATION ---
def register_handlers(application: Application):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", start_login)],
        states={
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
            OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_otp)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
  
