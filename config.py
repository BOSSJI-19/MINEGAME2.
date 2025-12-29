import os

# ⚙️ TELEGRAM API CONFIG (Userbot ke liye Bahut Zaruri hai)
# Ye tumhe my.telegram.org se milega. Agar .env me nahi hai to yahan direct likh dena
API_ID = int(os.getenv("API_ID", "1234567")) 
API_HASH = os.getenv("API_HASH", "your_api_hash_here")

# 🤖 MAIN BOT CONFIG
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") 
MONGO_URL = os.getenv("MONGO_URL")

# 👑 OWNER SETTINGS
OWNER_ID = 7453179290  # Main Owner (Tum)

# 🔥 Updated Owner List (Tum + Dusra Banda)
OWNER_IDS = [7453179290, 6356015122] 

OWNER_USERNAME = "@THE_BOSS_JI"
OWNER_NAME = "BOSS JI"  # Yuki tumhe is naam se bulayegi

# 🆔 IMPORTANT IDs
LOGGER_ID = -1003639584506 
ASSISTANT_ID = 8457855985

# 🏷️ BOT IDENTITY
BOT_NAME = "ㅤ𝚲𝛈𝛊𝛄𝛂me "

# 🎮 GAME SETTINGS
GRID_SIZE = 4
MAX_LOAN = 5000
LOAN_INTEREST = 0.10
DELETE_TIMER = 17  # Result message kitne seconds baad delete hoga

# 🏆 RANKING IMAGE
DEFAULT_BANNER = "https://i.ibb.co/vzDpQx9/ranking-banner.jpg"

# 🛠️ HELPER VARIABLES
# Agar kabhi zarurat padi ki string session direct config me dalna hai
STRING_SESSION = os.getenv("STRING_SESSION", "")

