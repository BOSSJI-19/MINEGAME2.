import random
import string
import io
import html
import time
import asyncio
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, JobQueue
import telegram

# --- WORD DATABASE ---
WORDS_POOL = [
    "LOVE", "FOREVER", "DIGAN", "PYTHON", "GAME", "FRIEND", 
    "COUPLE", "HEART", "MUSIC", "VIBE", "TRIBE", "INDIA",
    "BOT", "CODE", "HAPPY", "SMILE", "TRUST", "PEACE",
    "DREAM", "NIGHT", "PARTY", "MONEY", "POWER", "KING"
]

# --- GAME STORAGE ---
active_games = {}
game_timeouts = {}

# --- SETTINGS ---
GRID_SIZE = 8
CELL_SIZE = 60
FONT_PATH = "arial.ttf"
GAME_TIMEOUT = 300  # 5 minutes in seconds

# Fancy Text Converter
def to_fancy(text):
    mapping = {'A': 'Λ', 'E': 'Є', 'S': 'δ', 'O': 'σ', 'T': 'ᴛ', 'N': 'ɴ', 'M': 'ᴍ', 'U': 'ᴜ', 'R': 'ʀ', 'D': 'ᴅ', 'C': 'ᴄ', 'P': 'ᴘ', 'G': 'ɢ', 'B': 'ʙ', 'L': 'ʟ', 'W': 'ᴡ', 'K': 'ᴋ', 'J': 'ᴊ', 'Y': 'ʏ', 'I': 'ɪ', 'H': 'ʜ'}
    return "".join(mapping.get(c.upper(), c) for c in text)

# --- HELPER: CREATE HINT ---
def create_hint(word):
    chars = list(word)
    num_to_hide = len(word) // 2 
    indices_to_hide = random.sample(range(len(word)), num_to_hide)
    for i in indices_to_hide:
        chars[i] = "＿"
    return " ".join(chars)

