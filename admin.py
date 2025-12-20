from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import OWNER_ID
from database import (
    users_col, groups_col, codes_col, update_balance, 
    add_api_key, remove_api_key, get_all_keys,
    add_game_key, remove_game_key, get_game_keys,
    add_sticker_pack, remove_sticker_pack, get_sticker_packs, # 🔥 New Imports
    wipe_database, set_economy_status, get_economy_status
)

# --- 1. MAIN ADMIN PANEL ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return

    context.user_data['admin_state'] = None
    
    eco_status = "🟢 ON" if get_economy_status() else "🔴 OFF"
    chat_keys = len(get_all_keys())
    game_keys = len(get_game_keys())
    stickers = len(get_sticker_packs()) # Count Packs

    text = (
        f"👮‍♂️ **ADMIN CONTROL PANEL**\n\n"
        f"⚙️ **Economy:** {eco_status}\n"
        f"💬 **Chat Keys:** `{chat_keys}`\n"
        f"🎮 **Game Keys:** `{game_keys}`\n"
        f"👻 **Sticker Packs:** `{stickers}`\n\n"
        f"👇 Select an action:"
    )

    kb = [
        [InlineKeyboardButton(f"Economy: {eco_status}", callback_data="admin_toggle_eco")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_cast_ask"), InlineKeyboardButton("🎁 Create Code", callback_data="admin_code_ask")],
        [InlineKeyboardButton("💰 Add Money", callback_data="admin_add_ask"), InlineKeyboardButton("💸 Take Money", callback_data="admin_take_ask")],
        
        # Keys
        [InlineKeyboardButton("➕ Chat Key", callback_data="admin_key_add"), InlineKeyboardButton("➕ Game Key", callback_data="admin_game_key_add")],
        [InlineKeyboardButton("➖ Del Chat Key", callback_data="admin_key_del"), InlineKeyboardButton("➖ Del Game Key", callback_data="admin_game_key_del")],
        
        # 🔥 Sticker Packs Buttons
        [InlineKeyboardButton("➕ Add Sticker Pack", callback_data="admin_pack_add"), InlineKeyboardButton("➖ Del Sticker Pack", callback_data="admin_pack_del")],
        
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
    
    if user_id != OWNER_ID:
        await q.answer("❌ Sirf Owner ke liye hai!", show_alert=True)
        return

    # --- CLOSE ---
    if data == "admin_close":
        await q.message.delete()
        context.user_data['admin_state'] = None
        return

    # --- TOGGLE ECONOMY ---
    if data == "admin_toggle_eco":
        current = get_economy_status()
        set_economy_status(not current)
        await admin_panel(update, context)
        return

    # --- BROADCAST ASK ---
    if data == "admin_cast_ask":
        context.user_data['admin_state'] = 'broadcast'
        kb = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]]
        await q.edit_message_text(
            "📢 **Universal Broadcast Mode**\n\n"
            "Ab aap kuch bhi bhejo (Text, Sticker, Photo, Video).\n"
            "Main same to same sabko bhej dunga. 👇", 
            reply_markup=InlineKeyboardMarkup(kb), 
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # --- MONEY ASK ---
    if data == "admin_add_ask":
        context.user_data['admin_state'] = 'add_money'
        kb = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]]
        await q.edit_message_text("💰 **Add Money Mode**\n\nFormat: `User_ID Amount`\nExample: `123456789 5000`", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
        return

    if data == "admin_take_ask":
        context.user_data['admin_state'] = 'take_money'
        kb = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]]
        await q.edit_message_text("💸 **Take Money Mode**\n\nFormat: `User_ID Amount`\nExample: `123456789 5000`", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
        return

    # --- CHAT KEY ASK ---
    if data == "admin_key_add":
        context.user_data['admin_state'] = 'add_key'
        kb = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]]
        await q.edit_message_text("➕ **Add CHAT API Key (Mimi)**\n\nNayi Gemini API Key paste karo 👇", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
        return

    if data == "admin_key_del":
        context.user_data['admin_state'] = 'del_key'
        all_keys = "\n".join([f"`{k}`" for k in get_all_keys()])
        kb = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]]
        await q.edit_message_text(f"➖ **Delete CHAT Key**\n\nActive Keys:\n{all_keys}", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
        return

    # --- GAME KEY ASK ---
    if data == "admin_game_key_add":
        context.user_data['admin_state'] = 'add_game_key'
        kb = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]]
        await q.edit_message_text("➕ **Add GAME API Key (WordSeek)**\n\nGame wali Gemini API Key paste karo 👇", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
        return

    if data == "admin_game_key_del":
        context.user_data['admin_state'] = 'del_game_key'
        all_keys = "\n".join([f"`{k}`" for k in get_game_keys()])
        kb = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]]
        await q.edit_message_text(f"➖ **Delete GAME Key**\n\nActive Game Keys:\n{all_keys}", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
        return

    # --- 🔥 STICKER PACK LOGIC ---
    if data == "admin_pack_add":
        context.user_data['admin_state'] = 'add_pack'
        kb = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]]
        await q.edit_message_text(
            "➕ **Add Sticker Pack**\n\n"
            "Pack ka **Link** ya **Name** bhejo.\n"
            "Ex: `HotCherry` ya `https://t.me/addstickers/HotCherry`", 
            reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN
        )
        return

    if data == "admin_pack_del":
        context.user_data['admin_state'] = 'del_pack'
        all_packs = "\n".join([f"`{p}`" for p in get_sticker_packs()])
        kb = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]]
        await q.edit_message_text(f"➖ **Delete Pack**\n\nActive Packs:\n{all_packs}\n\nNaam bhejo delete karne ke liye.", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
        return

    # --- CODE ASK ---
    if data == "admin_code_ask":
        context.user_data['admin_state'] = 'create_code'
        kb = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]]
        await q.edit_message_text("🎁 **Create Promo Code**\n\nFormat: `Name Amount Limit`\nExample: `DIWALI25 1000 50`", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
        return

    # --- WIPE ASK ---
    if data == "admin_wipe_ask":
        kb = [
            [InlineKeyboardButton("⚠️ CONFIRM WIPE", callback_data="admin_wipe_confirm")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]
        ]
        await q.edit_message_text("☢️ **DANGER ZONE** ☢️\n\nDatabase RESET karna hai?", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
        return

    if data == "admin_wipe_confirm":
        wipe_database()
        await q.edit_message_text("💀 **Database Wiped Successfully!**")
        return

    # --- BACK ---
    if data == "admin_back":
        await admin_panel(update, context)
        return

# --- 3. INPUT HANDLER (TEXT & MEDIA) ---
async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID: return False

    state = context.user_data.get('admin_state')
    if not state: return False

    msg = update.message
    
    # 🔥 1. BROADCAST LOGIC (ANY MEDIA) 🔥
    if state == 'broadcast':
        users = list(users_col.find({}))
        groups = list(groups_col.find({}))
        
        count = 0
        status_msg = await msg.reply_text("📢 Sending Broadcast (Media supported)...")
        
        for u in users:
            try: 
                await context.bot.copy_message(chat_id=u["_id"], from_chat_id=msg.chat_id, message_id=msg.message_id)
                count+=1
            except: pass
            
        for g in groups:
            try: 
                await context.bot.copy_message(chat_id=g["_id"], from_chat_id=msg.chat_id, message_id=msg.message_id)
                count+=1
            except: pass
            
        await status_msg.edit_text(f"✅ **Broadcast Sent to {count} chats!**")
        context.user_data['admin_state'] = None
        return True

    # --- VALIDATION FOR OTHER COMMANDS ---
    if not msg.text:
        await msg.reply_text("❌ Is command ke liye sirf Text bhejo.")
        return True
        
    text = msg.text.strip()

    # --- 🔥 STICKER PACK ADD 🔥
    if state == 'add_pack':
        # Link se naam nikalna (https://t.me/addstickers/Name -> Name)
        pack_name = text.split('/')[-1].strip()
        
        try:
            # Check karo ki pack valid hai ya nahi Telegram par
            await context.bot.get_sticker_set(pack_name)
            
            if add_sticker_pack(pack_name):
                await msg.reply_text(f"✅ **Pack Added:** `{pack_name}`")
            else:
                await msg.reply_text("⚠️ Pack already exists.")
        except:
            await msg.reply_text("❌ **Invalid Pack!**\nTelegram par ye sticker pack exist nahi karta.\nSahi naam bhejo (e.g., `HotCherry`).")
        
        context.user_data['admin_state'] = None
        return True

    if state == 'del_pack':
        if remove_sticker_pack(text): await msg.reply_text("🗑 **Pack Deleted!**")
        else: await msg.reply_text("❌ Not Found.")
        context.user_data['admin_state'] = None
        return True

    # --- MONEY LOGIC ---
    if state in ['add_money', 'take_money']:
        try:
            parts = text.split()
            target_id = int(parts[0])
            amount = int(parts[1])
            if state == 'take_money': amount = -amount
            update_balance(target_id, amount)
            await msg.reply_text(f"✅ **Success!** Balance Updated.")
        except:
            await msg.reply_text("❌ Error! Format: `ID Amount`")
        context.user_data['admin_state'] = None
        return True

    # --- CHAT KEYS LOGIC ---
    if state == 'add_key':
        if add_api_key(text): await msg.reply_text("✅ Chat Key Added!")
        else: await msg.reply_text("⚠️ Key Exists!")
        context.user_data['admin_state'] = None
        return True

    if state == 'del_key':
        if remove_api_key(text): await msg.reply_text("🗑 Chat Key Deleted!")
        else: await msg.reply_text("❌ Key Not Found.")
        context.user_data['admin_state'] = None
        return True

    # --- GAME KEYS LOGIC ---
    if state == 'add_game_key':
        if add_game_key(text): await msg.reply_text("✅ **Game Key Added!** (For WordSeek)")
        else: await msg.reply_text("⚠️ Key Exists!")
        context.user_data['admin_state'] = None
        return True

    if state == 'del_game_key':
        if remove_game_key(text): await msg.reply_text("🗑 **Game Key Deleted!**")
        else: await msg.reply_text("❌ Key Not Found.")
        context.user_data['admin_state'] = None
        return True

    # --- CODE LOGIC ---
    if state == 'create_code':
        try:
            parts = text.split()
            name = parts[0]
            amt = int(parts[1])
            limit = int(parts[2])
            codes_col.insert_one({"code": name, "amount": amt, "limit": limit, "redeemed_by": []})
            await msg.reply_text(f"🎁 **Code Generated:** `{name}`")
        except:
            await msg.reply_text("❌ Format: `Name Amount Limit`")
        context.user_data['admin_state'] = None
        return True

    return False
