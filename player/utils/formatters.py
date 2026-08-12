"""توابع کمکی قالب‌بندی زمان، حجم و نوار پیشرفت."""

from __future__ import annotations

import re

_TIME_UNITS = ("s", "m", "h", "d")


def seconds_to_time(seconds: int | float | None) -> str:
    """۱۲۵ ثانیه → «۲:۰۵» (به ارقام لاتین، مثل پلیرهای رایج)."""
    try:
        total = int(seconds or 0)
    except (TypeError, ValueError):
        return "0:00"
    if total < 0:
        total = 0
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def seconds_to_clock(seconds: int | float | None) -> str:
    """۳۶۶۰ ثانیه → «01:01:00» (همیشه با ساعت، برای جدول آمار کال)."""
    try:
        total = max(0, int(seconds or 0))
    except (TypeError, ValueError):
        total = 0
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def time_to_seconds(value: str | int | float | None) -> int:
    """«۲:۰۵» یا «1:02:03» یا «90» → تعداد ثانیه."""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if not text:
        return 0
    text = _to_latin_digits(text)
    if ":" in text:
        total = 0
        for part in text.split(":"):
            digits = re.sub(r"\D", "", part) or "0"
            total = total * 60 + int(digits)
        return total
    match = re.match(r"^(\d+)\s*([smhd])?$", text, re.IGNORECASE)
    if match:
        amount = int(match.group(1))
        unit = (match.group(2) or "s").lower()
        factor = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
        return amount * factor
    digits = re.sub(r"\D", "", text)
    return int(digits) if digits else 0


def _to_latin_digits(text: str) -> str:
    persian = "۰۱۲۳۴۵۶۷۸۹"
    arabic = "٠١٢٣٤٥٦٧٨٩"
    table = {ord(char): str(index) for index, char in enumerate(persian)}
    table.update({ord(char): str(index) for index, char in enumerate(arabic)})
    return text.translate(table)


def to_latin_digits(text: str) -> str:
    return _to_latin_digits(text)


def human_bytes(size: int | float | None) -> str:
    try:
        value = float(size or 0)
    except (TypeError, ValueError):
        return "0B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(value)}{unit}"
            return f"{value:.1f}{unit}"
        value /= 1024
    return f"{value:.1f}TB"


def progress_bar(played: int, total: int, length: int = 12) -> str:
    """نوار پیشرفت متنی برای پیام «در حال پخش»."""
    if not total or total <= 0:
        return "🔴 " + "─" * length
    ratio = min(max(played / total, 0.0), 1.0)
    filled = int(ratio * length)
    filled = min(filled, length - 1)
    return "▬" * filled + "🔘" + "▬" * (length - filled - 1)


def human_timedelta(seconds: int | float | None) -> str:
    """۹۰۰۰۰ ثانیه → «1d 1h 0m»."""
    try:
        total = int(seconds or 0)
    except (TypeError, ValueError):
        return "0s"
    if total <= 0:
        return "0s"
    days, remainder = divmod(total, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts[-3:] if len(parts) > 3 else parts)


def shorten(text: str | None, limit: int = 45) -> str:
    value = (text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"
