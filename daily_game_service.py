"""Подбор категорий и слов на день (HTTP API)."""
import random
from datetime import date

import database
from http_logging import log_error, log_message
from models import Category
from timezone_yakt import get_yakt_date_str


def get_categories_from_db(user_hash: str) -> list[Category]:
    try:
        db_categories = database.get_categories()
        categories: list[Category] = []
        for cat in db_categories:
            words = database.get_words_by_category(cat["category_id"])
            if len(words) >= 4:
                categories.append(
                    Category(name=cat["category_name"], words=words[:4])
                )
        return categories
    except Exception as e:
        log_error(user_hash, "Error loading categories from DB", e)
        return generate_fallback_categories(user_hash)


def generate_fallback_categories(user_hash: str) -> list[Category]:
    log_message(user_hash, "🔄 Using fallback categories")
    return [
        Category("Фрукты", ["Яблоко", "Апельсин", "Банан", "Виноград"]),
        Category("Транспорт", ["Машина", "Автобус", "Поезд", "Велосипед"]),
        Category("Цвета", ["Красный", "Синий", "Зеленый", "Желтый"]),
        Category("Животные", ["Собака", "Кошка", "Птица", "Рыба"]),
    ]


def create_daily_game(user_hash: str) -> dict:
    """Одна игра на день для всех (дата по якутскому времени)."""
    try:
        all_categories = get_categories_from_db(user_hash)
        if len(all_categories) < 4:
            log_message(user_hash, "⚠️ Not enough categories from DB, using fallback")
            all_categories = generate_fallback_categories(user_hash)

        today_str = get_yakt_date_str()

        if len(all_categories) == 4:
            selected_categories = all_categories
        else:
            rotation_start_str = database.get_rotation_start_date(today_str)
            epoch = date.fromisoformat(rotation_start_str)
            today_date = date.fromisoformat(today_str)
            day_index = max(0, (today_date - epoch).days)
            start = (day_index * 4) % len(all_categories)
            selected_categories = [
                all_categories[(start + i) % len(all_categories)]
                for i in range(4)
            ]

        all_words: list[str] = []
        for category in selected_categories:
            all_words.extend(category.words)

        random.seed(today_str)
        random.shuffle(all_words)

        game_state = {
            "categories": selected_categories,
            "words": all_words,
            "game_date": today_str,
        }
        log_message(user_hash, f"🎮 New daily game created for date: {today_str}")
        return game_state
    except Exception as e:
        log_error(user_hash, "Error creating daily game", e)
        raise
