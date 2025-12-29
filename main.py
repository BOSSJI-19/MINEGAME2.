import random
import os
import asyncio # 🔥 Added for Async Tasks
import importlib 
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# IMPORTS
from config import TELEGRAM_TOKEN, BOT_NAME 
from database import (
    users_col, codes_col, update_balance, get_balance, 
    check_registered, register_user, update_group_activity, 
    update_username, update_chat_stats,
    is_user_muted, is_user_banned,
    get_logger_group
)
from ai_chat import get_yuki_response, get_mimi_sticker
from tts import generate_voice 

# 🔥 IMPORT USERBOT STARTER
try:
    from tools.userbot import start_userbots
except ImportError:
    print("⚠️ tools/userbot.py nahi mila! Userbot features kaam nahi karenge.")
    async def start_userbots(): pass # Dummy function taaki error na aaye

# MODULES (OLD ONES - Hardcoded)
# Make sure ye sab files wahi folder me ho, warna error aayega
try:
    import admin, start, help, group, leaderboard, pay, bet, wordseek, grouptools, chatstat, logger, events, info, tictactoe, couple
    import livetime, dmspam, bank, wordgrid
    from bank import check_balance 
    from antispam import check_spam
except ImportError as e:
    print(f"⚠️ Warning: Kuch modules missing hain: {e}")

# --- FLASK SERVER ---
app = Flask('')
@app.route('/')
def home(): return "I am Alive! 24/7"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run); t.start()

# VARS
SHOP_ITEMS = {
    "vip":   {"name": "👑 VIP", "price": 10000},
    "god":   {"name": "⚡ God", "price": 50000},
    "rich":  {"name": "💸 Rich", "price": 100000}
}

# --- 🔌 AUTO LOADER FUNCTION ---
def load_plugins(application: Application):
    plugin_dir = "tools"
    if not os.path.exists(plugin_dir):
        try: os.makedirs(plugin_dir); print(f"📁 Created '{plugin_dir}' directory.")
        except: pass
        return

    path_list = [f for f in os.listdir(plugin_dir) if f.endswith(".py") and f != "__init__.py"]
    print(f"🔌 Loading {len(path_list)} plugins from '{plugin_dir}'...")

    for file in path_list:
        module_name = file[:-3]
        try:
            module = importlib.import_module(f"{plugin_dir}.{module_name}")
            if hasattr(module, "register_handlers"):
                module.register_handlers(application)
                print(f"  ✅ Loaded: {module_name}")
            else:
                print(f"  ⚠️ Skipped: {module_name} (No 'register_handlers')")
        except Exception as e:
            print(f"  ❌ Failed to load {module_name}: {e}")

# --- STARTUP MESSAGE & USERBOT LAUNCHER ---
async def on_startup(application: Application):
    print(f"🚀 {BOT_NAME} IS STARTING...")
    
    # 1. Logger Message
    logger_id = get_logger_group()
    if logger_id:
        try:
            me = await application.bot.get_me()
            txt = f"<b>{BOT_NAME} Started Successfully! 🟢</b>\n🆔 ID: <code>{me.id}</code>"
            await application.bot.send_message(chat_id=logger_id, text=txt, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"⚠️ Logger Error: {e}")

    # 2. 🔥 START USERBOTS (Background Task)
    # Ye line tumhare saved sessions ko load karke start karegi
    print("🔄 Initializing Userbots...")
    asyncio.create_task(start_userbots())

# --- SHOP & REDEEM HANDLERS ---
async def shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg_func = update.callback_query.message.edit_text if update.callback_query else update.message.reply_text
    
    kb = []
    for k, v in SHOP_ITEMS.items():
        kb.append([InlineKeyboardButton(f"{v['name']} - ₹{v['price']}", callback_data=f"buy_{k}_{uid}")])
    kb.append([InlineKeyboardButton("❌ Close", callback_data=f"close_help")])
    
    await msg_func("🛒 **VIP SHOP**", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)

async def redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args: return await update.message.reply_text("⚠️ Usage: `/redeem CODE`")
    
    code = context.args[0]
    data = codes_col.find_one({"code": code})
    if not data: return await update.message.reply_text("❌ Invalid Code!")
    if user.id in data["redeemed_by"]: return await update.message.reply_text("⚠️ Already Redeemed!")
    
    update_balance(user.id, data["amount"])
    codes_col.update_one({"code": code}, {"$push": {"redeemed_by": user.id}})
    await update.message.reply_text(f"🎉 Redeemed ₹{data['amount']}!")

