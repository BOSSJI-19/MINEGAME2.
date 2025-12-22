import os
import asyncio
from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from config import API_ID, API_HASH, SESSION_STRING

# 1. Initialize Assistant Client
app = Client(
    "music_assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# 2. Initialize Music Player
call_py = PyTgCalls(app)

# 🔥 START FUNCTION (Main.py me call hoga)
async def start_music_bot():
    print("🎵 Starting Music Assistant...")
    await app.start()
    await call_py.start()
    print("✅ Music System Ready!")

# 🔥 PLAY FUNCTION
async def play_audio(chat_id, file_path):
    try:
        await call_py.play(
            chat_id,
            MediaStream(
                file_path,
            )
        )
        return True
    except Exception as e:
        print(f"Play Error: {e}")
        return False

# 🔥 STOP FUNCTION
async def stop_audio(chat_id):
    try:
        await call_py.leave_group_call(chat_id)
    except:
        pass
