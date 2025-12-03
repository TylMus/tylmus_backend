from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import traceback
import json
import random
import database  # Your database module
from models import Category  # Your models

app = FastAPI(title="Connections Game API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173"   # Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_categories_from_db():
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
        
        print(f"📊 Loaded {len(categories)} categories from database")
        return categories
        
    except Exception as e:
        print(f"❌ Error loading categories from DB: {e}")
        return generate_fallback_categories()

def generate_fallback_categories():
    """Fallback categories if database fails"""
    print("🔄 Using fallback categories")
    return [
        Category("Фрукты", ["Яблоко", "Апельсин", "Банан", "Виноград"]),
        Category("Транспорт", ["Машина", "Автобус", "Поезд", "Велосипед"]),
        Category("Цвета", ["Красный", "Синий", "Зеленый", "Желтый"]),
        Category("Животные", ["Собака", "Кошка", "Птица", "Рыба"])
    ]

def create_daily_game():
    """Create a daily game - same for everyone today"""
    try:
        # Use your actual database categories
        all_categories = get_categories_from_db()
        
        if len(all_categories) < 4:
            print("⚠️ Not enough categories from DB, using fallback")
            all_categories = generate_fallback_categories()
        
        # Use date-based seed for consistent daily game
        today_str = datetime.now(timezone.utc).date().isoformat()
        random.seed(today_str)  # Same seed for same date
        
        # SELECT ONLY 4 RANDOM CATEGORIES for the game
        selected_categories = random.sample(all_categories, 4)
        
        # Combine words from only the 4 selected categories
        all_words = []
        for category in selected_categories:
            all_words.extend(category.words)
        
        random.shuffle(all_words)
        
        game_state = {
            "categories": selected_categories,
            "words": all_words,
            "game_date": today_str
        }
        
        print(f"🎮 New daily game created for date: {today_str}")
        print(f"   📝 {len(all_words)} words and {len(selected_categories)} categories")
        for category in selected_categories:
            print(f"      {category.name}: {category.words}")
        
        return game_state
        
    except Exception as e:
        print(f"❌ Error creating daily game: {e}")
        traceback.print_exc()
        raise

def get_user_progress(request: Request):
    """Get user's progress from cookie"""
    try:
        progress_cookie = request.cookies.get("user_progress")
        if progress_cookie:
            progress_data = json.loads(progress_cookie)
            print(f"📖 Loaded user progress: {progress_data}")
            return progress_data
        print("📖 No user progress found")
        return {"found_categories": [], "game_date": None}
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Error parsing user progress cookie: {e}")
        return {"found_categories": [], "game_date": None}

def set_user_progress(response: Response, found_categories, game_date):
    """Set user's progress in cookie"""
    try:
        progress_data = {
            "found_categories": found_categories,
            "game_date": game_date
        }
        
        response.set_cookie(
            key="user_progress",
            value=json.dumps(progress_data),
            max_age=86400 * 2,  # 2 days expiration
            httponly=True,
            samesite="lax"
        )
        print(f"💾 Saved user progress: {len(found_categories)} categories")
    except Exception as e:
        print(f"❌ Error setting user progress cookie: {e}")

def is_same_day(date1, date2):
    """Check if two dates are the same day"""
    return date1 == date2

@app.get("/")
async def root():
    return {"message": "Connections Game API is running", "docs": "/docs"}

@app.get("/api/game")
async def get_game(request: Request):
    try:
        print("GET /api/game called")
        
        # Get daily game (same for everyone today)
        daily_game = create_daily_game()
        
        # Get user's personal progress
        user_progress = get_user_progress(request)
        
        # Check if user has progress for today's game
        today = datetime.now(timezone.utc).date().isoformat()
        user_has_todays_progress = is_same_day(user_progress.get("game_date"), today)
        
        found_categories = user_progress["found_categories"] if user_has_todays_progress else []
        
        response_data = {
            "words": daily_game["words"],
            "categories": [{"name": cat.name, "words": cat.words} for cat in daily_game["categories"]],
            "game_date": daily_game["game_date"],
            "found_categories": found_categories,
            "remaining": len(daily_game["categories"]) - len(found_categories)
        }
        
        print(f"📤 Returning game data: {len(response_data['words'])} words, {len(found_categories)} found categories")
        
        # Create response and set cookie with user progress
        response = JSONResponse(response_data)
        if user_has_todays_progress:
            set_user_progress(response, found_categories, today)
        
        return response
        
    except Exception as e:
        print(f"❌ Error in /api/game: {e}")
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Internal server error: {str(e)}"}, 
            status_code=500
        )

