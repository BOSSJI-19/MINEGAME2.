import asyncio
import random
import re
from pyrogram import Client, filters, enums
from pyrogram.handlers import MessageHandler
from config import API_ID, API_HASH
from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.types import InputStickerSetShortName

# 🔥 IMPORTS UPDATE:
# 1. Main DB se sirf Sessions lo
from database import db 
# 2. Stickers ke liye 'tools/db.py' use karo
try:
    from tools.db import add_sticker_pack, get_sticker_packs
except ImportError:
    print("⚠️ Error: tools/db.py nahi mila. Sticker features fail ho sakte hain.")
    def add_sticker_pack(x): pass
    def get_sticker_packs(): return []

from ai_chat import get_yuki_response

# --- MONGODB COLLECTIONS ---
sessions_col = db["userbot_sessions"]
active_chats_col = db["userbot_active_chats"] 

# Global Lists
userbot_clients = [] 
active_ai_chats = {} 

# --- HELPERS ---

async def load_active_chats():
    global active_ai_chats
    all_docs = active_chats_col.find({})
    for doc in all_docs:
        owner_id = doc["owner_id"]
        chat_id = doc["chat_id"]
        if owner_id not in active_ai_chats: active_ai_chats[owner_id] = []
        if chat_id not in active_ai_chats[owner_id]: active_ai_chats[owner_id].append(chat_id)

# 🔥 UPDATED STICKER LOGIC
async def send_random_sticker(client, chat_id):
    try:
        # 1. Database se Packs nikalo (Tools DB se)
        packs = get_sticker_packs()
        
        # 2. Fallback Packs
        if not packs:
            packs = ["Anya_SpyXfamily", "HotCherry_1"] 
        
        # 3. Pack Select karo
        raw_pack = random.choice(packs)
        
        # 4. Name Clean (Link se naam nikalo)
        pack_shortname = raw_pack.replace("https://t.me/addstickers/", "").split("/")[-1]

        # 5. Sticker Fetch & Send
        try:
            sticker_set = await client.get_sticker_set(pack_shortname)
        except Exception as e:
            print(f"⚠️ Sticker Pack Error ({pack_shortname}): {e}")
            sticker_set = await client.get_sticker_set("Anya_SpyXfamily")

        if sticker_set and sticker_set.stickers:
            sticker = random.choice(sticker_set.stickers)
            await client.send_sticker(chat_id, sticker.file_id)
            
    except Exception as e:
        print(f"❌ Userbot Sticker Error: {e}") 

def clean_text(text):
    if not text: return ""
    for char in ["?", "!", ",", "'", ":", "."]: text = text.replace(char, "")
    return text.lower().strip()

# --- COMMAND HANDLERS ---

# 1. ADD STICKER COMMAND (.addsticker)
async def add_sticker_command(client, message):
    try:
        if len(message.command) < 2:
            await message.edit("⚠️ **Usage:** `.addsticker [PackName or Link]`")
            return
        
        raw_input = message.command[1]
        pack_shortname = raw_input.replace("https://t.me/addstickers/", "").split("/")[-1]
            
        await message.edit(f"🔄 **Verifying:** `{pack_shortname}`...")
        
        try:
    await client.invoke(
        GetStickerSet(
            stickerset=InputStickerSetShortName(
                short_name=pack_shortname
            ),
            hash=0
        )
    )
except Exception:
    await message.edit("❌ **Invalid Sticker Pack!** Telegram par nahi mila.")
    return

        # Tools DB me save karo
        add_sticker_pack(pack_shortname)
        await message.edit(f"✅ **Saved!**\n\n📦 Pack: `{pack_shortname}`\n💾 Ab se ye pack use hoga.")
        
    except Exception as e:
        await message.edit(f"❌ Error: {e}")

