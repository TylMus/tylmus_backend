from fastapi import FastAPI

from app_middleware import add_cors, setup_request_logging_middleware
from leaderboard import init_leaderboard_table
from routes_game import router as game_router
from routes_leaderboard import router as leaderboard_router

app = FastAPI(title="Connections Game API")

setup_request_logging_middleware(app)
add_cors(app)

app.include_router(game_router)
app.include_router(leaderboard_router)


@app.on_event("startup")
async def startup():
    init_leaderboard_table()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
