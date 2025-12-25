import random
import asyncio
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, Application, CommandHandler, CallbackQueryHandler
from telegram.error import BadRequest, Forbidden

# Database imports (agar aapke pass database.py hai)
from database import users_col, get_balance

# Global variables
active_tag_sessions = {}  # Format: {chat_id: {"task": task, "stop": False}}

# EMOJI and MESSAGES (same as before)
EMOJI = [
    "🦋🦋🦋🦋🦋", "🧚🌸🧋🍬🫖", "🥀🌷🌹🌺💐", "🌸🌿💮🌱🌵",
    "❤️💚💙💜🖤", "💓💕💞💗💖", "🌸💐🌺🌹🦋", "🍔🦪🍛🍲🥗",
    "🍎🍓🍒🍑🌶️", "🧋🥤🧋🥛🍷", "🍬🍭🧁🎂🍡", "🍨🧉🍺☕🍻",
    "🥪🥧🍦🍥🍚", "🫖☕🍹🍷🥛", "☕🧃🍩🍦🍙", "🍁🌾💮🍂🌿",
    "🌨️🌥️⛈️🌩️🌧️", "🌷🏵️🌸🌺💐", "💮🌼🌻🍀🍁", "🧟🦸🦹🧙👸",
    "🧅🍠🥕🌽🥦", "🐷🐹🐭🐨🐻‍❄️", "🦋🐇🐀🐈🐈‍⬛", "🌼🌳🌲🌴🌵",
    "🥩🍋🍐🍈🍇", "🍴🍽️🔪🍶🥃", "🕌🏰🏩⛩️🏩", "🎉🎊🎈🎂🎀",
    "🪴🌵🌴🌳🌲", "🎄🎋🎍🎑🎎", "🦅🦜🕊️🦤🦢", "🦤🦩🦚🦃🦆",
    "🐬🦭🦈🐋🐳", "🐔🐟🐠🐡🦐", "🦩🦀🦑🐙🦪", "🐦🦂🕷️🕸️🐚",
    "🥪🍰🥧🍨🍨", " 🥬🍉🧁🧇",
]

