from telegram import Update, ChatPermissions
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from database import add_warning, remove_warning, reset_warnings
from config import OWNER_ID


# ─────────────────────────────────────────────
# HELPER: CHECK ADMIN
# ─────────────────────────────────────────────
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    # Owner always allowed
    if str(user.id) == str(OWNER_ID):
        return True

    # Private chat block
    if chat.type == "private":
        await update.message.reply_text("❌ Ye command sirf group me kaam karti hai.")
        return False

    try:
        member = await chat.get_member(user.id)
        if member.status in ("administrator", "creator"):
            return True
    except Exception as e:
        print("Admin check error:", e)

    await update.message.reply_text(
        "❌ **Access Denied!** Sirf Admins ye command use kar sakte hain.",
        parse_mode=ParseMode.MARKDOWN
    )
    return False


# ─────────────────────────────────────────────
# HELPER: REQUIRE REPLY
# ─────────────────────────────────────────────
async def require_reply(update: Update, msg: str):
    if not update.message.reply_to_message:
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return False
    return True


# ─────────────────────────────────────────────
# ID COMMAND
# ─────────────────────────────────────────────
async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.message
    reply = msg.reply_to_message

    text = ""

    if reply:
        text += f"👤 **User ID:** `{reply.from_user.id}`\n"
        if reply.forward_from:
            text += f"⏩ **Forwarded User ID:** `{reply.forward_from.id}`\n"
        if reply.forward_from_chat:
            text += f"📢 **Forwarded Chat ID:** `{reply.forward_from_chat.id}`\n"
        if reply.forward_sender_name and not reply.forward_from:
            text += f"⏩ **Forwarded Sender:** {reply.forward_sender_name} (Hidden)\n"
    else:
        text += f"👤 **Your User ID:** `{update.effective_user.id}`\n"

    text += f"👥 **Group ID:** `{chat.id}`"

    try:
        await msg.delete()
    except:
        pass

    await chat.send_message(text, parse_mode=ParseMode.MARKDOWN)


# ─────────────────────────────────────────────
# WARN / UNWARN
# ─────────────────────────────────────────────
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not await require_reply(update, "⚠️ Reply karke `.warn` use karo."):
        return

    try:
        await update.message.delete()
    except:
        pass

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat

    if str(target.id) == str(OWNER_ID) or target.is_bot:
        return await chat.send_message("❌ Owner ya bot ko warn nahi kar sakte!")

    count = add_warning(chat.id, target.id)

    if count >= 3:
        await chat.ban_member(target.id)
        reset_warnings(chat.id, target.id)
        await chat.send_message(f"🚫 **BANNED!**\n👤 {target.first_name} (3 warnings)")
    else:
        await chat.send_message(f"⚠️ **WARNING!**\n👤 {target.first_name}\nCount: {count}/3")


async def unwarn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not await require_reply(update, "⚠️ Reply karke `.unwarn` use karo."):
        return

    try:
        await update.message.delete()
    except:
        pass

    target = update.message.reply_to_message.from_user
    count = remove_warning(update.effective_chat.id, target.id)

    await update.effective_chat.send_message(
        f"✅ **Unwarned!**\n👤 {target.first_name}\nRemaining: {count}"
    )


# ─────────────────────────────────────────────
# MUTE / UNMUTE
# ─────────────────────────────────────────────
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not await require_reply(update, "⚠️ Reply karke `.mute` use karo."):
        return

    try:
        await update.message.delete()
    except:
        pass

    target = update.message.reply_to_message.from_user
    await update.effective_chat.restrict_member(
        target.id,
        ChatPermissions(can_send_messages=False)
    )
    await update.effective_chat.send_message(f"🔇 **Muted!** {target.first_name}")


async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not await require_reply(update, "⚠️ Reply karke `.unmute` use karo."):
        return

    try:
        await update.message.delete()
    except:
        pass

    target = update.message.reply_to_message.from_user
    await update.effective_chat.restrict_member(
        target.id,
        ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_send_polls=True
        )
    )
    await update.effective_chat.send_message(f"🔊 **Unmuted!** {target.first_name}")


# ─────────────────────────────────────────────
# BAN / UNBAN / KICK
# ─────────────────────────────────────────────
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not await require_reply(update, "⚠️ Reply karke `.ban` use karo."):
        return

    try:
        await update.message.delete()
    except:
        pass

    target = update.message.reply_to_message.from_user
    await update.effective_chat.ban_member(target.id)
    await update.effective_chat.send_message(f"🚫 **BANNED!** {target.first_name}")


async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not await require_reply(update, "⚠️ Reply karke `.unban` use karo."):
        return

    try:
        await update.message.delete()
    except:
        pass

    target = update.message.reply_to_message.from_user
    await update.effective_chat.unban_member(target.id)
    await update.effective_chat.send_message(f"✅ **Unbanned!** {target.first_name}")


async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not await require_reply(update, "⚠️ Reply karke `.kick` use karo."):
        return

    try:
        await update.message.delete()
    except:
        pass

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat
    await chat.ban_member(target.id)
    await chat.unban_member(target.id)
    await chat.send_message(f"🦵 **Kicked!** {target.first_name}")


# ─────────────────────────────────────────────
# PIN / DELETE
# ─────────────────────────────────────────────
async def pin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not await require_reply(update, "⚠️ Reply karke `.pin` use karo."):
        return

    try:
        await update.message.delete()
        await update.message.reply_to_message.pin()
    except Exception as e:
        await update.effective_chat.send_message(f"❌ Error: {e}")


async def delete_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not await require_reply(update, "⚠️ Reply karke `.d` use karo."):
        return

    try:
        await update.message.delete()
        await update.message.reply_to_message.delete()
    except Exception as e:
        await update.effective_chat.send_message(f"❌ Error: {e}")


# ─────────────────────────────────────────────
# ADMIN HELP
# ─────────────────────────────────────────────
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass

    text = (
        "🛡️ **Admin Commands** (Works with `.` or `/`)\n\n"
        "🔸 `.id` - Get User / Group / Forward ID\n"
        "🔸 `.warn` - Warn user (3 = Ban)\n"
        "🔸 `.unwarn` - Remove warning\n"
        "🔸 `.mute` - Mute user\n"
        "🔸 `.unmute` - Unmute user\n"
        "🔸 `.ban` - Ban user\n"
        "🔸 `.unban` - Unban user\n"
        "🔸 `.kick` - Kick user\n"
        "🔸 `.promote` - Promote\n"
        "🔸 `.demote` - Demote\n"
        "🔸 `.title` - Set title\n"
        "🔸 `.pin` - Pin message\n"
        "🔸 `.d` - Delete message\n\n"
        "⚠️ Most commands **reply ke saath** use hote hain."
    )

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)