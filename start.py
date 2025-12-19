from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from database import check_registered, register_user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Check if user is registered
    if not check_registered(user.id):
        # Agar naya user hai toh REGISTER button dikhao
        keyboard = [
            [InlineKeyboardButton("📝 Click to Register", callback_data=f"reg_start_{user.id}")]
        ]
        await update.message.reply_text(
            f"🛑 **Account Not Found!**\n\nHello {user.first_name}, game khelne ke liye pehle register karein.\n\n💰 **Bonus:** ₹500 milega!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Agar purana user hai toh normal welcome
        keyboard = [
            [InlineKeyboardButton("🎮 Play Game", callback_data="help_menu")] # Fake callback for visual
        ]
        await update.message.reply_text(
            f"👋 **Welcome Back, {user.first_name}!**\n\n"
            "Mines Game Bot is Online.\n"
            "Commands:\n"
            "🎮 `/bet 100` - Play Game\n"
            "🛒 `/shop` - Buy Titles\n"
            "🏆 `/ranking` - Group Leaderboard",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
      
