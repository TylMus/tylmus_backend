from datetime import datetime, timezone, timedelta

YAKT_TIMEZONE = timezone(timedelta(hours=9))


def get_yakt_time():
    return datetime.now(YAKT_TIMEZONE)


def get_yakt_date_str():
    return get_yakt_time().date().isoformat()


def format_yakt_time():
    return get_yakt_time().strftime("%Y-%m-%d %H:%M:%S %Z")
