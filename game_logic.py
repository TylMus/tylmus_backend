from typing import List, Dict, Tuple
import random
from models import Category
from daily_game import daily_generator

class ConnectionsGame:
    def __init__(self):
        self._current_game_state = None

    def generate_game(self) -> Tuple[List[str], List[Category]]:
        categories = daily_generator.get_daily_categories()
        all_words = [word for category in categories for word in category.words]
        
        # Create a shuffled copy without affecting original
        shuffled_words = all_words.copy()
        random.shuffle(shuffled_words)
        
        return shuffled_words, categories

    def check_selection(self, selected_words: List[str], categories: List[Category]) -> Dict:
        # Validate input
        if len(selected_words) != 4:
            return {
                "valid": False, 
                "message": "Выберите ровно 4 слова"
            }

        # Check for exact match with any category
        for category in categories:
            if set(selected_words) == set(category.words):
                return {
                    "valid": True, 
                    "category_name": category.name,
                    "matched_words": category.words
                }

        return {
            "valid": False, 
            "message": "Эти слова не образуют категорию"
        }

game_instance = ConnectionsGame()