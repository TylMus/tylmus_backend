from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from daily_game_service import create_daily_game
from http_logging import get_user_hash, log_error, log_message
from timezone_yakt import get_yakt_date_str, get_yakt_time
from user_progress import get_user_progress, is_same_day, set_user_progress

router = APIRouter(tags=["game"])

CATEGORY_COLORS = ["yellow", "green", "blue", "purple"]


@router.get("/")
async def root(request: Request):
    user_hash = get_user_hash(request)
    log_message(user_hash, "Root endpoint accessed")
    return {"message": "Connections Game API is running", "docs": "/docs"}


@router.get("/api/game")
async def get_game(request: Request):
    user_hash = get_user_hash(request)
    try:
        daily_game = create_daily_game(user_hash)
        user_progress = get_user_progress(request, user_hash)
        today = get_yakt_date_str()
        user_has_todays_progress = is_same_day(user_progress.get("game_date"), today)
        found_categories = user_progress["found_categories"] if user_has_todays_progress else []
        mistakes = user_progress["mistakes"] if user_has_todays_progress else 0

        categories_with_colors = []
        for i, cat in enumerate(daily_game["categories"]):
            color = CATEGORY_COLORS[i] if i < len(CATEGORY_COLORS) else "gray"
            categories_with_colors.append(
                {"name": cat.name, "words": cat.words, "color": color}
            )

        word_color_map = {}
        for i, cat in enumerate(daily_game["categories"]):
            color = CATEGORY_COLORS[i] if i < len(CATEGORY_COLORS) else "gray"
            for word in cat.words:
                word_color_map[word] = color

        response_data = {
            "words": daily_game["words"],
            "categories": categories_with_colors,
            "game_date": daily_game["game_date"],
            "found_categories": found_categories,
            "mistakes": mistakes,
            "remaining": len(daily_game["categories"]) - len(found_categories),
            "word_colors": word_color_map,
        }

        response = JSONResponse(response_data)
        if user_has_todays_progress:
            set_user_progress(
                response,
                found_categories,
                today,
                mistakes,
                user_hash,
                user_progress.get("started_at"),
            )
        return response
    except Exception as e:
        log_error(user_hash, "Error in /api/game", e)
        return JSONResponse(
            {"error": f"Internal server error: {str(e)}"},
            status_code=500,
        )


@router.post("/api/check_selection")
async def check_selection(selected_words: list, request: Request):
    user_hash = get_user_hash(request)
    try:
        log_message(user_hash, f"Checking selection: {selected_words}")
        daily_game = create_daily_game(user_hash)
        user_progress = get_user_progress(request, user_hash)
        today = get_yakt_date_str()

        if not is_same_day(user_progress.get("game_date"), today):
            log_message(user_hash, "🆕 New day detected, resetting progress")
            user_progress = {
                "found_categories": [],
                "game_date": today,
                "mistakes": 0,
                "started_at": get_yakt_time().isoformat(),
            }

        found_categories = user_progress["found_categories"]
        mistakes = user_progress.get("mistakes", 0)

        word_color_map = {}
        for i, cat in enumerate(daily_game["categories"]):
            color = CATEGORY_COLORS[i] if i < len(CATEGORY_COLORS) else "gray"
            for word in cat.words:
                word_color_map[word] = color

        for i, category in enumerate(daily_game["categories"]):
            if set(selected_words) == set(category.words):
                category_already_found = any(
                    found_cat["name"] == category.name for found_cat in found_categories
                )
                if not category_already_found:
                    found_categories.append(
                        {
                            "name": category.name,
                            "words": selected_words,
                            "color": CATEGORY_COLORS[i] if i < len(CATEGORY_COLORS) else "gray",
                        }
                    )
                else:
                    log_message(user_hash, f"ℹ️ Category already found: {category.name}")

                remaining = len(daily_game["categories"]) - len(found_categories)
                game_complete = remaining == 0
                response_data = {
                    "valid": True,
                    "category_name": category.name,
                    "category_color": CATEGORY_COLORS[i] if i < len(CATEGORY_COLORS) else "gray",
                    "remaining": remaining,
                    "game_complete": game_complete,
                }
                response = JSONResponse(response_data)
                set_user_progress(
                    response,
                    found_categories,
                    today,
                    mistakes,
                    user_hash,
                    user_progress.get("started_at"),
                )
                return response

        log_message(user_hash, "❌ No category match found - adding mistake")
        mistakes += 1
        selected_colors = []
        for word in selected_words:
            if word in word_color_map:
                selected_colors.append(word_color_map[word])

        response_data = {
            "valid": False,
            "message": "Эти слова не образуют категорию",
            "mistakes": mistakes,
            "selected_colors": selected_colors,
        }
        response = JSONResponse(response_data)
        set_user_progress(
            response,
            found_categories,
            today,
            mistakes,
            user_hash,
            user_progress.get("started_at"),
        )
        return response
    except Exception as e:
        log_error(user_hash, "Error in /api/check_selection", e)
        return JSONResponse(
            {"error": f"Internal server error: {str(e)}"},
            status_code=500,
        )


