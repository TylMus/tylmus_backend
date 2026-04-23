import json
from typing import Optional

from fastapi import Request, Response

from app_settings import COOKIE_DOMAIN, COOKIE_SAMESITE, COOKIE_SECURE
from http_logging import log_error, log_message
from timezone_yakt import get_yakt_time


def get_user_progress(request: Request, user_hash: str) -> dict:
    try:
        progress_cookie = request.cookies.get("user_progress")
        if progress_cookie:
            progress_data = json.loads(progress_cookie)
            category_colors = ["yellow", "green", "blue", "purple"]
            found_categories = progress_data.get("found_categories", [])

            for i, cat in enumerate(found_categories):
                if isinstance(cat, dict) and "color" not in cat:
                    cat["color"] = category_colors[i] if i < len(category_colors) else "gray"
                elif isinstance(cat, str):
                    found_categories[i] = {
                        "name": cat,
                        "words": [],
                        "color": category_colors[i] if i < len(category_colors) else "gray",
                    }

            if "mistakes" not in progress_data:
                progress_data["mistakes"] = 0
            if "started_at" not in progress_data:
                progress_data["started_at"] = get_yakt_time().isoformat()

            log_message(
                user_hash,
                f"📖 Loaded user progress: {len(found_categories)} categories, {progress_data['mistakes']} mistakes",
            )
            return progress_data

        log_message(user_hash, "📖 No user progress found")
        return {"found_categories": [], "game_date": None, "mistakes": 0, "started_at": None}

    except (json.JSONDecodeError, KeyError) as e:
        log_error(user_hash, "Error parsing user progress cookie", e)
        return {"found_categories": [], "game_date": None, "mistakes": 0, "started_at": None}


def set_user_progress(
    response: Response,
    found_categories,
    game_date,
    mistakes: int = 0,
    user_hash: str = "unknown",
    started_at: Optional[str] = None,
) -> None:
    try:
        category_colors = ["yellow", "green", "blue", "purple"]
        for i, cat in enumerate(found_categories):
            if "color" not in cat:
                cat["color"] = category_colors[i] if i < len(category_colors) else "gray"

        progress_data = {
            "found_categories": found_categories,
            "game_date": game_date,
            "mistakes": mistakes,
            "started_at": started_at or get_yakt_time().isoformat(),
        }

        kwargs = {
            "key": "user_progress",
            "value": json.dumps(progress_data),
            "max_age": 86400 * 2,
            "httponly": True,
            "samesite": COOKIE_SAMESITE,
            "secure": COOKIE_SECURE,
        }
        if COOKIE_DOMAIN:
            kwargs["domain"] = COOKIE_DOMAIN
        response.set_cookie(**kwargs)
    except Exception as e:
        log_error(user_hash, "Error setting user progress cookie", e)


def is_same_day(date1, date2) -> bool:
    return date1 == date2
