"""Настройки из окружения (cookie domain, и т.д.)."""
import os

# Для продакшена: COOKIE_DOMAIN=.tylmus.ru (фронт и API на поддоменах *.tylmus.ru).
# Для локальных тестов / localhost: не задавать или COOKIE_DOMAIN= — cookie без Domain.
_raw_cookie_domain = os.getenv("COOKIE_DOMAIN", ".tylmus.ru").strip()
COOKIE_DOMAIN = _raw_cookie_domain if _raw_cookie_domain else None
