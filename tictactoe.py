import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Global Dictionary to store game states
# Key: Message ID, Value: Game Data
ttt_games = {}

# Winning Combinations
WIN_COMBOS = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8], # Rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8], # Cols
    [0, 4, 8], [2, 4, 6]             # Diagonals
]

def to_fancy(text):
    mapping = {'A': 'Λ', 'E': 'Є', 'S': 'δ', 'O': 'σ', 'T': 'ᴛ', 'N': 'ɴ', 'M': 'ᴍ', 'U': 'ᴜ', 'R': 'ʀ', 'D': 'ᴅ', 'C': 'ᴄ', 'P': 'ᴘ', 'G': 'ɢ', 'B': 'ʙ', 'L': 'ʟ', 'W': 'ᴡ', 'K': 'ᴋ', 'J': 'ᴊ', 'Y': 'ʏ', 'I': 'ɪ', 'H': 'ʜ'}
    return "".join(mapping.get(c.upper(), c) for c in text)

# --- 1. START COMMAND (/zero) ---
async def start_ttt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    msg = f"""
<blockquote><b>🎮 {to_fancy("TIC TAC TOE")}</b></blockquote>
<blockquote><b>👤 ᴘʟᴀʏᴇʀ :</b> {html.escape(user.first_name)}
<b>⚔️ ᴍᴏᴅᴇ :</b> 1 vs 1
<b>👇 ᴄʟɪᴄᴋ 'ᴘʟᴀʏ' ᴛᴏ sᴛᴀʀᴛ!</b></blockquote>
"""
    kb = [
        [InlineKeyboardButton("▶️ PLAY", callback_data=f"ttt_init_{user.id}")],
        [InlineKeyboardButton("❌ Close", callback_data="ttt_close")]
    ]
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

# --- 2. GAME LOGIC ---
def check_winner(board):
    for combo in WIN_COMBOS:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] and board[combo[0]] != " ":
            return board[combo[0]] # Returns 'X' or 'O'
    if " " not in board:
        return "Draw"
    return None

def get_board_markup(game_id):
    game = ttt_games[game_id]
    board = game["board"]
    
    kb = []
    # 3x3 Grid
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            idx = i + j
            text = board[idx]
            if text == " ": text = "⬜"
            elif text == "X": text = "❌"
            elif text == "O": text = "⭕"
            
            row.append(InlineKeyboardButton(text, callback_data=f"ttt_move_{idx}"))
        kb.append(row)
    
    kb.append([InlineKeyboardButton("❌ End Game", callback_data="ttt_close")])
    return InlineKeyboardMarkup(kb)

# --- 3. CALLBACK HANDLER ---
async def ttt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    user = q.from_user
    msg_id = q.message.message_id
    chat_id = q.message.chat_id
    
    # A. CLOSE
    if data == "ttt_close":
        if msg_id in ttt_games: del ttt_games[msg_id]
        await q.message.delete()
        return

    # B. INITIALIZE GAME
    if data.startswith("ttt_init_"):
        p1_id = int(data.split("_")[2])
        
        # Game Data Structure
        ttt_games[msg_id] = {
            "board": [" "] * 9,
            "turn": "X",
            "p1": p1_id,
            "p2": None, # Player 2 will be whoever clicks next
            "p1_name": user.first_name,
            "p2_name": "Waiting..."
        }
        
        await q.edit_message_text(
            f"<blockquote><b>🎮 {to_fancy('GAME STARTED')}</b></blockquote>\n<blockquote>❌ <b>Turn:</b> {html.escape(user.first_name)}</blockquote>",
            reply_markup=get_board_markup(msg_id),
            parse_mode=ParseMode.HTML
        )
        return

    # C. PLAYER MOVE
    if data.startswith("ttt_move_"):
        if msg_id not in ttt_games:
            await q.answer("❌ Game Expired!", show_alert=True)
            await q.message.delete()
            return
            
        game = ttt_games[msg_id]
        idx = int(data.split("_")[2])
        
        # Assign Player 2 if not set
        if game["p2"] is None and user.id != game["p1"]:
            game["p2"] = user.id
            game["p2_name"] = user.first_name
            
        # Check Turn
        is_p1 = (user.id == game["p1"])
        is_p2 = (user.id == game["p2"])
        
        if game["turn"] == "X" and not is_p1:
            return await q.answer("❌ Not your turn! (Waiting for X)", show_alert=True)
        if game["turn"] == "O" and not is_p2:
            # If p2 is not set, anyone can join as O
            if game["p2"] is None:
                game["p2"] = user.id
                game["p2_name"] = user.first_name
            else:
                return await q.answer("❌ Not your turn! (Waiting for O)", show_alert=True)
        
        # Check if cell empty
        if game["board"][idx] != " ":
            return await q.answer("⚠️ Already taken!", show_alert=True)
            
        # Make Move
        game["board"][idx] = game["turn"]
        
        # Check Win/Draw
        winner = check_winner(game["board"])
        
        if winner:
            if winner == "Draw":
                txt = f"<blockquote><b>🤝 {to_fancy('GAME DRAW')}!</b></blockquote>\n<blockquote>Nobody won this round.</blockquote>"
            else:
                w_name = game["p1_name"] if winner == "X" else game["p2_name"]
                txt = f"<blockquote><b>👑 {to_fancy('WINNER')} : {html.escape(w_name)}</b></blockquote>\n<blockquote>🎉 Congratulations!</blockquote>"
            
            del ttt_games[msg_id]
            await q.edit_message_text(txt, parse_mode=ParseMode.HTML)
            return
            
        # Switch Turn
        game["turn"] = "O" if game["turn"] == "X" else "X"
        next_player = game["p1_name"] if game["turn"] == "X" else (game["p2_name"] if game["p2_name"] else "Player 2")
        
        await q.edit_message_text(
            f"<blockquote><b>🎮 {to_fancy('GAME ON')}</b></blockquote>\n<blockquote><b>Turn:</b> {game['turn']} ({html.escape(next_player)})</blockquote>",
            reply_markup=get_board_markup(msg_id),
            parse_mode=ParseMode.HTML
        )
