import asyncio
import random
import re
from pyrogram import Client, filters, enums
from pyrogram.handlers import MessageHandler
from config import API_ID, API_HASH
from database import db, get_sticker_packs # 🔥 Database se packs lene ke liye import kiya
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

# 🔥 NEW STICKER LOGIC (Database Connected)
async def send_random_sticker(client, chat_id):
    try:
        # 1. Database se Packs nikalo (Jaisa Main Bot karta hai)
        packs = get_sticker_packs()
        
        # 2. Agar Database khali hai, toh Fallback packs use karo
        if not packs:
            packs = ["Anya_SpyXfamily"]
        
        # 3. Random Pack select karo
        pack_shortname = random.choice(packs)
        
        # 4. Pyrogram se Sticker Set fetch karo
        sticker_set = await client.get_sticker_set(pack_shortname)
        
        if sticker_set and sticker_set.stickers:
            sticker = random.choice(sticker_set.stickers)
            await client.send_sticker(chat_id, sticker.file_id)
            
    except Exception as e:
        # print(f"Sticker Error: {e}") 
        pass

def clean_text(text):
    if not text: return ""
    for char in ["?", "!", ",", "'", ":", "."]: text = text.replace(char, "")
    return text.lower().strip()

# --- HANDLERS ---

async def ai_reply_logic(client, message):
    try:
        me = await client.get_me()
        my_id = me.id
        chat_id = message.chat.id
        
        # 1. Check Active Status
        if my_id not in active_ai_chats or chat_id not in active_ai_chats[my_id]: return

        # 2. Setup Variables
        is_group = message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]
        should_reply = False
        reply_context = "" 

        # --- LOGIC START ---

        # Case A: STICKER Handling
        if message.sticker:
            # DM me hamesha sticker bhejo
            if not is_group:
                await asyncio.sleep(random.randint(2, 4))
                await send_random_sticker(client, chat_id)
                return
            
            # Group me sirf tab jab Reply ME ho
            if is_group and message.reply_to_message and message.reply_to_message.from_user.id == my_id:
                await asyncio.sleep(random.randint(2, 4))
                await send_random_sticker(client, chat_id)
                return
            return 

        # Case B: TEXT Handling
        if not message.text: return

        if not is_group:
            should_reply = True 
        else:
            # GROUP Logic:
            
            # Rule 1: Reply to ME
            if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == my_id:
                should_reply = True
                if message.reply_to_message.text:
                    reply_context = f" (Context: User replied to your message: '{message.reply_to_message.text}')"

            # Rule 2: Mention/Tag
            elif message.entities:
                for entity in message.entities:
                    if entity.type == enums.MessageEntityType.MENTION and me.username and f"@{me.username}" in message.text:
                        should_reply = True
                        break
                    if entity.type == enums.MessageEntityType.TEXT_MENTION and entity.user.id == my_id:
                        should_reply = True
                        break
            
            # Rule 3: Name Trigger
            if not should_reply:
                text_lower = message.text.lower()
                triggers = ["aniya", "bot", "baby", me.first_name.lower()]
                if any(t in text_lower for t in triggers):
                    should_reply = True

        # --- EXECUTION ---
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
            await message.edit("on kar diya")
        else: await message.edit("are on hi hai")
    elif action == "off":
        if chat_id in active_ai_chats[my_id]:
            active_ai_chats[my_id].remove(chat_id)
            active_chats_col.delete_one({"owner_id": my_id, "chat_id": chat_id})
            await message.edit("off kar diya")
        else: await message.edit("band hi hai")
    
    await asyncio.sleep(2)
    try: await message.delete()
    except: pass

# --- STARTERS ---
async def start_new_userbot(user_id):
    await load_active_chats()
    user_data = sessions_col.find_one({"user_id": user_id})
    if not user_data: return
    try:
        app = Client(f"user_{user_id}", api_id=API_ID, api_hash=API_HASH, session_string=user_data['session_string'], in_memory=True)
        app.add_handler(MessageHandler(command_handler, filters.command("chat", prefixes=".") & filters.me))
        app.add_handler(MessageHandler(ai_reply_logic, (filters.text | filters.sticker) & ~filters.me & ~filters.bot))
        await app.start()
        userbot_clients.append(app)
    except: pass

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
        