@app.post("/api/check_selection")
async def check_selection(selected_words: list[str], request: Request):
    try:
        print(f"POST /api/check_selection called with: {selected_words}")
        
        # Get daily game (same for everyone today)
        daily_game = create_daily_game()
        
        # Get user's current progress
        user_progress = get_user_progress(request)
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Reset progress if it's a new day
        if not is_same_day(user_progress.get("game_date"), today):
            print("🆕 New day detected, resetting progress")
            user_progress = {"found_categories": [], "game_date": today}
        
        found_categories = user_progress["found_categories"]
        
        # Check if selection matches any category
        for category in daily_game["categories"]:
            print(f"🔍 Checking category: {category.name} with words: {category.words}")
            if set(selected_words) == set(category.words):
                print(f"✅ Match found: {category.name}")
                
                # Check if category was already found
                category_already_found = any(
                    found_cat["name"] == category.name 
                    for found_cat in found_categories
                )
                
                if not category_already_found:
                    # Add to found categories
                    found_categories.append({
                        "name": category.name,
                        "words": selected_words
                    })
                    print(f"➕ Added to found categories: {category.name}")
                else:
                    print(f"ℹ️ Category already found: {category.name}")

                remaining = len(daily_game["categories"]) - len(found_categories)
                game_complete = remaining == 0
                
                print(f"📊 Progress: {len(found_categories)}/{len(daily_game['categories'])} categories found")
                
                # Create response
                response_data = {
                    "valid": True,
                    "category_name": category.name,
                    "remaining": remaining,
                    "game_complete": game_complete
                }
                
                response = JSONResponse(response_data)
                set_user_progress(response, found_categories, today)
                
                return response

        print("❌ No category match found")
        response_data = {
            "valid": False,
            "message": "Эти слова не образуют категорию"
        }
        
        response = JSONResponse(response_data)
        set_user_progress(response, found_categories, today)
        
        return response
        
    except Exception as e:
        print(f"💥 Error in /api/check_selection: {e}")
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Internal server error: {str(e)}"}, 
            status_code=500
        )

@app.get("/api/game_status")
async def get_game_status(request: Request):
    try:
        # Get daily game
        daily_game = create_daily_game()
        
        # Get user's progress
        user_progress = get_user_progress(request)
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Reset progress if it's a new day
        if not is_same_day(user_progress.get("game_date"), today):
            user_progress = {"found_categories": [], "game_date": today}
        
        found_categories = user_progress["found_categories"]
        remaining = len(daily_game["categories"]) - len(found_categories)
        
        response_data = {
            "found_categories": found_categories,
            "total_categories": len(daily_game["categories"]),
            "remaining": remaining,
            "game_date": daily_game["game_date"],
            "game_complete": remaining == 0
        }
        
        response = JSONResponse(response_data)
        set_user_progress(response, found_categories, today)
        return response
        
    except Exception as e:
        print(f"Error in /api/game_status: {e}")
        return JSONResponse({"error": str(e)})

@app.get("/api/daily_info")
async def get_daily_info(request: Request):
    try:
        # Get daily game
        daily_game = create_daily_game()
        
        # Get user's progress
        user_progress = get_user_progress(request)
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Reset progress if it's a new day
        if not is_same_day(user_progress.get("game_date"), today):
            user_progress = {"found_categories": [], "game_date": today}
        
        found_categories = user_progress["found_categories"]
        remaining = len(daily_game["categories"]) - len(found_categories)
        
        response_data = {
            "today": today,
            "current_game_date": daily_game["game_date"],
            "game_complete": remaining == 0,
            "found_count": len(found_categories),
            "total_categories": len(daily_game["categories"])
        }
        
        response = JSONResponse(response_data)
        set_user_progress(response, found_categories, today)
        return response
        
    except Exception as e:
        print(f"Error in /api/daily_info: {e}")
        return JSONResponse({"error": str(e)})

@app.post("/api/reset_progress")
async def reset_progress(response: Response):
    """Reset user's progress for current day"""
    today = datetime.now(timezone.utc).date().isoformat()
    set_user_progress(response, [], today)
    return {"message": "Progress reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)