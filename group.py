from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from database import groups_col, investments_col, users_col, get_group_price, update_balance

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Top 10 Groups nikalo Activity ke hisaab se
    top_groups_cursor = groups_col.find().sort("activity", -1).limit(10)
    top_groups = list(top_groups_cursor)

    if not top_groups:
        await update.message.reply_text("❌ Market abhi khali hai! Koi group active nahi.")
        return

    # 2. List Banao
    msg = "🏢 **TOP GROUPS MARKET** 🏢\n\n"
    rank = 1
    
    for grp in top_groups:
        name = grp.get("name", "Unknown Group")
        activity = grp.get("activity", 0)
        
        # Price Calculation
        price = 10 + (activity * 0.5)

        # 3. HIGHLIGHT LOGIC (Blockquote for Rank 1)
        if rank == 1:
            # '>' lagane se Telegram me vertical line (Blockquote) aati hai
            msg += f"> 👑 **{name}**\n> 🔥 Score: {activity} | 📈 Price: ₹{price}\n\n"
        else:
            # Baaki sab normal dikhenge
            msg += f"{rank}. **{name}**\n   🔥 Score: {activity} | 📈 Price: ₹{price}\n\n"
            
        rank += 1
    
    msg += "💡 _Tip: Kisi bhi group me `/invest` use karein!_"

    # 4. Sirf Text Bhejo (Photo Hata Di)
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def market_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Private chat me mana kar dega
    if update.effective_chat.type == "private": 
        await update.message.reply_text("❌ Ye command sirf Groups me chalti hai!")
        return
        
    gid = update.effective_chat.id
    price = get_group_price(gid)
    
    await update.message.reply_text(
        f"📊 **{update.effective_chat.title}**\n"
        f"💰 Share Price: ₹{price}\n"
        f"🛒 Buy: `/invest <amount>`\n"
        f"💵 Sell: `/sell`", 
        parse_mode=ParseMode.MARKDOWN
    )

async def invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == "private": 
        await update.message.reply_text("❌ Group only!")
        return
        
    try: amount = int(context.args[0])
    except: 
        await update.message.reply_text("⚠️ Usage: `/invest 100`")
        return
        
    u = users_col.find_one({"_id": user.id})
    if not u or u["balance"] < amount: 
        await update.message.reply_text("❌ Low Balance!")
        return
    
    price = get_group_price(chat.id)
    shares = amount / price
    
    update_balance(user.id, -amount)
    investments_col.insert_one({
        "user_id": user.id, 
        "group_id": chat.id, 
        "shares": shares, 
        "invested": amount
    })
    
    await update.message.reply_text(f"✅ **Invested ₹{amount}**\n📈 Shares: {round(shares, 2)} @ ₹{price}", parse_mode=ParseMode.MARKDOWN)

async def sell_shares(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    invs = list(investments_col.find({"user_id": user.id, "group_id": chat.id}))
    if not invs: 
        await update.message.reply_text("❌ Is group me tumhare koi shares nahi hain!")
        return
    
    total_shares = sum(i["shares"] for i in invs)
    current_val = int(total_shares * get_group_price(chat.id))
    
    investments_col.delete_many({"user_id": user.id, "group_id": chat.id})
    update_balance(user.id, current_val)
    
    await update.message.reply_text(f"💵 **Sold Shares!**\n💰 Profit Booked: ₹{current_val}", parse_mode=ParseMode.MARKDOWN)
    
