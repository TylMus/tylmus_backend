from datetime import datetime, timezone, timedelta, date
from typing import List
import database
from models import Category

YAKT_TIMEZONE = timezone(timedelta(hours=9))

class DailyGameGenerator:
    def __init__(self):
        self._current_categories = None
        self._current_date = None

    def get_today_date_key(self) -> str:
        # Day rollover is based on Yakutsk local time (UTC+9).
        return datetime.now(YAKT_TIMEZONE).strftime("%Y-%m-%d")

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
        all_categories = database.get_categories()

        # Sequential 4 categories per day.
        if len(all_categories) >= 4:
            if len(all_categories) == 4:
                selected_categories = all_categories
            else:
                rotation_start_str = database.get_rotation_start_date(date_key)
                epoch = date.fromisoformat(rotation_start_str)
                day_index = max(0, (date.fromisoformat(date_key) - epoch).days)
                start = (day_index * 4) % len(all_categories)
                selected_categories = [
                    all_categories[(start + i) % len(all_categories)]
                    for i in range(4)
                ]

            categories: List[Category] = []
            for cat_info in selected_categories:
                words = database.get_words_by_category(cat_info["category_id"])
                if len(words) >= 4:
                    categories.append(
                        Category(
                            name=cat_info["category_name"],
                            words=words[:4],
                        )
                    )

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