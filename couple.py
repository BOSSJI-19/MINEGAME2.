import os
import random
import io
import asyncio
import html
from PIL import Image, ImageDraw, ImageFont, ImageOps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
# 🔥 IMPORT CHAT STATS COLLECTION (Group Specific Data ke liye)
from database import chat_stats_col 

# --- CONFIGURATION ---
BG_IMAGE = "ccpic.png" 
FONT_PATH = "arial.ttf" 

POS_1 = (165, 205)   
POS_2 = (660, 205)
CIRCLE_SIZE = 360    

def to_fancy(text):
    mapping = {'A': 'Λ', 'E': 'Є', 'S': 'δ', 'O': 'σ', 'T': 'ᴛ', 'N': 'ɴ', 'M': 'ᴍ', 'U': 'ᴜ', 'R': 'ʀ', 'D': 'ᴅ', 'C': 'ᴄ', 'P': 'ᴘ', 'G': 'ɢ', 'B': 'ʙ', 'L': 'ʟ', 'W': 'ᴡ', 'K': 'ᴋ', 'J': 'ᴊ', 'Y': 'ʏ', 'I': 'ɪ', 'H': 'ʜ'}
    return "".join(mapping.get(c.upper(), c) for c in text)

# --- SYNC IMAGE PROCESSING ---
def process_image_sync(bg_path, pfp1_bytes, pfp2_bytes, name1, name2):
    try:
        bg = Image.open(bg_path).convert("RGBA")
    except:
        bg = Image.new('RGBA', (1280, 720), (200, 0, 0, 255)) 

    def process_pfp(img_bytes, label_name):
        img = None
        if img_bytes:
            try:
                img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            except: pass

        if img is None:
            img = Image.new('RGBA', (CIRCLE_SIZE, CIRCLE_SIZE), (random.randint(50, 150), random.randint(50, 150), random.randint(150, 250)))
            d = ImageDraw.Draw(img)
            char = label_name[0].upper() if label_name else "?"
            try:
                fnt = ImageFont.truetype(FONT_PATH, 140)
            except:
                fnt = ImageFont.load_default()
            d.text((120, 80), char, fill="white", font=fnt)

        img = ImageOps.fit(img, (CIRCLE_SIZE, CIRCLE_SIZE), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        mask = Image.new('L', (CIRCLE_SIZE, CIRCLE_SIZE), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, CIRCLE_SIZE, CIRCLE_SIZE), fill=255)
        
        result = Image.new('RGBA', (CIRCLE_SIZE, CIRCLE_SIZE), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask=mask)
        return result

    img1 = process_pfp(pfp1_bytes, name1)
    img2 = process_pfp(pfp2_bytes, name2)

    bg.paste(img1, POS_1, img1)
    bg.paste(img2, POS_2, img2)

    draw = ImageDraw.Draw(bg)
    try:
        font = ImageFont.truetype(FONT_PATH, 35)
    except:
        font = ImageFont.load_default()

    name1 = name1[:15]
    bbox1 = draw.textbbox((0, 0), name1, font=font)
    w1 = bbox1[2] - bbox1[0]
    draw.text((POS_1[0] + (CIRCLE_SIZE - w1) // 2, POS_1[1] + CIRCLE_SIZE + 40), name1, font=font, fill="white")

    name2 = name2[:15]
    bbox2 = draw.textbbox((0, 0), name2, font=font)
    w2 = bbox2[2] - bbox2[0]
    draw.text((POS_2[0] + (CIRCLE_SIZE - w2) // 2, POS_2[1] + CIRCLE_SIZE + 40), name2, font=font, fill="white")

    bio = io.BytesIO()
    bio.name = "couple.png"
    bg.save(bio, "PNG")
    bio.seek(0)
    return bio

# --- ASYNC WRAPPER ---
async def make_couple_img(user1, user2, context):
    async def get_bytes(u_id):
        if not u_id: return None
        try:
            photos = await context.bot.get_profile_photos(u_id, limit=1)
            if photos.total_count > 0:
                file = await context.bot.get_file(photos.photos[0][-1].file_id)
                f_stream = io.BytesIO()
                await file.download_to_memory(out=f_stream)
                return f_stream.getvalue()
        except: pass
        return None

    pfp1_bytes, pfp2_bytes = await asyncio.gather(
        get_bytes(user1['id']),
        get_bytes(user2['id'])
    )

    loop = asyncio.get_running_loop()
    final_img = await loop.run_in_executor(
        None, 
        process_image_sync, 
        BG_IMAGE, pfp1_bytes, pfp2_bytes, user1['first_name'], user2['first_name']
    )
    return final_img

# --- COMMAND ---
async def couple_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    bot_id = context.bot.id
    
    msg = await update.message.reply_text("🔍 **Finding active lovers in this group...**", parse_mode=ParseMode.MARKDOWN)

    try:
        # 🔥 FIX: Query 'chat_stats_col' instead of 'users_col'
        # Sirf issi group_id ke active users ko dhundho
        pipeline = [
            {"$match": {"group_id": chat_id, "user_id": {"$ne": bot_id}}}, 
            {"$sample": {"size": 2}}
        ]
        
        random_users = list(chat_stats_col.aggregate(pipeline))
        
        # Agar iss group me stats nahi hain (Koi bola nahi ab tak)
        if len(random_users) < 2:
            return await msg.edit_text("❌ **Not enough active users!**\nLog thoda active honge tabhi couple banega (Mags karo).")

        u1 = random_users[0]
        u2 = random_users[1]
        
        # Note: Chat stats me usually 'user_id' hota hai, '_id' nahi (Depends on your DB structure)
        # Assuming chat_stats stores: {group_id: ..., user_id: ..., first_name: ...}
        
        # Name fetch logic (Agar DB me name na ho to API se lo)
        async def resolve_user(u_doc):
            uid = u_doc.get('user_id')
            name = u_doc.get('first_name', 'Unknown')
            # Fallback: Agar name DB me purana hai ya nahi hai
            if name == 'Unknown':
                try:
                    chat_member = await context.bot.get_chat_member(chat_id, uid)
                    name = chat_member.user.first_name
                except: pass
            return {'id': uid, 'first_name': name}

        user1_data = await resolve_user(u1)
        user2_data = await resolve_user(u2)

        # Generate Image
        photo = await make_couple_img(user1_data, user2_data, context)
        
        caption = f"""
<blockquote><b>💘 {to_fancy("TODAY'S COUPLE")}</b></blockquote>

<blockquote>
<b>🦁 ʙᴏʏ :</b> {html.escape(user1_data['first_name'])}
<b>🐰 ɢɪʀʟ :</b> {html.escape(user2_data['first_name'])}
</blockquote>

<blockquote>
<b>✨ ᴍᴀᴛᴄʜ :</b> 100% ❤️
<b>📅 ᴅᴀᴛᴇ :</b> {to_fancy("FOREVER")}
</blockquote>
"""
        kb = [[InlineKeyboardButton("👨‍💻 Support", url="https://t.me/Dev_Digan")]]
        
        if photo:
            await update.message.reply_photo(
                photo=photo,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode=ParseMode.HTML
            )
        else:
            await msg.edit_text("❌ Failed to generate image.")
            
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")