TAGMES = [
    "**➠ ɢᴏᴏᴅ ɴɪɢʜᴛ 🌚**",
    "**➠ ᴄʜᴜᴘ ᴄʜᴀᴘ sᴏ ᴊᴀ 🙊**",
    "**➠ ᴘʜᴏɴᴇ ʀᴀᴋʜ ᴋᴀʀ sᴏ ᴊᴀ, ɴᴀʜɪ ᴛᴏ ʙʜᴏᴏᴛ ᴀᴀ ᴊᴀʏᴇɢᴀ..👻**",
    "**➠ ᴀᴡᴇᴇ ʙᴀʙᴜ sᴏɴᴀ ᴅɪɴ ᴍᴇɪɴ ᴋᴀʀ ʟᴇɴᴀ ᴀʙʜɪ sᴏ ᴊᴀᴏ..?? 🥲**",
    "**➠ ᴍᴜᴍᴍʏ ᴅᴇᴋʜᴏ ʏᴇ ᴀᴘɴᴇ ɢғ sᴇ ʙᴀᴀᴛ ᴋʀ ʀʜᴀ ʜ ʀᴀᴊᴀɪ ᴍᴇ ɢʜᴜs ᴋᴀʀ, sᴏ ɴᴀʜɪ ʀᴀʜᴀ 😜**",
    "**➠ ᴘᴀᴘᴀ ʏᴇ ᴅᴇᴋʜᴏ ᴀᴘɴᴇ ʙᴇᴛᴇ ᴋᴏ ʀᴀᴀᴛ ʙʜᴀʀ ᴘʜᴏɴᴇ ᴄʜᴀʟᴀ ʀʜᴀ ʜᴀɪ 🤭**",
    "**➠ ᴊᴀɴᴜ ᴀᴀᴊ ʀᴀᴀᴛ ᴋᴀ sᴄᴇɴᴇ ʙɴᴀ ʟᴇ..?? 🌠**",
    "**➠ ɢɴ sᴅ ᴛᴄ.. 🙂**",
    "**➠ ɢᴏᴏᴅ ɴɪɢʜᴛ sᴡᴇᴇᴛ ᴅʀᴇᴀᴍ ᴛᴀᴋᴇ ᴄᴀʀᴇ..?? ✨**",
    "**➠ ʀᴀᴀᴛ ʙʜᴜᴛ ʜᴏ ɢʏɪ ʜᴀɪ sᴏ ᴊᴀᴏ, ɢɴ..?? 🌌**",
    "**➠ ᴍᴜᴍᴍʏ ᴅᴇᴋʜᴏ 11 ʙᴀᴊɴᴇ ᴡᴀʟᴇ ʜᴀɪ ʏᴇ ᴀʙʜɪ ᴛᴀᴋ ᴘʜᴏɴᴇ ᴄʜᴀʟᴀ ʀʜᴀ ɴᴀʜɪ sᴏ ɴᴀʜɪ ʀᴀʜᴀ 🕦**",
    "**➠ ᴋᴀʟ sᴜʙʜᴀ sᴄʜᴏᴏʟ ɴᴀʜɪ ᴊᴀɴᴀ ᴋʏᴀ, ᴊᴏ ᴀʙʜɪ ᴛᴀᴋ ᴊᴀɢ ʀʜᴇ ʜᴏ 🏫**",
    "**➠ ʙᴀʙᴜ, ɢᴏᴏᴅ ɴɪɢʜᴛ sᴅ ᴛᴄ..?? 😊**",
    "**➠ ᴀᴀᴊ ʙʜᴜᴛ ᴛʜᴀɴᴅ ʜᴀɪ, ᴀᴀʀᴀᴍ sᴇ ᴊᴀʟᴅɪ sᴏ ᴊᴀᴛɪ ʜᴏᴏɴ 🌼**",
    "**➠ ᴊᴀɴᴇᴍᴀɴ, ɢᴏᴏᴅ ɴɪɢʜᴛ 🌷**",
    "**➠ ᴍᴇ ᴊᴀ ʀᴀʜɪ sᴏɴᴇ, ɢɴ sᴅ ᴛᴄ 🏵️**",
    "**➠ ʜᴇʟʟᴏ ᴊɪ ɴᴀᴍᴀsᴛᴇ, ɢᴏᴏᴅ ɴɪɢʜᴛ 🍃**",
    "**➠ ʜᴇʏ, ʙᴀʙʏ ᴋᴋʀʜ..? sᴏɴᴀ ɴᴀʜɪ ʜᴀɪ ᴋʏᴀ ☃️**",
    "**➠ ɢᴏᴏᴅ ɴɪɢʜᴛ ᴊɪ, ʙʜᴜᴛ ʀᴀᴀᴛ ʜᴏ ɢʏɪ..? ⛄**",
    "**➠ ᴍᴇ ᴊᴀ ʀᴀʜɪ ʀᴏɴᴇ, ɪ ᴍᴇᴀɴ sᴏɴᴇ ɢᴏᴏᴅ ɴɪɢʜᴛ ᴊɪ 😁**",
    "**➠ ᴍᴀᴄʜʜᴀʟɪ ᴋᴏ ᴋᴇʜᴛᴇ ʜᴀɪ ғɪsʜ, ɢᴏᴏᴅ ɴɪɢʜᴛ ᴅᴇᴀʀ ᴍᴀᴛ ᴋʀɴᴀ ᴍɪss, ᴊᴀ ʀʜɪ sᴏɴᴇ 🌄**",
    "**➠ ɢᴏᴏᴅ ɴɪɢʜᴛ ʙʀɪɢʜᴛғᴜʟʟ ɴɪɢʜᴛ 🤭**",
    "**➠ ᴛʜᴇ ɴɪɢʜᴛ ʜᴀs ғᴀʟʟᴇɴ, ᴛʜᴇ ᴅᴀʏ ɪs ᴅᴏɴᴇ,, ᴛʜᴇ ᴍᴏᴏɴ ʜᴀs ᴛᴀᴋᴇɴ ᴛʜᴇ ᴘʟᴀᴄᴇ ᴏғ ᴛʜᴇ sᴜɴ... 😊**",
    "**➠ ᴍᴀʏ ᴀʟʟ ʏᴏᴜʀ ᴅʀᴇᴀᴍs ᴄᴏᴍᴇ ᴛʀᴜᴇ ❤️**",
    "**➠ ɢᴏᴏᴅ ɴɪɢʜᴛ sᴘʀɪɴᴋʟᴇs sᴡᴇᴇᴛ ᴅʀᴇᴀᴍ 💚**",
    "**➠ ɢᴏᴏᴅ ɴɪɢʜᴛ, ɴɪɴᴅ ᴀᴀ ʀʜɪ ʜᴀɪ 🥱**",
    "**➠ ᴅᴇᴀʀ ғʀɪᴇɴᴅ ɢᴏᴏᴅ ɴɪɢʜᴛ 💤**",
    "**➠ ʙᴀʙʏ ᴀᴀᴊ ʀᴀᴀᴛ ᴋᴀ sᴄᴇɴᴇ ʙɴᴀ ʟᴇ 🥰**",
    "**➠ ɪᴛɴɪ ʀᴀᴀᴛ ᴍᴇ ᴊᴀɢ ᴋᴀʀ ᴋʏᴀ ᴋᴀʀ ʀʜᴇ ʜᴏ sᴏɴᴀ ɴᴀʜɪ ʜᴀɪ ᴋʏᴀ 😜**",
    "**➠ ᴄʟᴏsᴇ ʏᴏᴜʀ ᴇʏᴇs sɴᴜɢɢʟᴇ ᴜᴘ ᴛɪɢʜᴛ,, ᴀɴᴅ ʀᴇᴍᴇᴍʙᴇʀ ᴛʜᴀᴛ ᴀɴɢᴇʟs, ᴡɪʟʟ ᴡᴀᴛᴄʜ ᴏᴠᴇʀ ʏᴏᴜ ᴛᴏɴɪɢʜᴛ... 💫**",
]

