from pymongo import MongoClient
from config import MONGO_URL

# --- DATABASE CONNECTION (Local for Tools) ---
client = MongoClient(MONGO_URL)
db = client["yuki_database"]
sticker_col = db["tools_sticker_packs"] # Alag collection banayi

def add_sticker_pack(pack_name):
    """
    Sticker pack ko database mein add karta hai.
    """
    # Link safai abhi bhi yahin kar lenge
    if "t.me/addstickers/" in pack_name:
        pack_name = pack_name.split("t.me/addstickers/")[-1]
    
    # DB Update
    sticker_col.update_one(
        {"_id": "sticker_list"},
        {"$addToSet": {"packs": pack_name}}, 
        upsert=True
    )
    return pack_name

def get_sticker_packs():
    """
    Database se packs fetch karta hai.
    """
    data = sticker_col.find_one({"_id": "sticker_list"})
    if data and "packs" in data:
        return data["packs"]
    return []
  