@router.get("/api/game_status")
async def get_game_status(request: Request):
    user_hash = get_user_hash(request)
    try:
        daily_game = create_daily_game(user_hash)
        user_progress = get_user_progress(request, user_hash)
        today = get_yakt_date_str()

        if not is_same_day(user_progress.get("game_date"), today):
            user_progress = {
                "found_categories": [],
                "game_date": today,
                "mistakes": 0,
                "started_at": get_yakt_time().isoformat(),
            }

        found_categories = user_progress["found_categories"]
        mistakes = user_progress.get("mistakes", 0)
        remaining = len(daily_game["categories"]) - len(found_categories)

        response_data = {
            "found_categories": found_categories,
            "total_categories": len(daily_game["categories"]),
            "remaining": remaining,
            "game_date": daily_game["game_date"],
            "mistakes": mistakes,
            "game_complete": remaining == 0,
        }
        response = JSONResponse(response_data)
        set_user_progress(
            response,
            found_categories,
            today,
            mistakes,
            user_hash,
            user_progress.get("started_at"),
        )
        return response
    except Exception as e:
        log_error(user_hash, "Error in /api/game_status", e)
        return JSONResponse({"error": str(e)})


@router.get("/api/daily_info")
async def get_daily_info(request: Request):
    user_hash = get_user_hash(request)
    try:
        daily_game = create_daily_game(user_hash)
        user_progress = get_user_progress(request, user_hash)
        today = get_yakt_date_str()

        if not is_same_day(user_progress.get("game_date"), today):
            user_progress = {
                "found_categories": [],
                "game_date": today,
                "mistakes": 0,
                "started_at": get_yakt_time().isoformat(),
            }

        found_categories = user_progress["found_categories"]
        mistakes = user_progress.get("mistakes", 0)
        remaining = len(daily_game["categories"]) - len(found_categories)

        response_data = {
            "today": today,
            "current_game_date": daily_game["game_date"],
            "game_complete": remaining == 0,
            "found_count": len(found_categories),
            "total_categories": len(daily_game["categories"]),
            "mistakes": mistakes,
        }
        response = JSONResponse(response_data)
        set_user_progress(
            response,
            found_categories,
            today,
            mistakes,
            user_hash,
            user_progress.get("started_at"),
        )
        return response
    except Exception as e:
        log_error(user_hash, "Error in /api/daily_info", e)
        return JSONResponse({"error": str(e)})


@router.post("/api/reset_progress")
async def reset_progress(request: Request, response: Response):
    user_hash = get_user_hash(request)
    today = get_yakt_date_str()
    set_user_progress(response, [], today, 0, user_hash, get_yakt_time().isoformat())
    log_message(user_hash, "🔄 User progress reset")
    return {"message": "Progress reset successfully"}