VC_TAG = [
    "**➠ ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ, ᴋᴇsᴇ ʜᴏ 🐱**",
    "**➠ ɢᴍ, sᴜʙʜᴀ ʜᴏ ɢʏɪ ᴜᴛʜɴᴀ ɴᴀʜɪ ʜᴀɪ ᴋʏᴀ 🌤️**",
    "**➠ ɢᴍ ʙᴀʙʏ, ᴄʜᴀɪ ᴘɪ ʟᴏ ☕**",
    "**➠ ᴊᴀʟᴅɪ ᴜᴛʜᴏ, sᴄʜᴏᴏʟ ɴᴀʜɪ ᴊᴀɴᴀ ᴋʏᴀ 🏫**",
    "**➠ ɢᴍ, ᴄʜᴜᴘ ᴄʜᴀᴘ ʙɪsᴛᴇʀ sᴇ ᴜᴛʜᴏ ᴠʀɴᴀ ᴘᴀɴɪ ᴅᴀʟ ᴅᴜɴɢɪ 🧊**",
    "**➠ ʙᴀʙʏ ᴜᴛʜᴏ ᴀᴜʀ ᴊᴀʟᴅɪ ғʀᴇsʜ ʜᴏ ᴊᴀᴏ, ɴᴀsᴛᴀ ʀᴇᴀᴅʏ ʜᴀɪ 🫕**",
    "**➠ ᴏғғɪᴄᴇ ɴᴀʜɪ ᴊᴀɴᴀ ᴋʏᴀ ᴊɪ ᴀᴀᴊ, ᴀʙʜɪ ᴛᴀᴋ ᴜᴛʜᴇ ɴᴀʜɪ 🏣**",
    "**➠ ɢᴍ ᴅᴏsᴛ, ᴄᴏғғᴇᴇ/ᴛᴇᴀ ᴋʏᴀ ʟᴏɢᴇ ☕🍵**",
    "**➠ ʙᴀʙʏ 8 ʙᴀᴊɴᴇ ᴡᴀʟᴇ ʜᴀɪ, ᴀᴜʀ ᴛᴜᴍ ᴀʙʜɪ ᴛᴋ ᴜᴛʜᴇ ɴᴀʜɪ 🕖**",
    "**➠ ᴋʜᴜᴍʙʜᴋᴀʀᴀɴ ᴋɪ ᴀᴜʟᴀᴅ ᴜᴛʜ ᴊᴀᴀ... ☃️**",
    "**➠ ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ ʜᴀᴠᴇ ᴀ ɴɪᴄᴇ ᴅᴀʏ... 🌄**",
    "**➠ ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ, ʜᴀᴠᴇ ᴀ ɢᴏᴏᴅ ᴅᴀʏ... 🪴**",
    "**➠ ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ, ʜᴏᴡ ᴀʀᴇ ʏᴏᴜ ʙᴀʙʏ 😇**",
    "**➠ ᴍᴜᴍᴍʏ ᴅᴇᴋʜᴏ ʏᴇ ɴᴀʟᴀʏᴋ ᴀʙʜɪ ᴛᴀᴋ sᴏ ʀʜᴀ ʜᴀɪ... 😵‍💫**",
    "**➠ ʀᴀᴀᴛ ʙʜᴀʀ ʙᴀʙᴜ sᴏɴᴀ ᴋʀ ʀʜᴇ ᴛʜᴇ ᴋʏᴀ, ᴊᴏ ᴀʙʜɪ ᴛᴋ sᴏ ʀʜᴇ ʜᴏ ᴜᴛʜɴᴀ ɴᴀʜɪ ʜᴀɪ ᴋʏᴀ... 😏**",
    "**➠ ʙᴀʙᴜ ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ ᴜᴛʜ ᴊᴀᴏ ᴀᴜʀ ɢʀᴏᴜᴘ ᴍᴇ sᴀʙ ғʀɪᴇɴᴅs ᴋᴏ ɢᴍ ᴡɪsʜ ᴋʀᴏ... 🌟**",
    "**➠ ᴘᴀᴘᴀ ʏᴇ ᴀʙʜɪ ᴛᴀᴋ ᴜᴛʜ ɴᴀʜɪ, sᴄʜᴏᴏʟ ᴋᴀ ᴛɪᴍᴇ ɴɪᴋᴀʟᴛᴀ ᴊᴀ ʀʜᴀ ʜᴀɪ... 🥲**",
    "**➠ ᴊᴀɴᴇᴍᴀɴ ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ, ᴋʏᴀ ᴋʀ ʀʜᴇ ʜᴏ ... 😅**",
    "**➠ ɢᴍ ʙᴇᴀsᴛɪᴇ, ʙʀᴇᴀᴋғᴀsᴛ ʜᴜᴀ ᴋʏᴀ... 🍳**",
]

