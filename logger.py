import time
import sys
import os
import psutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import OWNER_ID
from database import get_total_users, get_total_groups

# --- RESTART COMMAND ---
async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if str(user.id) != str(OWNER_ID): 
        return

    msg = await update.message.reply_text("🔄 **Restarting System...**")
    await time.sleep(2)
    await msg.edit_text("✅ **System Rebooted!**\nBack online in 5 seconds.")
    
    os.execl(sys.executable, sys.executable, *sys.argv)

# --- PING COMMAND (FIXED) ---
async def ping_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    # Loading Emoji
    msg = await update.message.reply_text("⚡")
    end_time = time.time()
    
    ping_ms = round((end_time - start_time) * 1000)
    
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
    except:
        cpu = 0; ram = 0; disk = 0
    
    modules_list = [
        "Admin", "Bank", "Economy", "Games",
        "Market", "Ranking", "Anti-Spam", 
        "WordSeek", "Logger", "AI Chat", "Group Tools"
    ]
    modules_str = " | ".join(modules_list)
    
    # Direct Image Link (Make sure ye link sahi ho)
    PING_IMG = "https://i.ibb.co/QGGKVnw/image.png" 
    
    caption = f"""╭───〔 🤖 **sʏsᴛᴇᴍ sᴛᴀᴛᴜs** 〕───
┆
┆ ⚡ **ᴘɪɴɢ:** `{ping_ms}ms`
┆ 💻 **ᴄᴘᴜ:** `{cpu}%`
┆ 💾 **ʀᴀᴍ:** `{ram}%`
┆ 💿 **ᴅɪsᴋ:** `{disk}%`
┆
╰──────────────────────
📚 **ʟᴏᴀᴅᴇᴅ ᴍᴏᴅᴜʟᴇs:**
`{modules_str}`"""

    kb = [[InlineKeyboardButton("❌ Close", callback_data="close_ping")]]

    # 🔥 FIX: Pehle loading msg delete karo
    try:
        await msg.delete()
    except: pass
    
    # 🔥 FIX: 'reply_photo' ki jagah 'send_photo' use kiya
    # Taki agar command delete bhi ho jaye to error na aaye
    try:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=PING_IMG,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        # Fallback: Agar photo fail ho jaye to text bhejo
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ **Image Error:** `{e}`\n\n{caption}",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode=ParseMode.MARKDOWN
        )

# --- STATS COMMAND ---
async def stats_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if str(user.id) != str(OWNER_ID): 
        return

    try:
        users = get_total_users()
        groups = get_total_groups()
    except:
        users = 0
        groups = 0

    text = f"""📊 **CURRENT DATABASE STATS**
    
👤 **Total Users:** `{users}`
👥 **Total Groups:** `{groups}`
    
⚡ **Server Status:** Running Smoothly
    """
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