# --- CALLBACK HANDLER ---
async def callback_handler(update, context):
    q = update.callback_query
    data = q.data
    uid = q.from_user.id
    
    if data in ["close_log", "close_ping", "close_help"]:
        try: await q.message.delete()
        except: pass
        return

    # Routing logic for modules
    if data == "open_shop": await q.answer(); await shop_menu(update, context); return
    if data == "open_games":
        await q.answer()
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="back_home")]]
        msg = "🎮 **GAME MENU**\n/bet, /new, /wordgrid, /zero, /invest"
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN); return

    if data == "open_ranking": await q.answer(); await leaderboard.user_leaderboard(update, context); return
    if data == "open_commands": await q.answer(); await help.help_callback(update, context); return
    if data == "back_home": await q.answer(); await start.start_callback(update, context); return
    
    # Pattern matching for modules
    if data.startswith(("help_", "mod_")): await help.help_callback(update, context); return
    if data.startswith(("start_", "st_")): await start.start_callback(update, context); return
    if data.startswith("admin_"): await admin.admin_callback(update, context); return
    if data.startswith(("wrank_", "new_wordseek_", "close_wrank", "end_wordseek")): await wordseek.wordseek_callback(update, context); return
    if data.startswith(("rank_", "hide_rank")): await chatstat.rank_callback(update, context); return
    if data.startswith(("set_", "clk_", "cash_", "close_", "noop_", "rebet_")): await bet.bet_callback(update, context); return
    if data.startswith("ttt_"): await tictactoe.ttt_callback(update, context); return
    
    if data.startswith("buy_"):
        parts = data.split("_")
        if uid != int(parts[2]): return await q.answer("Not for you!", show_alert=True)
        item = SHOP_ITEMS.get(parts[1])
        if get_balance(uid) < item["price"]: return await q.answer("No Money!", show_alert=True)
        update_balance(uid, -item["price"])
        users_col.update_one({"_id": uid}, {"$push": {"titles": item["name"]}})
        await q.answer(f"Bought {item['name']}!"); return

    if data.startswith("revive_"): await pay.revive_callback(update, context); return
    if data == "giveup_wordgrid": await wordgrid.give_up(update, context); return
    if data.startswith("grid_"): await wordgrid.grid_callback(update, context); return
    if data == "close_time": await livetime.close_time(update, context); return

# --- MAIN MESSAGE HANDLER ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user = update.effective_user
    chat = update.effective_chat
    
    # 0. Protection & Enforcement
    if chat.type == "private":
        spam_status = dmspam.check_spam(user.id)
        if spam_status in ["BLOCKED", "NEW_BLOCK"]: return
    
    if chat.type in ["group", "supergroup"] and not user.is_bot:
        if is_user_banned(chat.id, user.id) or is_user_muted(chat.id, user.id):
            try: await update.message.delete(); return
            except: pass

    if not user.is_bot and check_spam(user.id) == "BLOCKED":
        await update.message.reply_text("🚫 Spam Detected! Blocked."); return

    # 1. Stats
    update_username(user.id, user.first_name)
    if chat.type != "private":
        update_chat_stats(chat.id, user.id, user.first_name)
        update_group_activity(chat.id, chat.title)

    # 2. Game Logic
    if await admin.handle_admin_input(update, context): return
    await wordseek.handle_word_guess(update, context)
    await wordgrid.handle_word_guess(update, context)

    # 3. Sticker Logic
    if update.message.sticker:
        if chat.type == "private" or (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id) or random.random() < 0.2:
            sticker_id = await get_mimi_sticker(context.bot)
            if sticker_id: await update.message.reply_sticker(sticker_id)
        return

    # 4. 🔥 AI TEXT & VOICE LOGIC (Optimized)
    text = update.message.text
    if not text: return

    should_reply = False
    if chat.type == "private": should_reply = True
    elif any(trigger in text.lower() for trigger in ["aniya", context.bot.username.lower()]): should_reply = True
    elif update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id: should_reply = True

    if should_reply:
        voice_triggers = ["voice", "note", "moh", "audio", "gn", "gm", "rec","kaho"]
        wants_voice = any(v in text.lower() for v in voice_triggers)

        await context.bot.send_chat_action(chat_id=chat.id, action="typing")
        
        # 🔥 FIX: Run Blocking AI in Executor (Background Thread)
        # Isse bot lag nahi karega jab tak AI soch raha hai
        loop = asyncio.get_running_loop()
        try:
            ai_reply = await loop.run_in_executor(None, get_yuki_response, user.id, text, user.first_name)
        except Exception as e:
            ai_reply = "Dimag kharab ho gaya hai mera! (Error)"
            print(f"AI Error: {e}")

        if wants_voice:
            await context.bot.send_chat_action(chat_id=chat.id, action="record_voice")
            audio_path = await generate_voice(ai_reply)
            
            if audio_path:
                try:
                    with open(audio_path, 'rb') as voice_file:
                        await update.message.reply_voice(voice=voice_file)
                    os.remove(audio_path)
                except:
                    await update.message.reply_text(ai_reply)
            else:
                await update.message.reply_text(ai_reply)
        else:
            await update.message.reply_text(ai_reply)