# ==================== HELPER FUNCTIONS ====================
async def is_admin(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Check if user is admin in group"""
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ['creator', 'administrator']
    except:
        return False

async def get_chat_members(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Get all non-bot members of a chat"""
    members = []
    try:
        async for member in context.bot.get_chat_members(chat_id):
            if not member.user.is_bot:
                members.append(member.user)
    except Exception as e:
        print(f"Error getting members: {e}")
    return members

async def tag_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, user_name: str, tag_type: str):
    """Tag a single user"""
    try:
        if tag_type == "gn":
            message = f"[{user_name}](tg://user?id={user_id}) {random.choice(TAGMES)}"
        elif tag_type == "gm":
            message = f"[{user_name}](tg://user?id={user_id}) {random.choice(VC_TAG)}"
        else:  # custom
            message = f"[{user_name}](tg://user?id={user_id}) {tag_type}"
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        return True
    except Forbidden:
        print(f"Can't send message to {user_name}")
        return False
    except Exception as e:
        print(f"Error tagging {user_name}: {e}")
        return False

async def tag_all_members(context: ContextTypes.DEFAULT_TYPE, chat_id: int, tag_text: str, tag_type: str):
    """Main tagging function with better error handling"""
    try:
        # Get all members
        members = await get_chat_members(chat_id, context)
        if not members:
            await context.bot.send_message(chat_id, "❌ No members found to tag!")
            return
        
        total_members = len(members)
        await context.bot.send_message(
            chat_id, 
            f"🎯 Starting to tag {total_members} members...\n⏳ This may take a while."
        )
        
        tagged_count = 0
        failed_count = 0
        
        for i, user in enumerate(members, 1):
            # Check if we should stop
            if chat_id in active_tag_sessions and active_tag_sessions[chat_id].get("stop"):
                break
            
            # Tag the user
            success = await tag_user(context, chat_id, user.id, user.first_name, tag_type if tag_type != "custom" else tag_text)
            
            if success:
                tagged_count += 1
            else:
                failed_count += 1
            
            # Send progress every 5 users
            if i % 5 == 0:
                progress_msg = f"📊 Progress: {i}/{total_members}\n✅ Tagged: {tagged_count}\n❌ Failed: {failed_count}"
                await context.bot.send_message(chat_id, progress_msg)
            
            # Delay to avoid rate limits (3-5 seconds between tags)
            await asyncio.sleep(random.uniform(3, 5))
        
        # Send completion message
        completion_msg = f"""
✅ **Tagging Complete!**
━━━━━━━━━━━━━━
📊 **Statistics:**
• Total Members: {total_members}
• Successfully Tagged: {tagged_count}
• Failed: {failed_count}
• Success Rate: {(tagged_count/total_members)*100:.1f}%
━━━━━━━━━━━━━━
"""
        await context.bot.send_message(chat_id, completion_msg, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        print(f"Tagging error: {e}")
        await context.bot.send_message(chat_id, f"❌ Error during tagging: {str(e)}")
    finally:
        # Clean up session
        if chat_id in active_tag_sessions:
            del active_tag_sessions[chat_id]

# ==================== COMMAND HANDLERS ====================
async def tag_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tagall command"""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ This command only works in groups!")
        return
    
    # Check if already running
    if chat.id in active_tag_sessions:
        await update.message.reply_text("⚠️ Tagging is already running! Use /tagstop to stop.")
        return
    
    # Check admin
    if not await is_admin(chat.id, user.id, context):
        await update.message.reply_text("❌ You need to be an admin to use this command!")
        return
    
    # Get tag text
    tag_text = ""
    if update.message.reply_to_message:
        tag_text = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
    elif context.args:
        tag_text = " ".join(context.args)
    
    if not tag_text:
        await update.message.reply_text(
            "📝 Please provide text or reply to a message!\n"
            "Example: `/tagall Good Morning` or reply to a message with `/tagall`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Start tagging
    active_tag_sessions[chat.id] = {"stop": False}
    
    # Run tagging in background
    asyncio.create_task(
        tag_all_members(context, chat.id, tag_text, "custom")
    )
    
    await update.message.reply_text(
        f"🎯 Started tagging with message:\n\n`{tag_text[:100]}...`\n\n"
        f"⏳ Tagging will continue in background.\n"
        f"🛑 Use `/tagstop` to cancel.",
        parse_mode=ParseMode.MARKDOWN
    )

async def tag_all_gm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /gmtag command (Good Morning tag)"""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ This command only works in groups!")
        return
    
    # Check if already running
    if chat.id in active_tag_sessions:
        await update.message.reply_text("⚠️ Tagging is already running! Use /tagstop to stop.")
        return
    
    # Check admin
    if not await is_admin(chat.id, user.id, context):
        await update.message.reply_text("❌ You need to be an admin to use this command!")
        return
    
    # Start tagging
    active_tag_sessions[chat.id] = {"stop": False}
    
    # Run tagging in background
    asyncio.create_task(
        tag_all_members(context, chat.id, "", "gm")
    )
    
    await update.message.reply_text(
        "🌅 **Started Good Morning Tagging!**\n\n"
        "⏳ Tagging all members with Good Morning messages...\n"
        "🛑 Use `/tagstop` to cancel.",
        parse_mode=ParseMode.MARKDOWN
    )

async def tag_all_gn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /gntag command (Good Night tag)"""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ This command only works in groups!")
        return
    
    # Check if already running
    if chat.id in active_tag_sessions:
        await update.message.reply_text("⚠️ Tagging is already running! Use /tagstop to stop.")
        return
    
    # Check admin
    if not await is_admin(chat.id, user.id, context):
        await update.message.reply_text("❌ You need to be an admin to use this command!")
        return
    
    # Start tagging
    active_tag_sessions[chat.id] = {"stop": False}
    
    # Run tagging in background
    asyncio.create_task(
        tag_all_members(context, chat.id, "", "gn")
    )
    
    await update.message.reply_text(
        "🌙 **Started Good Night Tagging!**\n\n"
        "⏳ Tagging all members with Good Night messages...\n"
        "🛑 Use `/tagstop` to cancel.",
        parse_mode=ParseMode.MARKDOWN
    )

async def tag_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop tagging process"""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.id not in active_tag_sessions:
        await update.message.reply_text("ℹ️ No tagging process is currently running.")
        return
    
    # Check admin
    if not await is_admin(chat.id, user.id, context):
        await update.message.reply_text("❌ You need to be an admin to stop tagging!")
        return
    
    # Mark for stopping
    active_tag_sessions[chat.id]["stop"] = True
    await update.message.reply_text("🛑 Stopping tagging process... Please wait.")
    
    # Wait a bit and remove session
    await asyncio.sleep(2)
    if chat.id in active_tag_sessions:
        del active_tag_sessions[chat.id]
        await update.message.reply_text("✅ Tagging stopped successfully!")

async def tag_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check tagging status"""
    chat = update.effective_chat
    
    if chat.id in active_tag_sessions:
        await update.message.reply_text("🔄 Tagging is currently running...")
    else:
        await update.message.reply_text("ℹ️ No active tagging session.")

async def tag_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help for tag commands"""
    help_text = """
🎯 **TAGGER PLUGIN COMMANDS:**

**For Admins Only:**
• `/tagall [text]` - Tag all members with custom text
• `/tagall` (reply to message) - Tag all with replied message
• `/gmtag` - Tag all with Good Morning messages
• `/gntag` - Tag all with Good Night messages
• `/tagstop` - Stop ongoing tagging process
• `/tagstatus` - Check tagging status
• `/taghelp` - Show this help

**Examples:**
`/tagall Hello everyone!`
`/tagall` (reply to a message)
`/gmtag` - Sends GM to everyone
`/gntag` - Sends GN to everyone

⚠️ **Note:** 
• Tagging may take time for large groups
• 3-5 seconds delay between each tag to avoid bans
• Use `/tagstop` to cancel anytime
    """
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def quick_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick tag 5 members only (for testing)"""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ This command only works in groups!")
        return
    
    # Check admin
    if not await is_admin(chat.id, user.id, context):
        await update.message.reply_text("❌ You need to be an admin to use this command!")
        return
    
    await update.message.reply_text("🔸 Tagging 5 members for testing...")
    
    try:
        members = await get_chat_members(chat.id, context)
        members_to_tag = members[:5]  # Only first 5
        
        for user_obj in members_to_tag:
            await tag_user(context, chat.id, user_obj.id, user_obj.first_name, "custom")
            await asyncio.sleep(2)  # Shorter delay for testing
        
        await update.message.reply_text("✅ Quick tag test completed!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ==================== REGISTER HANDLERS ====================
def register_handlers(app: Application):
    """Register all handlers for this plugin"""
    app.add_handler(CommandHandler("tagall", tag_all))
    app.add_handler(CommandHandler("gmtag", tag_all_gm))
    app.add_handler(CommandHandler("gntag", tag_all_gn))
    app.add_handler(CommandHandler("tagstop", tag_stop))
    app.add_handler(CommandHandler("tagstatus", tag_status))
    app.add_handler(CommandHandler("taghelp", tag_help))
    app.add_handler(CommandHandler(["tagcancel", "cancletag"], tag_stop))
    app.add_handler(CommandHandler("tagtest", quick_tag))  # For testing only
    
    print("✅ Tagger Plugin Loaded Successfully!")

# For direct testing
if __name__ == "__main__":
    print("🧪 Testing Tagger Plugin...")
    print("Available commands:")
    print("  /tagall [text] - Tag all with custom text")
    print("  /gmtag - Good Morning tag")
    print("  /gntag - Good Night tag")
    print("  /tagstop - Stop tagging")
    print("  /tagstatus - Check status")
    print("  /tagtest - Quick test (tags 5 members)")
