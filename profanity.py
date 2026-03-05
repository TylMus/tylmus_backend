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

# Russian profanity (mat)
RU_BANNED = {
    "хуй", "пизда", "еблан", "ебать", "блядь", "пидор", "гандон",
    "мудак", "залупа", "шлюха", "петух", "манда", "пизд", "хуе",
    "ебло", "срака", "говно", "нахуй", "пох", "хер"
}

# Yakut profanity (common offensive words – to be extended as needed)
SAKHA_BANNED = {
    "кыыс",   # (could be offensive in context)
    "сиикэй", 
    "баабыр",
    "дьаабы"
}

# Combine all banned words (lowercase)
BANNED_WORDS = EN_BANNED.union(RU_BANNED).union(SAKHA_BANNED)

def contains_profanity(nickname: str) -> bool:
    """
    Check if nickname contains any banned word.
    Uses word boundaries to avoid false positives (e.g., "assassin").
    """
    nickname_lower = nickname.lower()
    for word in BANNED_WORDS:
        # regex with word boundaries
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, nickname_lower):
            return True
    return False