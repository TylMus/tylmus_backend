from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import traceback
import os
import database
from models import Category

app = FastAPI(title="Connections Game API")

# ✅ Чтение переменных окружения
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if name == "main":
    import uvicorn
    print(f"🚀 Starting server on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)

current_session = {
    "categories": [],
    "found_categories": [],
    "words": [],
    "game_date": None
}

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
        
        # If we have more than 4, we'll randomly select 4 later
        # If we have exactly 4, use all of them
        # If less than 4, use fallback
        
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

def reset_game():
    try:
        # Use your actual database categories
        all_categories = get_categories_from_db()
        
        if len(all_categories) < 4:
            print("⚠️ Not enough categories from DB, using fallback")
            all_categories = generate_fallback_categories()
        
        # SELECT ONLY 4 RANDOM CATEGORIES for the game
        import random
        selected_categories = random.sample(all_categories, 4)
        
        # Combine words from only the 4 selected categories
        all_words = []
        for category in selected_categories:
            all_words.extend(category.words)
        
        random.shuffle(all_words)
        
        current_session["categories"] = selected_categories
        current_session["found_categories"] = []
        current_session["words"] = all_words
        current_session["game_date"] = datetime.now(timezone.utc)
        
        print(f"🎮 Game reset with {len(all_words)} words and {len(selected_categories)} categories")
        for category in selected_categories:
            print(f"   📝 {category.name}: {category.words}")
        
    except Exception as e:
        print(f"❌ Error resetting game: {e}")
        traceback.print_exc()
        raise

@app.get("/")
async def root():
    return {"message": "Connections Game API is running", "docs": "/docs"}

@app.get("/api/game")
async def get_game():
    try:
        print("GET /api/game called")
        
        if is_new_day_needed() or not current_session["categories"]:
            reset_game()
        
        response_data = {
            "words": current_session["words"],
            "categories": [{"name": cat.name, "words": cat.words} for cat in current_session["categories"]],
            "game_date": current_session["game_date"].isoformat()
        }
        
        print(f"📤 Returning game data: {len(response_data['words'])} words")
        return JSONResponse(response_data)
        
    except Exception as e:
        print(f"❌ Error in /api/game: {e}")
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Internal server error: {str(e)}"}, 
            status_code=500
        )

@app.post("/api/check_selection")
async def check_selection(selected_words: list[str]):
    try:
        print(f"POST /api/check_selection called with: {selected_words}")
        
        if not current_session["categories"]:
            return JSONResponse({"error": "Игра не найдена"}, status_code=404)

        # Check if selection matches any category
        for category in current_session["categories"]:
            print(f"🔍 Checking category: {category.name} with words: {category.words}")
            if set(selected_words) == set(category.words):
                print(f"✅ Match found: {category.name}")
                # Add to found categories
                current_session["found_categories"].append({
                    "name": category.name,
                    "words": selected_words
                })

                remaining = len(current_session["categories"]) - len(current_session["found_categories"])
                
                return {
                    "valid": True,
                    "category_name": category.name,
                    "remaining": remaining,
                    "game_complete": remaining == 0
                }

        print("❌ No category match found")
        return {
            "valid": False,
            "message": "Эти слова не образуют категорию"
        }
        
    except Exception as e:
        print(f"💥 Error in /api/check_selection: {e}")
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Internal server error: {str(e)}"}, 
            status_code=500
        )

def is_new_day_needed():
    if not current_session["game_date"]:
        return True
    
    today = datetime.now(timezone.utc).date()
    game_date = current_session["game_date"].date()
    return today > game_date

@app.get("/api/game_status")
async def get_game_status():
    try:
        if current_session["categories"]:
            return {
                "found_categories": current_session["found_categories"],
                "total_categories": len(current_session["categories"]),
                "remaining": len(current_session["categories"]) - len(current_session["found_categories"]),
                "game_date": current_session["game_date"].isoformat()
            }
        return {"error": "Игра не найдена"}
    except Exception as e:
        print(f"Error in /api/game_status: {e}")
        return {"error": str(e)}

@app.get("/api/daily_info")
async def get_daily_info():
    try:
        today = datetime.now(timezone.utc)
        today_str = today.strftime("%Y-%m-%d")
        
        game_complete = len(current_session["found_categories"]) == 4 if current_session["found_categories"] else False
        
        return {
            "today": today_str,
            "current_game_date": current_session["game_date"].strftime("%Y-%m-%d") if current_session["game_date"] else None,
            "is_new_day": is_new_day_needed(),
            "game_complete": game_complete,
            "found_count": len(current_session["found_categories"])
        }
    except Exception as e:
        print(f"Error in /api/daily_info: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    @app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}