# --- 1. GENERATE GRID ---
def generate_grid():
    targets = random.sample(WORDS_POOL, 5)
    grid = [['' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    
    # Store word positions for highlighting
    word_positions = {}
    
    for word in targets:
        placed = False
        attempts = 0
        while not placed and attempts < 100:
            direction = random.choice(['H', 'V']) 
            if direction == 'H':
                row = random.randint(0, GRID_SIZE - 1)
                col = random.randint(0, GRID_SIZE - len(word))
                if all(grid[row][col+i] == '' or grid[row][col+i] == word[i] for i in range(len(word))):
                    positions = []
                    for i in range(len(word)):
                        grid[row][col+i] = word[i]
                        positions.append((row, col+i))
                    word_positions[word] = {'direction': 'H', 'positions': positions}
                    placed = True
            else: 
                row = random.randint(0, GRID_SIZE - len(word))
                col = random.randint(0, GRID_SIZE - 1)
                if all(grid[row+i][col] == '' or grid[row+i][col] == word[i] for i in range(len(word))):
                    positions = []
                    for i in range(len(word)):
                        grid[row+i][col] = word[i]
                        positions.append((row+i, col))
                    word_positions[word] = {'direction': 'V', 'positions': positions}
                    placed = True
            attempts += 1
    
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if grid[r][c] == '': 
                grid[r][c] = random.choice(string.ascii_uppercase)
    
    return grid, targets, word_positions

# --- 2. DRAW IMAGE ---
def draw_grid_image(grid, found_words=None, word_positions=None):
    if found_words is None:
        found_words = []
    if word_positions is None:
        word_positions = {}
    
    width = GRID_SIZE * CELL_SIZE
    height = GRID_SIZE * CELL_SIZE + 60 
    img = Image.new('RGB', (width, height), "white")
    draw = ImageDraw.Draw(img)
    
    try:
        # BIGGER FONT SIZE
        font = ImageFont.truetype(FONT_PATH, 36)  # Increased from 30 to 36
        header_font = ImageFont.truetype(FONT_PATH, 45)  # Increased from 40 to 45
    except:
        font = ImageFont.load_default()
        header_font = ImageFont.load_default()
    
    # Draw header
    draw.rectangle([0, 0, width, 60], fill="#0088cc") 
    text = "WORD GRID"
    bbox = draw.textbbox((0, 0), text, font=header_font)
    w = bbox[2] - bbox[0]
    draw.text(((width - w)/2, 10), text, fill="white", font=header_font)
    
    # Draw grid with highlighting for found words
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            x = c * CELL_SIZE
            y = r * CELL_SIZE + 60
            letter = grid[r][c]
            
            # Check if this cell belongs to a found word
            cell_in_found_word = False
            for word in found_words:
                if word in word_positions and (r, c) in word_positions[word]['positions']:
                    cell_in_found_word = True
                    break
            
            # Draw cell with different color if part of found word
            if cell_in_found_word:
                draw.rectangle([x, y, x+CELL_SIZE, y+CELL_SIZE], fill="#90EE90", outline="#4CAF50", width=2)
            else:
                draw.rectangle([x, y, x+CELL_SIZE, y+CELL_SIZE], outline="#dddddd", width=1)
            
            # Draw letter with strike-through if found
            bbox = draw.textbbox((0, 0), letter, font=font)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            
            if cell_in_found_word:
                # Draw letter in different color for found words
                draw.text((x + (CELL_SIZE-lw)/2, y + (CELL_SIZE-lh)/2), letter, fill="#2E7D32", font=font)
                # Draw diagonal line through the cell (X mark)
                draw.line([x+5, y+5, x+CELL_SIZE-5, y+CELL_SIZE-5], fill="#FF5722", width=3)
                draw.line([x+CELL_SIZE-5, y+5, x+5, y+CELL_SIZE-5], fill="#FF5722", width=3)
            else:
                draw.text((x + (CELL_SIZE-lw)/2, y + (CELL_SIZE-lh)/2), letter, fill="black", font=font)
    
    bio = io.BytesIO()
    img.save(bio, format="JPEG")
    bio.seek(0)
    return bio

# --- 3. AUTO-END GAME FUNCTION ---
async def auto_end_game(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    print(f"AUTO-END: Checking game for chat {chat_id}")
    
    if chat_id in active_games:
        game = active_games[chat_id]
        print(f"AUTO-END: Ending game in chat {chat_id}, targets: {game['targets']}")
        
        # Unpin the message
        if game.get('message_pinned'):
            try:
                await context.bot.unpin_chat_message(chat_id=chat_id, message_id=game.get('msg_id'))
                print(f"AUTO-END: Unpinned message {game.get('msg_id')}")
            except Exception as e:
                print(f"AUTO-END: Failed to unpin: {e}")
        
        # Delete game message
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=game.get('msg_id'))
            print(f"AUTO-END: Deleted game message {game.get('msg_id')}")
        except Exception as e:
            print(f"AUTO-END: Failed to delete game message: {e}")
        
        # Send timeout notification
        try:
            timeout_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=f"""⏰ <b>{to_fancy("TIME'S UP")}!</b>

Game ended due to inactivity (5 minutes)

<b>Words were:</b> {', '.join(game['targets'])}
<b>Found:</b> {len(game['found'])}/{len(game['targets'])}""",
                parse_mode=ParseMode.HTML
            )
            print(f"AUTO-END: Sent timeout message")
            # Delete timeout message after 10 seconds
            await asyncio.sleep(10)
            await timeout_msg.delete()
        except Exception as e:
            print(f"AUTO-END: Failed to send timeout message: {e}")
        
        # Clean up
        if chat_id in active_games:
            del active_games[chat_id]
            print(f"AUTO-END: Removed game from active_games")
        if chat_id in game_timeouts:
            del game_timeouts[chat_id]
            print(f"AUTO-END: Removed timeout job")
    else:
        print(f"AUTO-END: No active game found for chat {chat_id}")

# --- 4. START COMMAND ---
async def start_wordgrid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    print(f"START COMMAND: /wordgrid from user {user_id} in chat {chat_id}")
    
    # Delete the command message
    try:
        await update.message.delete()
        print(f"START COMMAND: Deleted command message")
    except Exception as e:
        print(f"START COMMAND: Could not delete command message: {e}")
    
    # Check if game already running in this chat
    if chat_id in active_games:
        warning_msg = await update.message.reply_text(
            f"⚠️ <b>A Word Grid game is already running in this chat!</b>\n"
            f"Complete it or use the 'Give Up' button first.",
            parse_mode=ParseMode.HTML
        )
        # Delete warning after 5 seconds
        await asyncio.sleep(5)
        try:
            await warning_msg.delete()
        except:
            pass
        return
    
    # Generate new game
    grid, targets, word_positions = generate_grid()
    photo = draw_grid_image(grid, [], word_positions)
    hints = {word: create_hint(word) for word in targets}
    
    active_games[chat_id] = {
        'grid': grid, 
        'targets': targets, 
        'hints': hints, 
        'found': [],
        'word_positions': word_positions,
        'message_pinned': False,
        'start_time': time.time(),
        'created_by': update.effective_user.id,
        'last_activity': time.time()
    }
    
    word_list_text = "\n".join([f"▫️ <code>{hints[w]}</code>" for w in targets])
    
    # FIXED HTML - NO EXTRA SPACES, CORRECT TAGS
    caption = f"""<blockquote><b>🧩 {to_fancy("WORD GRID CHALLENGE")}</b></blockquote>
<blockquote>{word_list_text}</blockquote>
<blockquote><b>👇 Type the FULL word to solve!</b>
<b>👨‍💻 Dev:</b> Digan
<b>🎯 Found: 0/{len(targets)} words</b>
<b>⏰ Auto-ends in 5 minutes</b></blockquote>"""
    
    kb = [[InlineKeyboardButton("🏳️ Give Up", callback_data="giveup_wordgrid")]]
    
    # Send the game message
    msg = await update.message.reply_photo(
        photo=photo,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode=ParseMode.HTML
    )
    
    active_games[chat_id]['msg_id'] = msg.message_id
    
    # Try to pin the message
    try:
        await msg.pin(disable_notification=True)
        active_games[chat_id]['message_pinned'] = True
        print(f"START COMMAND: Pinned game message {msg.message_id}")
    except Exception as e:
        print(f"START COMMAND: Could not pin message: {e}")
    
    # Schedule auto-end job - FIXED
    if context.job_queue:
        # Remove any existing timeout for this chat
        if chat_id in game_timeouts:
            try:
                old_job = game_timeouts[chat_id]
                old_job.schedule_removal()
                print(f"START COMMAND: Removed old timeout job")
            except:
                pass
        
        # Schedule new timeout
        job = context.job_queue.run_once(
            auto_end_game,
            when=GAME_TIMEOUT,
            chat_id=chat_id,
            name=f"wordgrid_timeout_{chat_id}"
        )
        game_timeouts[chat_id] = job
        print(f"START COMMAND: Scheduled auto-end job for {GAME_TIMEOUT} seconds from now")
        print(f"START COMMAND: Job name: wordgrid_timeout_{chat_id}")
    else:
        print(f"START COMMAND: No job_queue available!")

# --- 5. HANDLE GUESS ---
async def handle_word_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: 
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Check if there's an active game
    if chat_id not in active_games:
        return
    
    game = active_games[chat_id]
    text = update.message.text.upper().strip()
    
    # Update last activity time
    game['last_activity'] = time.time()
    
    # Debug print
    print(f"GUESS: User {user_id} guessed: '{text}' in chat {chat_id}")
    print(f"GUESS: Game targets: {game['targets']}")
    
    # Check if word is valid
    if text not in game['targets']:
        # Not a valid word - send reaction
        try:
            await update.message.react("❌")
        except Exception as e:
            print(f"GUESS: Error sending ❌ reaction: {e}")
        return
    
    if text in game['found']:
        # Word already found - send reaction
        try:
            await update.message.react("⚠️")
        except Exception as e:
            print(f"GUESS: Error sending ⚠️ reaction: {e}")
        return
    
    # Valid new word found!
    game['found'].append(text)
    print(f"GUESS: Found new word: {text}")
    
    # Reset timeout when word is found - FIXED
    if chat_id in game_timeouts and context.job_queue:
        print(f"GUESS: Resetting timeout for chat {chat_id}")
        # Remove old timeout
        try:
            old_job = game_timeouts[chat_id]
            old_job.schedule_removal()
            print(f"GUESS: Removed old timeout job")
        except Exception as e:
            print(f"GUESS: Error removing old job: {e}")
        
        # Schedule new timeout
        job = context.job_queue.run_once(
            auto_end_game,
            when=GAME_TIMEOUT,
            chat_id=chat_id,
            name=f"wordgrid_timeout_{chat_id}"
        )
        game_timeouts[chat_id] = job
        print(f"GUESS: Scheduled new timeout for {GAME_TIMEOUT} seconds")
    else:
        print(f"GUESS: No job_queue or timeout found for chat {chat_id}")
    
    # Update image
    photo = draw_grid_image(game['grid'], game['found'], game['word_positions'])
    
    # Update caption - COMPACT VERSION
    new_list = []
    for w in game['targets']:
        if w in game['found']:
            new_list.append(f"✅ <s>{w}</s>")
        else:
            new_list.append(f"▫️ <code>{game['hints'][w]}</code>")
    
    progress = len(game['found'])
    total = len(game['targets'])
    
    # FIXED HTML FORMATTING
    caption = f"""<blockquote><b>🧩 {to_fancy("WORD GRID CHALLENGE")}</b></blockquote>
<blockquote>{"\n".join(new_list)}</blockquote>
<blockquote><b>👇 Type the FULL word to solve!</b>
<b>👨‍💻 Dev:</b> Digan
<b>🎯 Found: {progress}/{total} words</b>
<b>⏰ Auto-ends in 5 minutes</b></blockquote>"""
    
    try:
        # Update image
        media = telegram.InputMediaPhoto(media=photo)
        await context.bot.edit_message_media(
            chat_id=chat_id,
            message_id=game['msg_id'],
            media=media
        )
        
        # Update caption
        await context.bot.edit_message_caption(
            chat_id=chat_id,
            message_id=game['msg_id'],
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏳️ Give Up", callback_data="giveup_wordgrid")]])
        )
        
        # ADD REACTION TO USER'S MESSAGE
        try:
            await update.message.react("👍")
            print(f"GUESS: Sent 👍 reaction for word: {text}")
        except Exception as e:
            print(f"GUESS: Error sending 👍 reaction: {e}")
        
        print(f"GUESS: Successfully updated game for word: {text}")
        
    except Exception as e:
        print(f"GUESS: Error updating game: {str(e)}")
    
    # Check if game is complete
    if len(game['found']) == len(game['targets']):
        print(f"GUESS: Game completed! All words found")
        
        # Cancel timeout job
        if chat_id in game_timeouts:
            try:
                job = game_timeouts[chat_id]
                job.schedule_removal()
                del game_timeouts[chat_id]
                print(f"GUESS: Cancelled timeout job")
            except Exception as e:
                print(f"GUESS: Error cancelling timeout: {e}")
        
        # Unpin message
        if game.get('message_pinned'):
            try:
                await context.bot.unpin_chat_message(chat_id=chat_id, message_id=game['msg_id'])
                print(f"GUESS: Unpinned message")
            except Exception as e:
                print(f"GUESS: Error unpinning: {e}")
        
        # Delete game message
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=game['msg_id'])
            print(f"GUESS: Deleted game message")
        except Exception as e:
            print(f"GUESS: Error deleting game message: {e}")
        
        # Send completion message
        final_caption = f"""<blockquote><b>🏆 {to_fancy("GAME COMPLETE")}!</b></blockquote>
<blockquote>✅ All {total} words found!
🎉 Congratulations @{update.effective_user.username if update.effective_user.username else update.effective_user.first_name}!
⏱️ Time: {(time.time() - game['start_time']):.1f}s</blockquote>
<blockquote><b>Words:</b> {', '.join(game['targets'])}
<b>👨‍💻 Dev:</b> Digan</blockquote>"""
        
        try:
            # Send completion message
            completion_msg = await update.message.reply_text(final_caption, parse_mode=ParseMode.HTML)
            
            # Add celebration reaction
            try:
                await update.message.react("🎉")
            except:
                pass
            
            # Delete completion message after 15 seconds
            await asyncio.sleep(15)
            await completion_msg.delete()
            
        except Exception as e:
            print(f"GUESS: Error sending completion: {e}")
        
        # Clean up
        del active_games[chat_id]
        print(f"GUESS: Game cleaned up from active_games")

