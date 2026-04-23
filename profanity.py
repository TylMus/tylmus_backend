"""
Profanity filter for multiple languages (English, Russian, Yakut).
Returns True if nickname contains any banned word (case-insensitive).
"""
import re

# English profanity (common ones)
EN_BANNED = {
    "fuck", "shit", "ass", "bitch", "cunt", "dick", "piss", "cock",
    "bastard", "damn", "hell", "nigger", "faggot", "slut", "whore"
}

RU_BANNED = {
    "хуй", "пизда", "еблан", "ебать", "блядь", "пидор", "гандон",
    "мудак", "залупа", "шлюха", "петух", "манда", "пизд", "хуе",
    "ебло", "срака", "говно", "нахуй", "пох", "хер"
}

SAKHA_BANNED = {
    "абас",
    "эмэьэ", 
    "баабыр",
    "дьаабы"
}

BANNED_WORDS = EN_BANNED.union(RU_BANNED).union(SAKHA_BANNED)

def contains_profanity(nickname: str) -> bool:
    """
    Check if nickname contains any banned word.
    Uses word boundaries to avoid false positives (e.g., "assassin").
    """
    nickname_lower = nickname.lower()
    for word in BANNED_WORDS:
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, nickname_lower):
            return True
    return False