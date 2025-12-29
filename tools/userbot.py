import asyncio
import random
from pyrogram import Client, filters, enums
# 🔥 FIX: MessageHandler import karna jaruri hai manual adding ke liye
from pyrogram.handlers import MessageHandler 
from config import API_ID, API_HASH
from database import db
from ai_chat import get_yuki_response

# --- MONGODB COLLECTION ---
sessions_col = db["userbot_sessions"]

# Global List to store running clients
userbot_clients = []
active_ai_chats = {} # Format: {user_id: [chat_id1, chat_id2]}

# --- 1. USERBOT LOGIC (Handlers) ---

async def ai_reply_logic(client, message):
    try:
        me = await client.get_me()
        user_id = me.id
        chat_id = message.chat.id
        
        # Check if AI is active for this user in this chat
        if user_id not in active_ai_chats or chat_id not in active_ai_chats[user_id]:
            return

        # --- Realism Delays ---
        await asyncio.sleep(random.randint(2, 5))
        try:
            await client.send_chat_action(chat_id, enums.ChatAction.TYPING)
        except:
            pass # Agar permission na ho to crash na kare
        await asyncio.sleep(random.randint(3, 5))

        # --- Get AI Response (No-Lag Fix) ---
        query = message.text
        sender_name = message.from_user.first_name if message.from_user else "User"
        
        # 🔥 AI Background Process
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, get_yuki_response, chat_id, query, sender_name)
        
        if response:
            await message.reply_text(response)
            
    except Exception as e:
        print(f"Userbot AI Error: {e}")

async def command_handler(client, message):
    me = await client.get_me()
    user_id = me.id
    chat_id = message.chat.id
    cmd = message.command

    if len(cmd) < 2: return

    action = cmd[1].lower()
    
    if user_id not in active_ai_chats: active_ai_chats[user_id] = []

    if action == "on":
        if chat_id not in active_ai_chats[user_id]:
            active_ai_chats[user_id].append(chat_id)
            await message.edit("🟢 **Yuki AI Activated!**\nMain ab khud baat karungi.")
        else:
            await message.edit("⚠️ Already Active.")
            
    elif action == "off":
        if chat_id in active_ai_chats[user_id]:
            active_ai_chats[user_id].remove(chat_id)
            await message.edit("🔴 **Yuki AI Deactivated!**")
        else:
            await message.edit("⚠️ Already Inactive.")
            
    await asyncio.sleep(3)
    try: await message.delete()
    except: pass


# --- 2. MANAGER FUNCTION (Start all bots) ---

async def start_userbots():
    print("🔄 Loading Userbots from MongoDB...")
    sessions = sessions_col.find({"is_active": True})
    
    count = 0
    for user in sessions:
        try:
            # Create Client
            app = Client(
                f"user_{user['user_id']}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=user['session_string'],
                in_memory=True
            )
            
            # --- 🔥 HANDLERS FIX HERE ---
            # Hum sidha filters pass nahi kar sakte, MessageHandler wrapper chahiye
            
            # 1. Command Handler (.chat on/off)
            app.add_handler(
                MessageHandler(
                    command_handler, 
                    filters.command("chat", prefixes=".") & filters.me
                )
            )
            
            # 2. AI Chat Handler
            app.add_handler(
                MessageHandler(
                    ai_reply_logic,
                    filters.text & ~filters.me & ~filters.bot
                )
            )

            # Start Client
            await app.start()
            userbot_clients.append(app)
            count += 1
            print(f"✅ Userbot Started: {user.get('first_name', user['user_id'])}")
            
        except Exception as e:
            print(f"❌ Failed to start userbot for {user.get('user_id')}: {e}")

    print(f"🚀 Total {count} Userbots are running!")

# --- 3. STOP FUNCTION (Cleanup) ---
async def stop_userbots():
    for app in userbot_clients:
        try: await app.stop()
        except: pass
            
