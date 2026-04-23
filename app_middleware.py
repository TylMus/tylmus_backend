"""HTTP middleware и CORS (без изменения путей API)."""
import time

from fastapi import FastAPI, Request

from http_logging import get_user_hash, log_message


def setup_request_logging_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        user_hash = get_user_hash(request)
        start_time = time.time()
        log_message(user_hash, f"→ {request.method} {request.url.path}")
        response = await call_next(request)
        process_time = time.time() - start_time
        log_message(
            user_hash,
            f"← {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)",
        )
        if not request.cookies.get("user_hash"):
            response.set_cookie(
                key="user_hash",
                value=user_hash,
                max_age=365 * 24 * 60 * 60,
                httponly=True,
                samesite="none",
                secure=True,
                domain=".twc1.net",
            )
        return response


def add_cors(app: FastAPI) -> None:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://tylmus.ru",
            "https://www.tylmus.ru",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
