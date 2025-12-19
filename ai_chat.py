import google.generativeai as genai
from config import OWNER_NAME
from database import get_all_keys
import random

# Global Index
current_key_index = 0

def get_next_key(keys_list):
    """Next API Key nikalta hai list se"""
    global current_key_index
    if not keys_list: return None
    current_key_index = (current_key_index + 1) % len(keys_list)
    return keys_list[current_key_index]

def get_yuki_response(user_text, user_name):
    global current_key_index
    
    # 1. Database se Keys lao
    available_keys = get_all_keys()
    
    if not available_keys:
        return "Arre boss ne API Key nahi daali! (No Keys in DB)"

    # SYSTEM PROMPT (Yuki Persona)
    system_instruction = (
        f"Tera naam Yuki hai. Tu 17 saal ki ladki hai, Delhi se. "
        f"Tu hobby classes (Dance/Art) jati hai. "
        f"Tera owner {OWNER_NAME} hai. "
        f"User ka naam {user_name} hai. "
        f"Reply style: Hinglish, Delhi slang, thoda attitude but cute. "
        f"IMPORTANT: Reply sirf 1 line ka hona chahiye. "
        f"Current Topic: {user_text}"
    )

    # 2. Retry Logic (Keys Rotate karega)
    # Loop max utni baar chalega jitni keys hain
    for _ in range(len(available_keys)):
        try:
            # Current Key uthao
            api_key = available_keys[current_key_index]
            genai.configure(api_key=api_key)
            
            # 🔥 USE GEMINI 1.5 FLASH (Fastest Model)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            response = model.generate_content(system_instruction)
            
            # Agar empty response aye toh skip
            if not response.text: raise Exception("Empty Response")
            
            return response.text.strip()
            
        except Exception as e:
            print(f"⚠️ Key Failed: {e}")
            # Agli key try karo
            get_next_key(available_keys)
            continue

    return "Yaar sar dard ho raha hai... baad me ana. (All Keys Quota Exceeded)"
  
