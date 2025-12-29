import asyncio
import random
import re  # 🔥 Text clean karne ke liye
from pyrogram import Client, filters, enums
from pyrogram.handlers import MessageHandler
from config import API_ID, API_HASH
from database import db
from ai_chat import get_yuki_response

# --- MONGODB COLLECTIONS ---
sessions_col = db["userbot_sessions"]
active_chats_col = db["userbot_active_chats"] 

# Global Memory
active_ai_chats = {} 

# --- 1. HELPERS ---

async def load_active_chats():
    """Restart hone par Database se purani chats wapas load karega"""
    global active_ai_chats
    print("📂 Loading Active Chats...")
    
    all_docs = active_chats_col.find({})
    for doc in all_docs:
        owner_id = doc["owner_id"]
        chat_id = doc["chat_id"]
        
        if owner_id not in active_ai_chats:
            active_ai_chats[owner_id] = []
        
        if chat_id not in active_ai_chats[owner_id]:
            active_ai_chats[owner_id].append(chat_id)

async def send_random_sticker(client, chat_id):
    """Random Sticker Bhejega"""
    try:
        packs = [
            "yurucamp_lay", "Menhera_chan_2", "Komi_san", 
            "Anya_SpyXfamily", "Honkai_Star_Rail"
        ]
        pack_shortname = random.choice(packs)
        
        sticker_set = await client.get_sticker_set(pack_shortname)
        if sticker_set and sticker_set.stickers:
            sticker = random.choice(sticker_set.stickers)
            await client.send_sticker(chat_id, sticker.file_id)
    except:
        pass

def clean_text(text):
    """
    Ye function text ko 'Humanize' karega.
    ? ! , ' : sab hata dega aur lowercase kar dega.
    """
    if not text: return ""
    # Remove specific symbols
    for char in ["?", "!", ",", "'", ":", "."]:
        text = text.replace(char, "")
    
    # Optional: Sab lowercase kar do (Casual look)
    return text.lower().strip()

# --- 2. MAIN LOGIC (Text & Sticker) ---

async def ai_reply_logic(client, message):
    try:
        me = await client.get_me()
        owner_id = me.id
        chat_id = message.chat.id
        
        # 🔒 Check Active
        if owner_id not in active_ai_chats or chat_id not in active_ai_chats[owner_id]:
            return

        # --- Human Delay ---
        await asyncio.sleep(random.randint(2, 5))

        # --- CASE 1: STICKER ---
        if message.sticker:
            await send_random_sticker(client, chat_id)
            return

        # --- CASE 2: TEXT ---
        elif message.text:
            try: await client.send_chat_action(chat_id, enums.ChatAction.TYPING)
            except: pass
            
            await asyncio.sleep(random.randint(2, 4))

            query = message.text
            sender_name = message.from_user.first_name if message.from_user else "User"
            
            # AI Response Generation
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, get_yuki_response, chat_id, query, sender_name)
            
            if response:
                # 🔥 HUMANIZER: Yahan hum text saaf kar rahe hain
                final_reply = clean_text(response)
                
                if final_reply:
                    await message.reply_text(final_reply)
            
    except Exception as e:
        print(f"Auto-Reply Error: {e}")

# --- 3. COMMAND HANDLER (.chat on/off) ---

async def command_handler(client, message):
    me = await client.get_me()
    owner_id = me.id
    chat_id = message.chat.id
    cmd = message.command

    if len(cmd) < 2: return
    action = cmd[1].lower()
    
    if owner_id not in active_ai_chats: active_ai_chats[owner_id] = []

    if action == "on":
        if chat_id not in active_ai_chats[owner_id]:
            active_ai_chats[owner_id].append(chat_id)
            active_chats_col.insert_one({"owner_id": owner_id, "chat_id": chat_id})
            
            # Ekdam casual reply
            await message.edit("on kar diya")
            await asyncio.sleep(2)
            try: await message.delete()
            except: pass
        else:
            await message.edit("are on hi hai")
            await asyncio.sleep(2)
            try: await message.delete()
            except: pass

    elif action == "off":
        if chat_id in active_ai_chats[owner_id]:
            active_ai_chats[owner_id].remove(chat_id)
            active_chats_col.delete_one({"owner_id": owner_id, "chat_id": chat_id})
            
            await message.edit("off kar diya")
            await asyncio.sleep(2)
            try: await message.delete()
            except: pass
        else:
            await message.edit("band hi hai")
            await asyncio.sleep(2)
            try: await message.delete()
            except: pass

# --- 4. STARTUP MANAGER ---

async def start_userbots():
    await load_active_chats()
    
    print(f"🔄 Loading Userbots... (Active Chats: {len(active_ai_chats)})")
    
    sessions = sessions_col.find({"is_active": True})
    
    count = 0
    for user in sessions:
        try:
            app = Client(
                f"user_{user['user_id']}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=user['session_string'],
                in_memory=True
            )
            
            app.add_handler(
                MessageHandler(
                    command_handler, 
                    filters.command("chat", prefixes=".") & filters.me
                )
            )
            
            app.add_handler(
                MessageHandler(
                    ai_reply_logic,
                    (filters.text | filters.sticker) & ~filters.me & ~filters.bot
                )
            )

            await app.start()
            userbot_clients.append(app)
            count += 1
            print(f"✅ Userbot Started: {user.get('first_name', user['user_id'])}")
            
        except Exception as e:
            print(f"❌ Failed Userbot: {e}")

    print(f"🚀 Total {count} Userbots Running!")

async def stop_userbots():
    for app in userbot_clients:
        try: await app.stop()
        except: pass
            
