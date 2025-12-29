import asyncio
import os
import importlib
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
from pymongo import MongoClient
from config import MONGO_URL

# --- DATABASE CONNECTION ---
client = MongoClient(MONGO_URL)
db = client["yuki_database"]
clones_col = db["cloned_bots"]

# --- GLOBAL LIST ---
running_clones = []

# --- ✨ AESTHETIC FONT HELPER ---
def to_fancy(text):
    """Converts normal text to Small Caps (Aesthetic Font)"""
    mapping = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ',
        'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ',
        'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ꜰ', 'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ',
        'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 'ꜱ', 'T': 'ᴛ',
        'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ'
    }
    return "".join(mapping.get(c, c) for c in text)

# --- CLONE LOADER ---
def load_plugins_for_clone(application: Application):
    plugin_dir = "tools"
    if not os.path.exists(plugin_dir): return
    path_list = [f for f in os.listdir(plugin_dir) if f.endswith(".py") and f != "__init__.py"]
    for file in path_list:
        module_name = file[:-3]
        try:
            module = importlib.import_module(f"{plugin_dir}.{module_name}")
            if hasattr(module, "register_handlers"):
                module.register_handlers(application)
        except: pass

async def start_one_clone(token):
    try:
        clone_app = Application.builder().token(token).build()
        load_plugins_for_clone(clone_app)
        await clone_app.initialize()
        await clone_app.start()
        await clone_app.updater.start_polling(drop_pending_updates=True)
        running_clones.append(clone_app)
        me = await clone_app.bot.get_me()
        return me.username
    except: return None

# --- COMMANDS ---

async def clone_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    # 1. Validation (Empty)
    if not args:
        txt = to_fancy("Usage")
        await update.message.reply_text(f"> ⚠️ **{txt}:** `/clone [BOT_TOKEN]`", parse_mode=ParseMode.MARKDOWN)
        return

    bot_token = args[0]
    
    # 2. Duplicate Check
    if clones_col.find_one({"token": bot_token}):
        txt = to_fancy("This bot is already active in our database")
        await update.message.reply_text(f"> ⚠️ **{txt}.**", parse_mode=ParseMode.MARKDOWN)
        return

    # 3. Processing
    txt_proc = to_fancy("Processing request")
    msg = await update.message.reply_text(f"> 🔄 **{txt_proc}...**", parse_mode=ParseMode.MARKDOWN)

    # 4. Start Bot
    username = await start_one_clone(bot_token)
    
    if username:
        # Save to DB
        clones_col.insert_one({
            "token": bot_token,
            "owner_id": user_id,
            "username": username
        })
        
        t_success = to_fancy("Clone Successful")
        t_user = to_fancy("Username")
        t_status = to_fancy("Status")
        t_active = to_fancy("Active")
        
        await msg.edit_text(
            f"> 🎉 **{t_success}!**\n"
            f"> 🤖 **{t_user}:** @{username}\n"
            f"> ✅ **{t_status}:** {t_active}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        t_err = to_fancy("Invalid Token or Bot is Banned")
        await msg.edit_text(f"> ❌ **{t_err}.**", parse_mode=ParseMode.MARKDOWN)

async def remove_clone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    if not args:
        txt = to_fancy("Usage")
        await update.message.reply_text(f"> ⚠️ **{txt}:** `/remove @BotUsername`", parse_mode=ParseMode.MARKDOWN)
        return

    target_username = args[0].replace("@", "")
    
    # 1. Check DB
    clone_data = clones_col.find_one({"username": target_username})
    
    if not clone_data:
        txt = to_fancy("Bot not found in database")
        await update.message.reply_text(f"> ❌ **{txt}.**", parse_mode=ParseMode.MARKDOWN)
        return
        
    # 2. Security Check (Ownership)
    if clone_data["owner_id"] != user_id:
        txt_denied = to_fancy("Access Denied")
        txt_reason = to_fancy("You are not the owner of this bot")
        await update.message.reply_text(f"> 🚫 **{txt_denied}!**\n> {txt_reason}.", parse_mode=ParseMode.MARKDOWN)
        return

    txt_stop = to_fancy("Stopping bot instance")
    msg = await update.message.reply_text(f"> 🗑️ **{txt_stop}...**", parse_mode=ParseMode.MARKDOWN)

    # 3. Stop Process
    for app in running_clones:
        try:
            bot_me = await app.bot.get_me()
            if bot_me.username == target_username:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
                running_clones.remove(app)
                break
        except: pass

    # 4. Delete from DB
    clones_col.delete_one({"username": target_username})
    
    t_removed = to_fancy("Successfully Removed")
    await msg.edit_text(f"> ✅ **{t_removed}:** @{target_username}", parse_mode=ParseMode.MARKDOWN)

async def restart_all_clones():
    print("🚀 Restarting Clones...")
    clones = clones_col.find({})
    for doc in clones:
        await start_one_clone(doc["token"])
        await asyncio.sleep(1)

def register_handlers(application: Application):
    application.add_handler(CommandHandler("clone", clone_bot))
    application.add_handler(CommandHandler("remove", remove_clone))
