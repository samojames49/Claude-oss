"""آمار حضور اعضا در ویس‌چت («آمار کال»).

زمان حضور با نمونه‌برداری دوره‌ای از لیست شرکت‌کنندگان ویس‌چت جمع می‌شود؛ پس عددها
با دقت بازهٔ نمونه‌برداری (`CALL_STATS_INTERVAL_SECONDS`) تقریبی‌اند و نه ثانیه‌به‌ثانیه.
"""

from __future__ import annotations

from datetime import date, timedelta

from .. import config
from ..utils.formatters import seconds_to_clock
from .db import db

# شمارهٔ روز هفته در پایتون: دوشنبه ۰ … یکشنبه ۶
WEEKDAYS: dict[str, int] = {
    "شنبه": 5,
    "saturday": 5,
    "sat": 5,
    "یکشنبه": 6,
    "يكشنبه": 6,
    "sunday": 6,
    "sun": 6,
    "دوشنبه": 0,
    "monday": 0,
    "mon": 0,
    "سه‌شنبه": 1,
    "سه شنبه": 1,
    "سهشنبه": 1,
    "tuesday": 1,
    "tue": 1,
    "چهارشنبه": 2,
    "wednesday": 2,
    "wed": 2,
    "پنج‌شنبه": 3,
    "پنج شنبه": 3,
    "پنجشنبه": 3,
    "thursday": 3,
    "thu": 3,
    "جمعه": 4,
    "friday": 4,
    "fri": 4,
}

WEEKDAY_NAMES_FA = {
    5: "شنبه",
    6: "یکشنبه",
    0: "دوشنبه",
    1: "سه‌شنبه",
    2: "چهارشنبه",
    3: "پنج‌شنبه",
    4: "جمعه",
}


def today_key() -> str:
    return date.today().isoformat()


def last_days(count: int) -> list[str]:
    """کلید روزهای امروز و ‎count-1 روز قبل."""
    count = max(1, min(count, config.CALL_STATS_KEEP_DAYS))
    today = date.today()
    return [(today - timedelta(days=offset)).isoformat() for offset in range(count)]


def weekday_key(name: str) -> str | None:
    """آخرین تاریخی که در آن روزِ هفتهٔ داده‌شده بوده (شامل امروز)."""
    weekday = WEEKDAYS.get(name.strip().lower())
    if weekday is None:
        return None
    today = date.today()
    for offset in range(7):
        day = today - timedelta(days=offset)
        if day.weekday() == weekday:
            return day.isoformat()
    return None


def weekday_label(day_key: str) -> str:
    try:
        parsed = date.fromisoformat(day_key)
    except ValueError:
        return day_key
    return f"{WEEKDAY_NAMES_FA.get(parsed.weekday(), '')} {day_key}".strip()


def stats_enabled(chat_id: int) -> bool:
    return bool(db.chat_setting(chat_id, "call_stats", config.CALL_STATS_ENABLED))


def accumulate(chat_id: int, user_ids: list[int], seconds: int, names: dict[int, str]) -> None:
    """افزودن زمان حضور به آمار امروز."""
    if seconds <= 0:
        return
    day = today_key()
    for user_id in user_ids:
        db.add_call_time(chat_id, user_id, seconds, name=names.get(user_id, ""), day=day)
    db.prune_call_stats(chat_id, config.CALL_STATS_KEEP_DAYS)


def leaderboard(chat_id: int, days: list[str], limit: int | None = None) -> list[tuple[int, int]]:
    limit = limit or config.CALL_STATS_TOP
    return db.call_totals(chat_id, days)[:limit]


def user_rank(chat_id: int, user_id: int, days: list[str]) -> tuple[int, int, int]:
    """(رتبه، ثانیه‌های حضور، تعداد کل افراد)؛ رتبهٔ صفر یعنی حضوری ثبت نشده."""
    totals = db.call_totals(chat_id, days)
    for index, (candidate, seconds) in enumerate(totals, start=1):
        if candidate == user_id:
            return index, seconds, len(totals)
    return 0, 0, len(totals)


def render(chat_id: int, s, days: list[str], *, title: str) -> str:
    """متن آمادهٔ نمایش آمار کال."""
    rows = leaderboard(chat_id, days)
    if not rows:
        return s("callstats_empty")
    text = s("callstats_header", title=title, count=len(rows))
    for index, (user_id, seconds) in enumerate(rows, start=1):
        name = db.call_user_name(chat_id, user_id) or str(user_id)
        text += s(
            "callstats_item",
            index=index,
            user=f"[{name}](tg://user?id={user_id})",
            duration=seconds_to_clock(seconds),
        )
    return text
