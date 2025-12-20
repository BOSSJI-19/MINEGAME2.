from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import OWNER_ID
from database import (
    users_col, groups_col, codes_col, update_balance, 
    add_api_key, remove_api_key, get_all_keys,
    add_game_key, remove_game_key, get_game_keys,
    add_sticker_pack, remove_sticker_pack, get_sticker_packs,
    wipe_database, set_economy_status, get_economy_status,
    set_logger_group, delete_logger_group,
    add_voice_key, remove_voice_key, get_all_voice_keys, # Voice Key Imports
    set_custom_voice, get_custom_voice # Custom TTS Imports
)

ADMIN_INPUT_STATE = {} 

# --- 1. MAIN ADMIN PANEL ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(OWNER_ID): return

    if update.effective_user.id in ADMIN_INPUT_STATE:
        del ADMIN_INPUT_STATE[update.effective_user.id]
    
    eco_status = "🟢 ON" if get_economy_status() else "🔴 OFF"
    voice_id = get_custom_voice()
    voice_keys = len(get_all_voice_keys())

    text = (
        f"👮‍♂️ **ADMIN CONTROL PANEL**\n\n"
        f"⚙️ **Economy:** {eco_status}\n"
        f"🗣 **Custom Voice ID:** `{voice_id}`\n"
        f"🔑 **Voice Keys:** `{voice_keys}`\n"
        f"👇 Select an action:"
    )

    kb = [
        [InlineKeyboardButton(f"Economy: {eco_status}", callback_data="admin_toggle_eco")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_cast_ask"), InlineKeyboardButton("🎁 Code", callback_data="admin_code_ask")],
        
        # Keys Management
        [InlineKeyboardButton("🔑 Chat Keys", callback_data="admin_chat_keys"), InlineKeyboardButton("🔑 Game Keys", callback_data="admin_game_keys")],
        
        # 🔥 VOICE & TTS SECTION 🔥
        [InlineKeyboardButton("🗣 Voice Keys", callback_data="admin_voice_keys"), InlineKeyboardButton("🎙 Custom TTS", callback_data="admin_tts_set")],
        
        # Stickers & Logger
        [InlineKeyboardButton("👻 Stickers", callback_data="admin_stickers"), InlineKeyboardButton("📝 Logger", callback_data="admin_logger")],
        
        [InlineKeyboardButton("☢️ WIPE DATA", callback_data="admin_wipe_ask"), InlineKeyboardButton("❌ Close", callback_data="admin_close")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)

# --- 2. CALLBACK HANDLER ---
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    user_id = q.from_user.id
    
    if str(user_id) != str(OWNER_ID):
        await q.answer("❌ Owner Only!", show_alert=True)
        return

    # --- VOICE KEY SUB-MENU ---
    if data == "admin_voice_keys":
        kb = [
            [InlineKeyboardButton("➕ Add Voice Key", callback_data="admin_vkey_add")],
            [InlineKeyboardButton("➖ Del Voice Key", callback_data="admin_vkey_del")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
        ]
        await q.edit_message_text("🎙 **ElevenLabs Voice Keys**\n\nManage your API keys for Mimi's voice note.", reply_markup=InlineKeyboardMarkup(kb))
        return

    # --- CUSTOM TTS SET ---
    if data == "admin_tts_set":
        ADMIN_INPUT_STATE[user_id] = 'set_tts_id'
        kb = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]]
        await q.edit_message_text("🎙 **Set Custom Voice ID**\n\nElevenLabs se Voice ID paste karo (e.g. `Rachel`).\n\n👉 Current: `{}`".format(get_custom_voice()), reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
        return

    # Logical Triggers
    if data == "admin_vkey_add":
        ADMIN_INPUT_STATE[user_id] = 'add_voice_key'
        await q.edit_message_text("➕ Send ElevenLabs API Key:")
        return

    if data == "admin_vkey_del":
        ADMIN_INPUT_STATE[user_id] = 'del_voice_key'
        keys = "\n".join([f"`{k}`" for k in get_all_voice_keys()])
        await q.edit_message_text(f"➖ Send Key to delete:\n\n{keys}", parse_mode=ParseMode.MARKDOWN)
        return

    # ... (Baki purane callback logic chat_keys, game_keys, logger, broadcast same rahenge)
    
    if data == "admin_toggle_eco":
        set_economy_status(not get_economy_status())
        await admin_panel(update, context)
    elif data == "admin_back":
        await admin_panel(update, context)
    elif data == "admin_close":
        await q.message.delete()

# --- 3. INPUT HANDLER ---
async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(OWNER_ID): return False

    state = ADMIN_INPUT_STATE.get(user_id)
    if not state: return False

    text = update.message.text.strip() if update.message.text else None

    # 🔥 CUSTOM TTS ID INPUT 🔥
    if state == 'set_tts_id' and text:
        set_custom_voice(text)
        await update.message.reply_text(f"✅ **Custom Voice Set:** `{text}`")
        del ADMIN_INPUT_STATE[user_id]
        return True

    # 🔥 VOICE KEY INPUT 🔥
    if state == 'add_voice_key' and text:
        if add_voice_key(text): await update.message.reply_text("✅ Voice Key Added!")
        else: await update.message.reply_text("⚠️ Key Exists!")
        del ADMIN_INPUT_STATE[user_id]
        return True

    if state == 'del_voice_key' and text:
        if remove_voice_key(text): await update.message.reply_text("🗑 Voice Key Deleted!")
        else: await update.message.reply_text("❌ Not Found.")
        del ADMIN_INPUT_STATE[user_id]
        return True

    # ... (Purana money, chat keys, codes input logic wahi rahega)
    return False
