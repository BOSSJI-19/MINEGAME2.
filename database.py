import pymongo
from config import MONGO_URL

try:
    client = pymongo.MongoClient(MONGO_URL)
    db = client["CasinoBot"]
    users_col = db["users"]
    groups_col = db["groups"]
    investments_col = db["investments"]
    codes_col = db["codes"]
    print("✅ Database Connected!")
except Exception as e:
    print(f"❌ DB Error: {e}")

# --- HELPER FUNCTIONS ---

def check_registered(user_id):
    return users_col.find_one({"_id": user_id}) is not None

def register_user(user_id, name):
    if check_registered(user_id): return False
    user = {
        "_id": user_id, 
        "name": name, 
        "balance": 500,  # Bonus
        "loan": 0,
        "titles": []     # Shop items yahan aayenge
    } 
    users_col.insert_one(user)
    return True

def get_user(user_id):
    return users_col.find_one({"_id": user_id})

def update_balance(user_id, amount):
    users_col.update_one({"_id": user_id}, {"$inc": {"balance": amount}}, upsert=True)

def get_balance(user_id):
    user = users_col.find_one({"_id": user_id})
    return user["balance"] if user else 0

def update_group_activity(group_id, group_name):
    groups_col.update_one(
        {"_id": group_id},
        {"$set": {"name": group_name}, "$inc": {"activity": 1}},
        upsert=True
    )

def get_group_price(group_id):
    grp = groups_col.find_one({"_id": group_id})
    if not grp: return 10.0
    return round(10 + (grp.get("activity", 0) * 0.5), 2)
  
