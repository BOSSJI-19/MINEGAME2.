from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import OWNER_ID

# --- MAIN HELP COMMAND ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 **HELP MENU**\n\n"
        "Select a category below to see available commands:"
    )
    
    kb = [
        [InlineKeyboardButton("🏦 Bank & Economy", callback_data="help_bank"), InlineKeyboardButton("🎮 Games & Activity", callback_data="help_game")],
        [InlineKeyboardButton("🔫 Crime & RPG", callback_data="help_crime"), InlineKeyboardButton("📈 Market & Stats", callback_data="help_market")],
        [InlineKeyboardButton("🛒 Shop & Extras", callback_data="help_shop"), InlineKeyboardButton("🛠 Group Tools", callback_data="help_tools")],
        [InlineKeyboardButton("👮 Admin Only", callback_data="help_admin")],
        [InlineKeyboardButton("❌ Close", callback_data="close_help")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)

# --- CALLBACK HANDLER FOR HELP BUTTONS ---
async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    
    if data == "close_help":
        await q.message.delete()
        return

    # 1. BANKING
    if data == "help_bank":
        text = (
            "🏦 **BANKING & ECONOMY**\n\n"
            "• `/bal` - Check Wallet Balance\n"
            "• `/bank` - Check Bank Account\n"
            "• `/deposit <amount>` - Save Money in Bank\n"
            "• `/withdraw <amount>` - Withdraw Cash\n"
            "• `/loan <amount>` - Take Loan from Bank\n"
            "• `/payloan <amount>` - Repay Bank Loan"
        )
    
    # 2. GAMES
    elif data == "help_game":
        text = (
            "🎮 **GAMES & ACTIVITY**\n\n"
            "• `/bet <amount>` - Play Mines (Risk vs Reward)\n"
            "• `/new` - Start WordSeek Game\n"
            "• `/wrank` - WordSeek Leaderboard\n"
            "• `/crank` - Chat Message Ranking"
        )

    # 3. CRIME
    elif data == "help_crime":
        text = (
            "🔫 **CRIME & RPG**\n\n"
            "• `/rob` - Rob a user (Reply to msg)\n"
            "• `/kill` - Kill a user (Reply to msg)\n"
            "• `/pay <amount>` - Give Money (Reply)\n"
            "• `/protect` - Buy Shield (24 Hours)\n"
            "• `/alive` - Check Dead/Alive Status"
        )

    # 4. MARKET
    elif data == "help_market":
        text = (
            "📈 **MARKET & STATS**\n\n"
            "• `/market` - Check Group Share Prices\n"
            "• `/invest <group_id> <amount>` - Buy Shares\n"
            "• `/sell <group_id>` - Sell Shares\n"
            "• `/ranking` - Top Groups by Activity\n"
            "• `/top` - Global Rich List"
        )

    # 5. SHOP
    elif data == "help_shop":
        text = (
            "🛒 **SHOP & EXTRAS**\n\n"
            "• `/shop` - Buy VIP Titles\n"
            "• `/redeem <code>` - Claim Promo Code\n"
            "• `/id` - Get User/Group ID\n"
            "• `/ping` - Check Bot Speed\n"
            "• `/stats` - Check Bot Users"
        )

    # 6. TOOLS
    elif data == "help_tools":
        text = (
            "🛠 **GROUP ADMIN TOOLS**\n"
            "_(Use . or /)_\n\n"
            "• `.warn` / `.unwarn` - Manage Warnings\n"
            "• `.mute` / `.unmute` - Silence Users\n"
            "• `.ban` / `.unban` - Ban Users\n"
            "• `.kick` - Kick User\n"
            "• `.pin` / `.d` - Pin/Delete Msg"
        )

    # 7. ADMIN
    elif data == "help_admin":
        text = (
            "👮 **OWNER COMMANDS**\n\n"
            "• `/admin` - Open Control Panel\n"
            "• `/restart` - Restart Bot\n"
            "• `.stats` - Check Database Stats\n"
            "• `.ping` - System Status"
        )
    
    # Back Button
    kb = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="help_home")]]
    
    if data == "help_home":
        await help_command(update, context)
        return

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
