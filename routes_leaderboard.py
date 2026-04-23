from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from http_logging import get_user_hash, log_error, log_message
from leaderboard import get_today_leaderboard, get_user_entry, submit_score
from profanity import contains_profanity
from timezone_yakt import get_yakt_date_str, get_yakt_time
from user_progress import get_user_progress, is_same_day

router = APIRouter(tags=["leaderboard"])


@router.post("/api/leaderboard/submit")
async def leaderboard_submit(request: Request, nickname: str):
    user_hash = get_user_hash(request)
    log_message(user_hash, f"Leaderboard submit attempt: nickname='{nickname}'")

    if not nickname or len(nickname) < 2 or len(nickname) > 12:
        return JSONResponse(
            {"error": "Никнейм должен быть от 2 до 12 символов"},
            status_code=400,
        )
    if contains_profanity(nickname):
        return JSONResponse(
            {"error": "Никнейм содержит недопустимые слова"},
            status_code=400,
        )

    today = get_yakt_date_str()
    user_progress = get_user_progress(request, user_hash)
    if not is_same_day(user_progress.get("game_date"), today):
        return JSONResponse({"error": "Игра ещё не начата сегодня"}, status_code=400)

    mistakes = user_progress.get("mistakes", 0)
    found_count = len(user_progress.get("found_categories", []))
    if found_count < 4:
        return JSONResponse({"error": "Игра не завершена"}, status_code=400)

    started_at_raw = user_progress.get("started_at")
    duration_seconds = 0
    if started_at_raw:
        try:
            started_at = datetime.fromisoformat(started_at_raw)
            duration_seconds = max(0, int((get_yakt_time() - started_at).total_seconds()))
        except ValueError:
            duration_seconds = 0

    mistake_penalty = mistakes * 250
    time_penalty = duration_seconds // 6
    points = max(0, 5000 - mistake_penalty - time_penalty)

    success = submit_score(today, user_hash, nickname, mistakes, duration_seconds, points)
    if not success:
        return JSONResponse({"error": "Вы уже отправляли результат сегодня"}, status_code=400)

    log_message(
        user_hash,
        f"✅ Leaderboard entry added: points={points}, mistakes={mistakes}, duration={duration_seconds}s",
    )
    return {
        "success": True,
        "message": "Результат добавлен в таблицу лидеров",
        "points": points,
        "duration_seconds": duration_seconds,
    }


@router.get("/api/leaderboard/today")
async def leaderboard_today(request: Request):
    user_hash = get_user_hash(request)
    today = get_yakt_date_str()
    entries = get_today_leaderboard(today)
    user_entry = get_user_entry(today, user_hash)
    return {"entries": entries, "user_entry": user_entry}