# --- MAIN ENGINE ---
def main():
    keep_alive()
    
    app = Application.builder().token(TELEGRAM_TOKEN).post_init(on_startup).build()
    
    # Handlers Registration
    app.add_handler(CommandHandler("start", start.start))
    app.add_handler(CommandHandler("help", help.help_command))
    app.add_handler(CommandHandler("admin", admin.admin_panel))
    
    app.add_handler(CommandHandler("info", info.user_info))
    app.add_handler(CommandHandler("love", info.love_calculator))
    app.add_handler(CommandHandler("stupid", info.stupid_meter))
    app.add_handler(CommandHandler("couple", couple.couple_check))
    
    app.add_handler(CommandHandler("bal", check_balance))
    app.add_handler(CommandHandler("redeem", redeem_code))
    app.add_handler(CommandHandler("shop", shop_menu))
    
    app.add_handler(CommandHandler("top", leaderboard.user_leaderboard))
    app.add_handler(CommandHandler("ranking", group.ranking))
    app.add_handler(CommandHandler("stats", logger.stats_bot))
    app.add_handler(CommandHandler("ping", logger.ping_bot))
    
    app.add_handler(CommandHandler("bet", bet.bet_menu))
    app.add_handler(CommandHandler("new", wordseek.start_wordseek))
    app.add_handler(CommandHandler("wordgrid", wordgrid.start_wordgrid))
    app.add_handler(CommandHandler("zero", tictactoe.start_ttt))
    app.add_handler(CommandHandler("market", group.market_info))
    app.add_handler(CommandHandler("invest", group.invest))
    app.add_handler(CommandHandler("sell", group.sell_shares))
    app.add_handler(CommandHandler("topinvest", group.top_investors))
    
    app.add_handler(CommandHandler("bank", bank.bank_info))
    app.add_handler(CommandHandler("deposit", bank.deposit))
    app.add_handler(CommandHandler("withdraw", bank.withdraw))
    app.add_handler(CommandHandler("loan", bank.take_loan))
    app.add_handler(CommandHandler("payloan", bank.repay_loan))
    
    app.add_handler(CommandHandler("pay", pay.pay_user))
    app.add_handler(CommandHandler("rob", pay.rob_user))
    app.add_handler(CommandHandler("kill", pay.kill_user))
    app.add_handler(CommandHandler("protect", pay.protect_user))
    app.add_handler(CommandHandler("alive", pay.check_status))
    
    app.add_handler(CommandHandler("time", livetime.start_live_time))
    app.add_handler(MessageHandler(filters.Regex(r'^[\./]time'), livetime.start_live_time))

    app.add_handler(CallbackQueryHandler(callback_handler))
    
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, events.welcome_user))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, events.track_leave))
    app.add_handler(MessageHandler(filters.StatusUpdate.VIDEO_CHAT_STARTED, events.vc_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.VIDEO_CHAT_ENDED, events.vc_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.VIDEO_CHAT_PARTICIPANTS_INVITED, events.vc_handler))
    
    app.add_handler(MessageHandler(filters.Regex(r'(?i)^[\./]crank'), chatstat.show_leaderboard))
    
    # Simple Group Tools
    app.add_handler(MessageHandler(filters.Regex(r'^[\./]id$'), grouptools.get_id))
    app.add_handler(MessageHandler(filters.Regex(r'^[\./]warn$'), grouptools.warn_user))
    app.add_handler(MessageHandler(filters.Regex(r'^[\./]mute$'), grouptools.mute_user))
    app.add_handler(MessageHandler(filters.Regex(r'^[\./]unmute$'), grouptools.unmute_user))
    app.add_handler(MessageHandler(filters.Regex(r'^[\./]ban$'), grouptools.ban_user))
    app.add_handler(MessageHandler(filters.Regex(r'^[\./]unban$'), grouptools.unban_user))
    app.add_handler(MessageHandler(filters.Regex(r'^[\./]kick$'), grouptools.kick_user))
    app.add_handler(MessageHandler(filters.Regex(r'^[\./]pin$'), grouptools.pin_message))
    
    # Auto-Load New Tools (string.py, user_ai.py, etc.)
    load_plugins(app)

    # Main Message Handler (Last)
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))
    
    print(f"🚀 {BOT_NAME} STARTED SUCCESSFULLY!")
    app.run_polling()

if __name__ == "__main__":
    main()
        
