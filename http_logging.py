"""Идентификация пользователя в логах и печать логов."""
import traceback
import uuid
from typing import Optional

from fastapi import Request

from timezone_yakt import format_yakt_time

def get_user_hash(request: Request) -> str:
    user_hash = request.cookies.get("user_hash")
    if not user_hash:
        user_hash = request.headers.get("x-user-hash")
    if not user_hash:
        user_hash = f"anon_{uuid.uuid4().hex[:8]}"
    return user_hash

def log_message(user_hash: str, message: str) -> None:
    print(f"[{format_yakt_time()}] [USER:{user_hash}] {message}")


def log_error(user_hash: str, message: str, error: Optional[Exception] = None) -> None:
    error_msg = f"❌ {message}"
    if error:
        error_msg += f": {str(error)}"
    print(f"[{format_yakt_time()}] [USER:{user_hash}] {error_msg}")
    if error:
        traceback.print_exc()