# 2. CHAT ON/OFF COMMAND (.chat)
async def command_handler(client, message):
    me = await client.get_me()
    my_id = me.id
    chat_id = message.chat.id
    cmd = message.command
    if len(cmd) < 2: return
    action = cmd[1].lower()
    
    if my_id not in active_ai_chats: active_ai_chats[my_id] = []

    if action == "on":
        if chat_id not in active_ai_chats[my_id]:
            active_ai_chats[my_id].append(chat_id)
            active_chats_col.insert_one({"owner_id": my_id, "chat_id": chat_id})
            await message.edit("✅ **AI Chat Enabled** here!")
        else: await message.edit("⚠️ Already Enabled.")
    elif action == "off":
        if chat_id in active_ai_chats[my_id]:
            active_ai_chats[my_id].remove(chat_id)
            active_chats_col.delete_one({"owner_id": my_id, "chat_id": chat_id})
            await message.edit("❌ **AI Chat Disabled** here!")
        else: await message.edit("⚠️ Already Disabled.")
    
    await asyncio.sleep(2)
    try: await message.delete()
    except: pass

# --- AI LOGIC ---

async def ai_reply_logic(client, message):
    try:
        me = await client.get_me()
        my_id = me.id
        chat_id = message.chat.id
        
        if my_id not in active_ai_chats or chat_id not in active_ai_chats[my_id]: return

        is_group = message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]
        should_reply = False
        reply_context = "" 

        # A. STICKER HANDLING
if message.sticker:

    # 🔹 Private chat → always reply with sticker
    if not is_group:
        await asyncio.sleep(random.randint(2, 4))
        await send_random_sticker(client, chat_id)
        return

    # 🔹 Group: reply only if user replied to YOU
    if (
        is_group
        and message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == my_id
    ):
        await asyncio.sleep(random.randint(2, 4))
        await send_random_sticker(client, chat_id)
        return

    return

        # B. TEXT HANDLING
        if not message.text: return

        if not is_group:
            should_reply = True 
        else:
            if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == my_id:
                should_reply = True
                if message.reply_to_message.text:
                    reply_context = f" (Context: User replied to your message: '{message.reply_to_message.text}')"

            elif message.entities:
                for entity in message.entities:
                    if entity.type == enums.MessageEntityType.MENTION and me.username and f"@{me.username}" in message.text:
                        should_reply = True
                        break
                    if entity.type == enums.MessageEntityType.TEXT_MENTION and entity.user.id == my_id:
                        should_reply = True
                        break
            
            if not should_reply:
                text_lower = message.text.lower()
                triggers = ["aniya", "bot", "baby", me.first_name.lower()]
                if any(t in text_lower for t in triggers):
                    should_reply = True

        if not should_reply: return

        try: await client.send_chat_action(chat_id, enums.ChatAction.TYPING)
        except: pass
        
        await asyncio.sleep(random.randint(2, 5))

        query = message.text + reply_context 
        sender_name = message.from_user.first_name if message.from_user else "User"
        
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, get_yuki_response, chat_id, query, sender_name)
        
        if response:
            final_reply = clean_text(response)
            if final_reply: 
                if message.reply_to_message:
                    await message.reply_text(final_reply, quote=True)
                else:
                    await message.reply_text(final_reply)

    except Exception as e:
        pass

# --- STARTERS ---
async def start_new_userbot(user_id):
    await load_active_chats()
    user_data = sessions_col.find_one({"user_id": user_id})
    if not user_data: return
    try:
        app = Client(f"user_{user_id}", api_id=API_ID, api_hash=API_HASH, session_string=user_data['session_string'], in_memory=True)
        
        # Handlers Register
        app.add_handler(MessageHandler(command_handler, filters.command("chat", prefixes=".") & filters.me))
        app.add_handler(MessageHandler(add_sticker_command, filters.command("addsticker", prefixes=".") & filters.me))
        app.add_handler(MessageHandler(ai_reply_logic, (filters.text | filters.sticker) & ~filters.me & ~filters.bot))
        
        await app.start()
        userbot_clients.append(app)
        print(f"✅ Userbot Active: {user_data.get('first_name')}")
    except Exception as e:
        print(f"❌ Userbot Start Error: {e}")

async def start_userbots():
    await load_active_chats()
    print("🔄 Loading Userbots...")
    sessions = sessions_col.find({"is_active": True})
    for user in sessions:
        await start_new_userbot(user["user_id"])

async def stop_userbots():
    for app in userbot_clients:
        try: await app.stop()
        except: pass
            
