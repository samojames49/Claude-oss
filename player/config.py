"""تنظیمات ربات پلیر — همهٔ مقادیر از متغیرهای محیطی (`player/.env`) خوانده می‌شوند."""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv اختیاری است
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent

if load_dotenv is not None:
    for candidate in (BASE_DIR / ".env", BASE_DIR.parent / ".env"):
        if candidate.exists():
            load_dotenv(candidate)
            break


class ConfigError(RuntimeError):
    """تنظیمات ناقص یا نامعتبر."""


def _str(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _int(name: str, default: int | None = None) -> int | None:
    raw = _str(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ConfigError(f"متغیر {name} باید عدد باشد (مقدار فعلی: {raw!r}).")


def _bool(name: str, default: bool = False) -> bool:
    raw = _str(name)
    if raw is None:
        return default
    return raw.lower() in ("1", "true", "yes", "on", "بله", "روشن")


def _int_list(name: str) -> list[int]:
    raw = _str(name, "") or ""
    out: list[int] = []
    for part in raw.replace(",", " ").split():
        try:
            out.append(int(part))
        except ValueError:
            continue
    return out


# ── حساب تلگرام ───────────────────────────────────────────────────────────────
API_ID = _int("API_ID", 0)
API_HASH = _str("API_HASH", "")
BOT_TOKEN = _str("BOT_TOKEN", "")

# نشست اکانت‌های «اسیستنت» (حساب کاربری که داخل ویس‌چت می‌شود و صدا پخش می‌کند).
# با تعریف چند نشست، بار بین آن‌ها تقسیم می‌شود (Multi Assistant).
STRING_SESSIONS: list[str] = []
for _index in range(1, 11):
    _name = "STRING_SESSION" if _index == 1 else f"STRING_SESSION{_index}"
    _value = _str(_name)
    if _value:
        STRING_SESSIONS.append(_value)

# ── مالکیت و مدیریت ───────────────────────────────────────────────────────────
OWNER_ID = _int("OWNER_ID", 0)
SUDO_USERS = _int_list("SUDO_USERS")
LOGGER_ID = _int("LOGGER_ID", 0)  # آیدی گروه لاگ (عدد منفی)
LOG_LEVEL = (_str("LOG_LEVEL", "INFO") or "INFO").upper()

# ── برندینگ ───────────────────────────────────────────────────────────────────
BOT_NAME = _str("BOT_NAME", "Player")
OWNER_USERNAME = _str("OWNER_USERNAME", "")
SUPPORT_CHAT = _str("SUPPORT_CHAT", "")
SUPPORT_CHANNEL = _str("SUPPORT_CHANNEL", "")
START_IMAGE = _str("START_IMAGE", "")
PLAYER_IMAGE = _str("PLAYER_IMAGE", "")
DEFAULT_LANGUAGE = (_str("DEFAULT_LANGUAGE", "fa") or "fa").lower()

# ── محدودیت‌ها و رفتار پخش ────────────────────────────────────────────────────
DURATION_LIMIT_MINUTES = _int("DURATION_LIMIT_MINUTES", 180) or 180
QUEUE_LIMIT = _int("QUEUE_LIMIT", 50) or 50
SEARCH_RESULTS_LIMIT = _int("SEARCH_RESULTS_LIMIT", 6) or 6
MAX_TELEGRAM_FILE_MB = _int("MAX_TELEGRAM_FILE_MB", 300) or 300
VIDEO_CALL_LIMIT = _int("VIDEO_CALL_LIMIT", 3) or 3  # سقف پخش ویدیویی هم‌زمان
PLAY_MODE = (_str("PLAY_MODE", "everyone") or "everyone").lower()  # everyone|admins
STREAM_MODE = (_str("STREAM_MODE", "direct") or "direct").lower()  # direct|download
AUDIO_QUALITY = (_str("AUDIO_QUALITY", "high") or "high").lower()  # studio|high|medium|low
VIDEO_QUALITY = (_str("VIDEO_QUALITY", "hd") or "hd").lower()  # uhd|qhd|fhd|hd|sd
AUTO_LEAVE_ASSISTANT = _bool("AUTO_LEAVE_ASSISTANT", True)
INACTIVE_TIMEOUT_SECONDS = _int("INACTIVE_TIMEOUT_SECONDS", 600) or 600
EMPTY_CALL_TIMEOUT_SECONDS = _int("EMPTY_CALL_TIMEOUT_SECONDS", 120) or 120
WATCHER_INTERVAL_SECONDS = _int("WATCHER_INTERVAL_SECONDS", 30) or 30

# ── آمار ویس‌چت (آمار کال) ────────────────────────────────────────────────────
CALL_STATS_ENABLED = _bool("CALL_STATS_ENABLED", True)
CALL_STATS_INTERVAL_SECONDS = _int("CALL_STATS_INTERVAL_SECONDS", 60) or 60
CALL_STATS_KEEP_DAYS = _int("CALL_STATS_KEEP_DAYS", 40) or 40
CALL_STATS_TOP = _int("CALL_STATS_TOP", 20) or 20

# ── امنیت کال ─────────────────────────────────────────────────────────────────
CALL_SECURITY_ENABLED = _bool("CALL_SECURITY_ENABLED", False)
CALL_SECURITY_MIN_AGE_DAYS = _int("CALL_SECURITY_MIN_AGE_DAYS", 7) or 7
CALL_SECURITY_MAX_JOINS = _int("CALL_SECURITY_MAX_JOINS", 5) or 5

# ── پخش زنده تلویزیون/ماهواره ────────────────────────────────────────────────
LIVE_CHANNELS_FILE = _str("LIVE_CHANNELS_FILE", "")  # پیش‌فرض: player/data/live_channels.json

# ── زیرنویس ───────────────────────────────────────────────────────────────────
SUBTITLE_ENABLED = _bool("SUBTITLE_ENABLED", True)
SUBTITLE_FONT_SIZE = _int("SUBTITLE_FONT_SIZE", 20) or 20
SUBTITLE_MAX_MB = _int("SUBTITLE_MAX_MB", 5) or 5

# ── پیام‌ها ───────────────────────────────────────────────────────────────────
AUTO_CLEAR_SECONDS = _int("AUTO_CLEAR_SECONDS", 10) or 10  # پاک‌سازی خودکار پیام پایان پخش
INVITE_CALL_LIMIT = _int("INVITE_CALL_LIMIT", 200) or 200

# ── دسترسی ────────────────────────────────────────────────────────────────────
PRIVATE_MODE = _bool("PRIVATE_MODE", False)  # فقط گروه‌های تاییدشده
FORCE_SUB_CHANNEL = _str("FORCE_SUB_CHANNEL", "")  # یوزرنیم بدون @

# ── منابع خارجی ───────────────────────────────────────────────────────────────
COOKIES_FILE = _str("COOKIES_FILE", "")  # کوکی یوتیوب برای رفع محدودیت سن/ربات
YTDLP_PROXY = _str("YTDLP_PROXY", "")
LYRICS_ENABLED = _bool("LYRICS_ENABLED", True)

# ── مسیرها ────────────────────────────────────────────────────────────────────
DOWNLOADS_DIR = Path(_str("DOWNLOADS_DIR", str(BASE_DIR / "downloads")))
CACHE_DIR = Path(_str("CACHE_DIR", str(BASE_DIR / "cache")))
DB_FILE = Path(_str("DB_FILE", str(BASE_DIR / "player_db.json")))
SESSION_DIR = Path(_str("SESSION_DIR", str(BASE_DIR / "sessions")))
DATA_DIR = BASE_DIR / "data"


def live_channels_file() -> Path:
    """مسیر فایل شبکه‌های پخش زنده (قابل جایگزینی با LIVE_CHANNELS_FILE)."""
    if LIVE_CHANNELS_FILE:
        return Path(LIVE_CHANNELS_FILE)
    return DATA_DIR / "live_channels.json"

AUDIO_QUALITY_MAP = {"studio": "STUDIO", "high": "HIGH", "medium": "MEDIUM", "low": "LOW"}
VIDEO_QUALITY_MAP = {
    "uhd": "UHD_4K",
    "4k": "UHD_4K",
    "qhd": "QHD_2K",
    "2k": "QHD_2K",
    "fhd": "FHD_1080p",
    "1080": "FHD_1080p",
    "hd": "HD_720p",
    "720": "HD_720p",
    "sd": "SD_480p",
    "480": "SD_480p",
}

REQUIRED = ("API_ID", "API_HASH", "BOT_TOKEN")


def sudoers() -> set[int]:
    """مجموعهٔ ادمین‌های سراسری تعریف‌شده در تنظیمات."""
    ids = set(SUDO_USERS)
    if OWNER_ID:
        ids.add(OWNER_ID)
    return ids


def validate() -> None:
    """بررسی تنظیمات حیاتی؛ در صورت نقص، پیام خوانا چاپ و خروج."""
    missing = [name for name in REQUIRED if not globals().get(name)]
    if not STRING_SESSIONS:
        missing.append("STRING_SESSION")
    if missing:
        print("❌ تنظیمات ناقص است. متغیرهای زیر مقدار ندارند:")
        for name in missing:
            print(f"   • {name}")
        print("\n💡 راهنما: cp player/.env.example player/.env سپس مقادیر را پر کنید.")
        sys.exit(1)

    if PLAY_MODE not in ("everyone", "admins"):
        raise ConfigError("PLAY_MODE باید everyone یا admins باشد.")
    if STREAM_MODE not in ("direct", "download"):
        raise ConfigError("STREAM_MODE باید direct یا download باشد.")
    if AUDIO_QUALITY not in AUDIO_QUALITY_MAP:
        raise ConfigError("AUDIO_QUALITY باید یکی از studio/high/medium/low باشد.")
    if VIDEO_QUALITY not in VIDEO_QUALITY_MAP:
        raise ConfigError("VIDEO_QUALITY باید یکی از uhd/qhd/fhd/hd/sd باشد.")

    for directory in (DOWNLOADS_DIR, CACHE_DIR, SESSION_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
