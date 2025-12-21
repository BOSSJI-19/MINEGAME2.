import html
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from database import users_col

# Fancy Font Helper
def to_fancy(text):
    mapping = {'A': 'Λ', 'E': 'Є', 'S': 'δ', 'O': 'σ', 'T': 'ᴛ', 'N': 'ɴ', 'M': 'ᴍ', 'U': 'ᴜ', 'R': 'ʀ', 'D': 'ᴅ', 'C': 'ᴄ', 'P': 'ᴘ', 'G': 'ɢ', 'B': 'ʙ', 'L': 'ʟ', 'W': 'ᴡ', 'K': 'ᴋ', 'J': 'ᴊ', 'Y': 'ʏ', 'I': 'ɪ', 'H': 'ʜ'}
    return "".join(mapping.get(c.upper(), c) for c in text)

async def user_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🔥 FIX: Button click par 'message' None hota hai, isliye 'effective_message' use karein
    message = update.effective_message 
    
    # 1. Find Top Killer
    top_killer_data = users_col.find_one(sort=[("kills", -1)])
    top_killer_id = top_killer_data["_id"] if top_killer_data else None

    # 2. Top 10 Richest Users
    top_users = users_col.find().sort("balance", -1).limit(10)
    
    # Header Block
    msg = f"<blockquote><b>🏆 {to_fancy('GLOBAL RICH LIST')}</b></blockquote>\n\n"
    
    rank = 1
    
    for user in top_users:
        name = html.escape(user.get("name", "Unknown"))
        bal = user.get("balance", 0)
        titles = user.get("titles", [])
        kills = user.get("kills", 0)
        user_id = user.get("_id")
        
        # Rank Icons
        if rank == 1: icon = "🥇"
        elif rank == 2: icon = "🥈"
        elif rank == 3: icon = "🥉"
        else: icon = f"<b>{rank}.</b>"
        
        # --- TAGS LOGIC ---
        tags = ""
        if titles: tags += f" [<b>{html.escape(titles[0])}</b>]"
        if user_id == top_killer_id and kills > 0: tags += " 🔪[<b>THE KILLER</b>]"

        # --- FORMATTING ---
        if rank <= 3:
            msg += f"<blockquote>{icon} <b>{name}</b>{tags}\n💰 <code>₹{bal}</code> | 💀 <code>{kills} Kills</code></blockquote>\n"
        else:
            msg += f"{icon} <b>{name}</b>{tags} — <code>₹{bal}</code>\n"
            
        rank += 1
        
    # 🔥 FIX: Check agar callback query hai to edit kare, nahi to reply kare
    if update.callback_query:
        await message.edit_text(msg, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(msg, parse_mode=ParseMode.HTML)