# --- 6. GIVE UP ---
async def give_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    print(f"GIVE UP: User gave up in chat {chat_id}")
    
    if chat_id in active_games:
        game = active_games[chat_id]
        targets = game['targets']
        
        # Cancel timeout job
        if chat_id in game_timeouts:
            try:
                job = game_timeouts[chat_id]
                job.schedule_removal()
                del game_timeouts[chat_id]
                print(f"GIVE UP: Cancelled timeout job")
            except Exception as e:
                print(f"GIVE UP: Error cancelling timeout: {e}")
        
        # Unpin message
        if game.get('message_pinned'):
            try:
                await context.bot.unpin_chat_message(chat_id=chat_id, message_id=game['msg_id'])
                print(f"GIVE UP: Unpinned message")
            except Exception as e:
                print(f"GIVE UP: Error unpinning: {e}")
        
        # Delete game message
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=game['msg_id'])
            print(f"GIVE UP: Deleted game message")
        except Exception as e:
            print(f"GIVE UP: Error deleting game message: {e}")
        
        # Send give up message
        giveup_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=f"""<blockquote><b>❌ {to_fancy("GAME OVER")}</b></blockquote>
<blockquote>🏳️ Game ended by user
⏱️ Time played: {(time.time() - game['start_time']):.1f}s</blockquote>
<blockquote><b>Words were:</b> {', '.join(targets)}
<b>Found:</b> {len(game['found'])}/{len(targets)}</blockquote>""",
            parse_mode=ParseMode.HTML
        )
        
        # Delete give up message after 10 seconds
        await asyncio.sleep(10)
        try:
            await giveup_msg.delete()
        except:
            pass
        
        # Remove game
        del active_games[chat_id]
        print(f"GIVE UP: Game removed from active_games")
    else:
        await query.answer("No active game.", show_alert=True)

# --- 7. CALLBACK HANDLER ---
async def grid_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "giveup_wordgrid":
        await give_up(update, context)

# --- 8. CLEANUP FUNCTION ---
def cleanup_old_games():
    """Clean up games older than timeout + buffer"""
    current_time = time.time()
    chats_to_remove = []
    
    for chat_id, game in active_games.items():
        if current_time - game['start_time'] > GAME_TIMEOUT + 60:  # 6 minutes
            chats_to_remove.append(chat_id)
            print(f"CLEANUP: Removing stale game from chat {chat_id}")
    
    for chat_id in chats_to_remove:
        if chat_id in active_games:
            del active_games[chat_id]
        if chat_id in game_timeouts:
            del game_timeouts[chat_id]

# Export functions
__all__ = [
    'start_wordgrid',
    'handle_word_guess',
    'grid_callback',
    'give_up',
    'cleanup_old_games'
]