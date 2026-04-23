"""Настройки из окружения (cookie domain, и т.д.)."""
import os

# Domain задаётся только если API реально отдаёт ответ с хоста из этой зоны
# (например api.tylmus.ru → можно COOKIE_DOMAIN=.tylmus.ru).
# Если API на другом домене (twc1, отдельный VPS, туннель) — НЕ задавать: иначе
# браузер отбросит Set-Cookie и прогресс не сохранится.
_raw_cookie_domain = os.getenv("COOKIE_DOMAIN", "").strip()
COOKIE_DOMAIN = _raw_cookie_domain if _raw_cookie_domain else None

# HTTPS в проде: true (по умолчанию). Локальный HTTP: COOKIE_SECURE=false
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() in ("1", "true", "yes")

# none — для кросс-доменных запросов с credentials (фронт на tylmus.ru, API на другом хосте).
# lax — если фронт и API на одном сайте и не нужен cross-site cookie.
_raw_samesite = os.getenv("COOKIE_SAMESITE", "none").strip().lower()
if _raw_samesite not in ("none", "lax", "strict"):
    _raw_samesite = "none"
# SameSite=None требует Secure; иначе браузер игнорирует cookie.
if not COOKIE_SECURE and _raw_samesite == "none":
    COOKIE_SAMESITE = "lax"
else:
    COOKIE_SAMESITE = _raw_samesite
