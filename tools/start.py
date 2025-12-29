from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- ✨ AESTHETIC FONT HELPER ---
def to_fancy(text):
    """Normal text ko Fancy Font mein convert karta hai"""
    mapping = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ',
        'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ',
        'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ꜰ', 'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ',
        'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 'ꜱ', 'T': 'ᴛ',
        'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        ' ': ' '
    }
    return "".join(mapping.get(c, c) for c in text)

# --- 1. CLOSE BUTTON HANDLER ---
# Ye function sirf "Close" button ko handle karega (main.py ki jarurat nahi)
async def close_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        await query.message.delete()
    except:
        pass

# --- 2. START COMMAND LOGIC ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check karein ki ye Message hai ya Callback (Button click)
    if update.callback_query:
        message = update.callback_query.message
        user = update.callback_query.from_user
        chat = message.chat
        is_callback = True
    else:
        message = update.message
        user = update.effective_user
        chat = update.effective_chat
        is_callback = False

    bot_username = context.bot.username

    # --- 🔥 GROUP LOGIC (GC) ---
    if chat.type != "private":
        # Fancy Text
        txt_msg = to_fancy("Hello dear I am alive")
        txt_instruct = to_fancy("Please start me in DM to use my features")
        
        final_text = (
            f"👋 **{txt_msg}!**\n\n"
            f"⚠️ **{txt_instruct}.**"
        )
        
        # Fancy Buttons
        btn_dm = to_fancy("DM Me")
        btn_support = to_fancy("Support")
        btn_close = to_fancy("Close")
        
        # Support Link
        support_link = "https://t.me/Aniya_Support" 

        keyboard = [
            [
                InlineKeyboardButton(f"↗️ {btn_dm}", url=f"https://t.me/{bot_username}?start=start"),
                InlineKeyboardButton(f"🆘 {btn_support}", url=support_link)
            ],
            [
                # Note: callback_data="close_me" ab yahi file handle karegi
                InlineKeyboardButton(f"❌ {btn_close}", callback_data="close_me")
            ]
        ]
        
        if is_callback:
            await message.edit_text(final_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await message.reply_text(final_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    # --- 👤 PRIVATE LOGIC (DM) ---
    first_name = user.first_name
    txt_welcome = to_fancy("Welcome to Aniya AI Bot")
    txt_desc = to_fancy("I am an advanced AI bot with Userbot capabilities")
    
    text = (
        f"✨ **{txt_welcome}, {first_name}!**\n\n"
        f"🤖 **{txt_desc}.**\n"
        "Click below to explore commands."
    )
    
    # Buttons for Private Chat
    btn_cmds = to_fancy("Commands")
    btn_add = to_fancy("Add Me to GC")
    
    keyboard = [
        [InlineKeyboardButton(f"📜 {btn_cmds}", callback_data="open_commands")],
        [InlineKeyboardButton(f"➕ {btn_add}", url=f"https://t.me/{bot_username}?startgroup=true")]
    ]
    
    if is_callback:
        await message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- 3. AUTO LOADER HOOK ---
# Ye function main.py automatically call karega
def register_handlers(application: Application):
    # /start command handler
    application.add_handler(CommandHandler("start", start_command))
    
    # "Back Home" button handler (agar help menu se wapas aana ho)
    application.add_handler(CallbackQueryHandler(start_command, pattern="back_home"))
    
    # 🔥 Close Button Handler (Yahi par register kar diya)
    # Isse main.py mein kuch likhne ki zarurat nahi padegi
    application.add_handler(CallbackQueryHandler(close_message, pattern="close_me"))
      
