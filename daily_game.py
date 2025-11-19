from datetime import datetime, timezone
from typing import List
import hashlib
import random
import database
from models import Category

class DailyGameGenerator:
    def __init__(self):
        self._current_categories = None
        self._current_date = None

    def get_today_date_key(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def get_daily_categories(self) -> List[Category]:
        today_key = self.get_today_date_key()
        
        # Return cached categories if same day
        if (self._current_categories and 
            self._current_date == today_key):
            return self._current_categories
        
        # Generate new categories for new day
        self._current_date = today_key
        self._current_categories = self._generate_deterministic_categories(today_key)
        return self._current_categories

    def _generate_deterministic_categories(self, date_key: str) -> List[Category]:
        seed = int(hashlib.md5(date_key.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        all_categories = database.get_categories()
        
        if len(all_categories) >= 4:
            selected_categories = random.sample(all_categories, 4)
            
            categories = []
            for cat_info in selected_categories:
                words = database.get_words_by_category(cat_info["category_id"])
                if len(words) >= 4:
                    categories.append(Category(
                        name=cat_info["category_name"], 
                        words=words[:4]
                    ))
            
            if len(categories) == 4:
                return categories
        
        return self._get_fallback_categories()

    def _get_fallback_categories(self) -> List[Category]:
        """Fallback categories in case of database issues"""
        fallback_data = [
            ("Фрукты", ["Яблоко", "Банан", "Апельсин", "Виноград"]),
            ("Животные", ["Кошка", "Собака", "Лошадь", "Корова"]),
            ("Цвета", ["Красный", "Синий", "Зеленый", "Желтый"]),
            ("Города", ["Москва", "Париж", "Лондон", "Токио"]),
        ]
        
        return [Category(name=name, words=words) for name, words in fallback_data]

daily_generator = DailyGameGenerator()