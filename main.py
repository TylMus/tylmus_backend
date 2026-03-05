from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timezone, timedelta
import traceback
import json
import random
import uuid
import time
import database
from models import Category
from leaderboard import init_leaderboard_table, submit_score, get_today_leaderboard, get_user_entry
from profanity import contains_profanity

app = FastAPI(title="Connections Game API")

YAKT_TIMEZONE = timezone(timedelta(hours=9))

def get_yakt_time():
    """Получить текущее время в Якутске"""
    return datetime.now(YAKT_TIMEZONE)

def format_yakt_time():
    """Форматировать время для логов"""
    return get_yakt_time().strftime("%Y-%m-%d %H:%M:%S %Z")

def get_user_hash(request: Request):
    """Получить или создать user_hash для пользователя"""
    user_hash = request.cookies.get("user_hash")
    
    if not user_hash:
        user_hash = request.headers.get("x-user-hash")
    
    if not user_hash:
        user_hash = f"anon_{uuid.uuid4().hex[:8]}"
    
    return user_hash

def log_message(user_hash: str, message: str):
    """Логировать сообщение с user_hash и временем"""
    print(f"[{format_yakt_time()}] [USER:{user_hash}] {message}")

def log_error(user_hash: str, message: str, error: Exception = None):
    """Логировать ошибку с user_hash и временем"""
    error_msg = f"❌ {message}"
    if error:
        error_msg += f": {str(error)}"
    print(f"[{format_yakt_time()}] [USER:{user_hash}] {error_msg}")
    if error:
        traceback.print_exc()

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    user_hash = get_user_hash(request)
    start_time = time.time()
    
    log_message(user_hash, f"→ {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    log_message(user_hash, f"← {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
    
    if not request.cookies.get("user_hash"):
        response.set_cookie(
            key="user_hash",
            value=user_hash,
            max_age=365*24*60*60,  # 1 год
            httponly=True,
            samesite="none",
            secure=True,
            domain=".twc1.net" 
        )
    
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://tylmus.ru",
        "https://www.tylmus.ru",
        "https://tylmus-tylmus-frontend-8a70.twc1.net/"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_categories_from_db(user_hash: str):
    """Get categories from your actual database"""
    try:
        db_categories = database.get_categories()
        categories = []
        
        for cat in db_categories:
            words = database.get_words_by_category(cat["category_id"])
            if len(words) >= 4:
                categories.append(
                    Category(name=cat["category_name"], words=words[:4])
                )
        
        # log_message(user_hash, f"📊 Loaded {len(categories)} categories from database")
        return categories
        
    except Exception as e:
        log_error(user_hash, "Error loading categories from DB", e)
        return generate_fallback_categories(user_hash)

def generate_fallback_categories(user_hash: str):
    """Fallback categories if database fails"""
    log_message(user_hash, "🔄 Using fallback categories")
    return [
        Category("Фрукты", ["Яблоко", "Апельсин", "Банан", "Виноград"]),
        Category("Транспорт", ["Машина", "Автобус", "Поезд", "Велосипед"]),
        Category("Цвета", ["Красный", "Синий", "Зеленый", "Желтый"]),
        Category("Животные", ["Собака", "Кошка", "Птица", "Рыба"])
    ]

def create_daily_game(user_hash: str):
    """Create a daily game - same for everyone today"""
    try:
        all_categories = get_categories_from_db(user_hash)
        
        if len(all_categories) < 4:
            log_message(user_hash, "⚠️ Not enough categories from DB, using fallback")
            all_categories = generate_fallback_categories(user_hash)
        
        today_str = datetime.now(timezone.utc).date().isoformat()
        random.seed(today_str)
        
        selected_categories = random.sample(all_categories, 4)
        
        all_words = []
        for category in selected_categories:
            all_words.extend(category.words)
        
        random.shuffle(all_words)
        
        game_state = {
            "categories": selected_categories,
            "words": all_words,
            "game_date": today_str
        }
        
        log_message(user_hash, f"🎮 New daily game created for date: {today_str}")
        #log_message(user_hash, f"📝 {len(all_words)} words and {len(selected_categories)} categories")
        #for category in selected_categories:
        #    log_message(user_hash, f"      {category.name}: {category.words}")
        
        return game_state
        
    except Exception as e:
        log_error(user_hash, "Error creating daily game", e)
        raise

def get_user_progress(request: Request, user_hash: str):
    """Get user's progress from cookie"""
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
                        "color": category_colors[i] if i < len(category_colors) else "gray"
                    }
            
            if "mistakes" not in progress_data:
                progress_data["mistakes"] = 0
            
            log_message(user_hash, f"📖 Loaded user progress: {len(found_categories)} categories, {progress_data['mistakes']} mistakes")
            return progress_data
        
        log_message(user_hash, "📖 No user progress found")
        return {"found_categories": [], "game_date": None, "mistakes": 0}
    
    except (json.JSONDecodeError, KeyError) as e:
        _error(user_hash, "Error parsing user progress cookie", e)
        return {"found_categories": [], "game_date": None, "mistakes": 0}

def set_user_progress(response: Response, found_categories, game_date, mistakes=0, user_hash: str = "unknown"):
    """Set user's progress in cookie"""
    try:
        # Добавляем цвета к найденным категориям
        category_colors = ["yellow", "green", "blue", "purple"]
        for i, cat in enumerate(found_categories):
            if "color" not in cat:
                cat["color"] = category_colors[i] if i < len(category_colors) else "gray"
        
        progress_data = {
            "found_categories": found_categories,
            "game_date": game_date,
            "mistakes": mistakes
        }
        
        response.set_cookie(
            key="user_progress",
            value=json.dumps(progress_data),
            max_age=86400 * 2,
            httponly=True,
            samesite="none",
            secure=True,
            domain=".twc1.net"
        )
        #log_message(user_hash, f"💾 Saved user progress: {len(found_categories)} categories, {mistakes} mistakes")
    except Exception as e:
        log_error(user_hash, "Error setting user progress cookie", e)

def is_same_day(date1, date2):
    """Check if two dates are the same day"""
    return date1 == date2

@app.get("/")
async def root(request: Request):
    user_hash = get_user_hash(request)
    log_message(user_hash, "Root endpoint accessed")
    return {"message": "Connections Game API is running", "docs": "/docs"}

@app.get("/api/game")
async def get_game(request: Request):
    user_hash = get_user_hash(request)
    
    try:
        daily_game = create_daily_game(user_hash)
        
        user_progress = get_user_progress(request, user_hash)
        
        today = datetime.now(timezone.utc).date().isoformat()
        user_has_todays_progress = is_same_day(user_progress.get("game_date"), today)
        
        found_categories = user_progress["found_categories"] if user_has_todays_progress else []
        mistakes = user_progress["mistakes"] if user_has_todays_progress else 0
        
        category_colors = ["yellow", "green", "blue", "purple"]
        categories_with_colors = []
        
        for i, cat in enumerate(daily_game["categories"]):
            color = category_colors[i] if i < len(category_colors) else "gray"
            categories_with_colors.append({
                "name": cat.name,
                "words": cat.words,
                "color": color
            })
        
        word_color_map = {}
        for i, cat in enumerate(daily_game["categories"]):
            color = category_colors[i] if i < len(category_colors) else "gray"
            for word in cat.words:
                word_color_map[word] = color
        
        response_data = {
            "words": daily_game["words"],
            "categories": categories_with_colors,
            "game_date": daily_game["game_date"],
            "found_categories": found_categories,
            "mistakes": mistakes,
            "remaining": len(daily_game["categories"]) - len(found_categories),
            "word_colors": word_color_map
        }
        
        #log_message(user_hash, f"📤 Returning game data: {len(response_data['words'])} words, {len(found_categories)} found categories, {mistakes} mistakes")
        
        response = JSONResponse(response_data)
        if user_has_todays_progress:
            set_user_progress(response, found_categories, today, mistakes, user_hash)
        
        return response
        
    except Exception as e:
        log_error(user_hash, "Error in /api/game", e)
        return JSONResponse(
            {"error": f"Internal server error: {str(e)}"}, 
            status_code=500
        )
        
@app.post("/api/check_selection")
async def check_selection(selected_words: list[str], request: Request):
    user_hash = get_user_hash(request)
    
    try:
        log_message(user_hash, f"Checking selection: {selected_words}")
        
        daily_game = create_daily_game(user_hash)
        
        user_progress = get_user_progress(request, user_hash)
        today = datetime.now(timezone.utc).date().isoformat()
        
        if not is_same_day(user_progress.get("game_date"), today):
            log_message(user_hash, "🆕 New day detected, resetting progress")
            user_progress = {"found_categories": [], "game_date": today, "mistakes": 0}
        
        found_categories = user_progress["found_categories"]
        mistakes = user_progress.get("mistakes", 0)
        
        # Цвета категорий
        category_colors = ["yellow", "green", "blue", "purple"]
        
        # Создаем мапу: слово → цвет
        word_color_map = {}
        for i, cat in enumerate(daily_game["categories"]):
            color = category_colors[i] if i < len(category_colors) else "gray"
            for word in cat.words:
                word_color_map[word] = color
        
        for i, category in enumerate(daily_game["categories"]):
            if set(selected_words) == set(category.words):
                #log_message(user_hash, f"✅ Match found: {category.name}")
                
                category_already_found = any(
                    found_cat["name"] == category.name 
                    for found_cat in found_categories
                )
                
                if not category_already_found:
                    found_categories.append({
                        "name": category.name,
                        "words": selected_words,
                        "color": category_colors[i] if i < len(category_colors) else "gray"
                    })
                    #log_message(user_hash, f"➕ Added to found categories: {category.name}")
                else:
                    log_message(user_hash, f"ℹ️ Category already found: {category.name}")

                remaining = len(daily_game["categories"]) - len(found_categories)
                game_complete = remaining == 0
                
                #log_message(user_hash, f"📊 Progress: {len(found_categories)}/{len(daily_game['categories'])} categories found, {mistakes} mistakes")
                
                response_data = {
                    "valid": True,
                    "category_name": category.name,
                    "category_color": category_colors[i] if i < len(category_colors) else "gray",
                    "remaining": remaining,
                    "game_complete": game_complete
                }
                
                response = JSONResponse(response_data)
                set_user_progress(response, found_categories, today, mistakes, user_hash)
                
                return response

        log_message(user_hash, "❌ No category match found - adding mistake")
        mistakes += 1
        
        # Определяем цвета выбранных слов
        selected_colors = []
        for word in selected_words:
            if word in word_color_map:
                selected_colors.append(word_color_map[word])
        
        response_data = {
            "valid": False,
            "message": "Эти слова не образуют категорию",
            "mistakes": mistakes,
            "selected_colors": selected_colors  # Новая: цвета выбранных слов
        }
        
        response = JSONResponse(response_data)
        set_user_progress(response, found_categories, today, mistakes, user_hash)
        
        return response
        
    except Exception as e:
        log_error(user_hash, "Error in /api/check_selection", e)
        return JSONResponse(
            {"error": f"Internal server error: {str(e)}"}, 
            status_code=500
        )

@app.get("/api/game_status")
async def get_game_status(request: Request):
    user_hash = get_user_hash(request)
    
    try:
        daily_game = create_daily_game(user_hash)
        
        user_progress = get_user_progress(request, user_hash)
        today = datetime.now(timezone.utc).date().isoformat()
        
        if not is_same_day(user_progress.get("game_date"), today):
            user_progress = {"found_categories": [], "game_date": today, "mistakes": 0}
        
        found_categories = user_progress["found_categories"]
        mistakes = user_progress.get("mistakes", 0)
        remaining = len(daily_game["categories"]) - len(found_categories)
        
        response_data = {
            "found_categories": found_categories,
            "total_categories": len(daily_game["categories"]),
            "remaining": remaining,
            "game_date": daily_game["game_date"],
            "mistakes": mistakes, 
            "game_complete": remaining == 0
        }
        
        response = JSONResponse(response_data)
        set_user_progress(response, found_categories, today, mistakes, user_hash)
        return response
        
    except Exception as e:
        log_error(user_hash, "Error in /api/game_status", e)
        return JSONResponse({"error": str(e)})

@app.get("/api/daily_info")
async def get_daily_info(request: Request):
    user_hash = get_user_hash(request)
    
    try:
        daily_game = create_daily_game(user_hash)
        
        user_progress = get_user_progress(request, user_hash)
        today = datetime.now(timezone.utc).date().isoformat()
        
        if not is_same_day(user_progress.get("game_date"), today):
            user_progress = {"found_categories": [], "game_date": today, "mistakes": 0}
        
        found_categories = user_progress["found_categories"]
        mistakes = user_progress.get("mistakes", 0)
        remaining = len(daily_game["categories"]) - len(found_categories)
        
        response_data = {
            "today": today,
            "current_game_date": daily_game["game_date"],
            "game_complete": remaining == 0,
            "found_count": len(found_categories),
            "total_categories": len(daily_game["categories"]),
            "mistakes": mistakes
        }
        
        response = JSONResponse(response_data)
        set_user_progress(response, found_categories, today, mistakes, user_hash)
        return response
        
    except Exception as e:
        log_error(user_hash, "Error in /api/daily_info", e)
        return JSONResponse({"error": str(e)})

@app.post("/api/reset_progress")
async def reset_progress(request: Request, response: Response):
    """Reset user's progress for current day"""
    user_hash = get_user_hash(request)
    today = datetime.now(timezone.utc).date().isoformat()
    set_user_progress(response, [], today, 0, user_hash)
    log_message(user_hash, "🔄 User progress reset")
    return {"message": "Progress reset successfully"}
@app.on_event("startup")
async def startup():
    init_leaderboard_table()
    print("✅ Leaderboard table initialized")
@app.post("/api/leaderboard/submit")
async def leaderboard_submit(request: Request, nickname: str):
    user_hash = get_user_hash(request)
    log_message(user_hash, f"Leaderboard submit attempt: nickname='{nickname}'")

    # Validate nickname
    if not nickname or len(nickname) < 2 or len(nickname) > 12:
        return JSONResponse({"error": "Никнейм должен быть от 2 до 12 символов"}, status_code=400)
    if contains_profanity(nickname):
        return JSONResponse({"error": "Никнейм содержит недопустимые слова"}, status_code=400)

    # Check if game completed today
    today = datetime.now(timezone.utc).date().isoformat()
    user_progress = get_user_progress(request, user_hash)
    if not is_same_day(user_progress.get("game_date"), today):
        return JSONResponse({"error": "Игра ещё не начата сегодня"}, status_code=400)

    # Get mistakes from progress
    mistakes = user_progress.get("mistakes", 0)
    found_count = len(user_progress.get("found_categories", []))
    if found_count < 4:
        return JSONResponse({"error": "Игра не завершена"}, status_code=400)

    # Submit to leaderboard
    success = submit_score(today, user_hash, nickname, mistakes)
    if not success:
        return JSONResponse({"error": "Вы уже отправляли результат сегодня"}, status_code=400)

    log_message(user_hash, f"✅ Leaderboard entry added: mistakes={mistakes}")
    return {"success": True, "message": "Результат добавлен в таблицу лидеров"}

@app.get("/api/leaderboard/today")
async def leaderboard_today(request: Request):
    user_hash = get_user_hash(request)
    today = datetime.now(timezone.utc).date().isoformat()

    entries = get_today_leaderboard(today)
    user_entry = get_user_entry(today, user_hash)

    return {
        "entries": entries,
        "user_entry": user_entry
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config=None 
    )