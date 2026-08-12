"""تنظیمات مرکزی — همه مقادیر از متغیرهای محیطی (فایل .env) خوانده می‌شوند.

هیچ توکن یا کلیدی نباید داخل کد نوشته شود. برای شروع، فایل `.env.example` را به
`.env` کپی کنید و مقادیر خودتان را جایگذاری کنید.
"""

import os
import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv نصب نیست؛ فقط از محیط سیستم می‌خوانیم
    pass


class ConfigError(RuntimeError):
    pass


def _str(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and not value:
        raise ConfigError(
            f"متغیر محیطی {name} تنظیم نشده است. فایل .env.example را به .env کپی و مقادیر را پر کنید."
        )
    return value


def _int(name, default=None, required=False):
    raw = os.getenv(name)
    if raw is None or raw == "":
        if required and default is None:
            raise ConfigError(
                f"متغیر محیطی {name} تنظیم نشده است. فایل .env.example را به .env کپی و مقادیر را پر کنید."
            )
        return default
    try:
        return int(raw)
    except ValueError:
        raise ConfigError(f"متغیر محیطی {name} باید یک عدد باشد (مقدار فعلی: {raw!r}).")


def _float(name, default=None):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        raise ConfigError(f"متغیر محیطی {name} باید یک عدد باشد (مقدار فعلی: {raw!r}).")


def _bool(name, default=False):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on", "بله")


def _list(name, default=None):
    raw = os.getenv(name)
    if not raw:
        return list(default or [])
    return [item.strip() for item in raw.split(",") if item.strip()]


# ── حساب تلگرام / API ─────────────────────────────────────────────────────────
API_ID = _int("API_ID")
API_HASH = _str("API_HASH")

# ── ربات سلف‌ساز (bot.py) ─────────────────────────────────────────────────────
BOT_TOKEN = _str("BOT_TOKEN")
ADMIN_ID = _int("ADMIN_ID")

# ── ربات هلپر (helper.py) ─────────────────────────────────────────────────────
HELPER_BOT_TOKEN = _str("HELPER_BOT_TOKEN")
HELPER_BOT_USERNAME = _str("HELPER_BOT_USERNAME", "")  # بدون @
MANAGER_BOT_LINK = _str("MANAGER_BOT_LINK", "https://t.me/")
PANEL_IMAGE = _str("PANEL_IMAGE", "")

# ── عضویت اجباری ──────────────────────────────────────────────────────────────
FORCE_CHANNELS = _list("FORCE_CHANNELS", [])

# ── اقتصاد سکه ────────────────────────────────────────────────────────────────
COIN_RATE = _int("COIN_RATE", 1440)  # تعداد سکه به ازای COIN_PRICE_TOMAN
COIN_PRICE_TOMAN = _int("COIN_PRICE_TOMAN", 50000)
TOMAN_PER_COIN = COIN_PRICE_TOMAN / COIN_RATE if COIN_RATE else 0
TAX_PERCENT = _int("TAX_PERCENT", 10)
TAX_MIN_AMOUNT = _int("TAX_MIN_AMOUNT", 2)
FREE_STARTING_CREDITS = _int("FREE_STARTING_CREDITS", 5)

# ── پرداخت کارت به کارت (روش دستی) ────────────────────────────────────────────
CARD_NUMBER = _str("CARD_NUMBER", "")
CARD_OWNER = _str("CARD_OWNER", "")
CARD_BANK = _str("CARD_BANK", "")

card_info = {
    "card_number": CARD_NUMBER,
    "card_owner": CARD_OWNER,
    "bank_name": CARD_BANK,
}

# ── درگاه پرداخت آنی ریالی ────────────────────────────────────────────────────
# با PAYMENT_GATEWAY_ENABLED=true فعال می‌شود. در غیر این صورت روش کارت‌به‌کارت
# استفاده می‌شود.
PAYMENT_GATEWAY_ENABLED = _bool("PAYMENT_GATEWAY_ENABLED", False)
PAYMENT_GATEWAY_PROVIDER = _str("PAYMENT_GATEWAY_PROVIDER", "zarinpal")
PAYMENT_GATEWAY_MERCHANT_ID = _str("PAYMENT_GATEWAY_MERCHANT_ID", "")
PAYMENT_GATEWAY_CALLBACK_URL = _str("PAYMENT_GATEWAY_CALLBACK_URL", "")
PAYMENT_GATEWAY_SANDBOX = _bool("PAYMENT_GATEWAY_SANDBOX", False)

# ── سرویس‌های خارجی مورد استفاده سلف ──────────────────────────────────────────
PRICE_API_KEY = _str("PRICE_API_KEY", "")
INSTAGRAM_API_KEY = _str("INSTAGRAM_API_KEY", "")

# ── نگهداری و سلامت سرویس ─────────────────────────────────────────────────────
HEALTH_REPORT_ENABLED = _bool("HEALTH_REPORT_ENABLED", True)
HEALTH_REPORT_INTERVAL = _int("HEALTH_REPORT_INTERVAL", 3600)  # ثانیه
AUTO_RESTART_ENABLED = _bool("AUTO_RESTART_ENABLED", True)

# ── مسیر فایل‌ها ──────────────────────────────────────────────────────────────
SESSIONS_DIR = _str("SESSIONS_DIR", "sessions")
DATABASE_FILE = _str("DATABASE_FILE", "database.json")
SELF_SCRIPT = _str("SELF_SCRIPT", "self.py")


def require(*names):
    """اطمینان از وجود متغیرهای حیاتی؛ در صورت نبود، خطای خوانا چاپ و خروج."""
    missing = [name for name in names if not globals().get(name)]
    if missing:
        print("❌ تنظیمات ناقص است. متغیرهای زیر در فایل .env مقدار ندارند:")
        for name in missing:
            print(f"   • {name}")
        print("\n💡 راهنما: cp .env.example .env  سپس مقادیر را پر کنید.")
        sys.exit(1)
