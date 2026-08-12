"""پایگاه‌داده JSON با نوشتن اتمیک و قفل — جایگزین ایمن نسخه قبلی.

مشکل نسخه قبلی: هر `set()` کل فایل را می‌خواند و دوباره می‌نوشت، بدون قفل و بدون
نوشتن اتمیک. در نتیجه اگر دو هندلر (یا ترد تایمر شارژ) هم‌زمان مقدار را عوض
می‌کردند، یکی از تغییرات گم می‌شد و اگر برنامه در میانه نوشتن کرش می‌کرد فایل
خراب می‌ماند.

اینجا:
  • همه عملیات با یک RLock سریالایز می‌شوند.
  • نوشتن اتمیک است (فایل موقت + os.replace) پس فایل نیمه‌نوشته باقی نمی‌ماند.
  • قبل از خرابکاری، از فایل سالم قبلی نسخه پشتیبان .bak گرفته می‌شود.
  • `atomic()` امکان خواندن-تغییر-نوشتن ایمن (مثل کم/زیاد کردن سکه) را می‌دهد.
"""

import json
import os
import shutil
import tempfile
import threading
from contextlib import contextmanager

DEFAULT_CATEGORIES = (
    "users",
    "processes",
    "temp_data",
    "credits",
    "timers",
    "verifications",
    "payments",
    "group_bets",
    "settings",
)


class JSONDatabase:
    def __init__(self, filename="database.json", defaults=None):
        self.filename = filename
        self._lock = threading.RLock()
        self._defaults = dict(defaults or {})
        self.data = self._load()

    # ── بارگذاری / ذخیره ─────────────────────────────────────────────────────
    def _empty(self):
        data = {category: {} for category in DEFAULT_CATEGORIES}
        data["settings"] = dict(self._defaults)
        return data

    def _load(self):
        for path in (self.filename, f"{self.filename}.bak"):
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                if not isinstance(data, dict):
                    raise ValueError("ساختار پایگاه‌داده باید دیکشنری باشد")
                if path.endswith(".bak"):
                    print(f"⚠️ {self.filename} خراب بود؛ از نسخه پشتیبان بازیابی شد.")
                for category in DEFAULT_CATEGORIES:
                    data.setdefault(category, {})
                for key, value in self._defaults.items():
                    data["settings"].setdefault(key, value)
                return data
            except (json.JSONDecodeError, ValueError, OSError) as error:
                print(f"❌ خطا در خواندن {path}: {error}")

        data = self._empty()
        self._write(data)
        return data

    def _write(self, data):
        """نوشتن اتمیک: ابتدا در فایل موقت، سپس جایگزینی."""
        directory = os.path.dirname(os.path.abspath(self.filename)) or "."
        handle = None
        try:
            fd, temp_path = tempfile.mkstemp(dir=directory, prefix=".db-", suffix=".tmp")
            handle = os.fdopen(fd, "w", encoding="utf-8")
            json.dump(data, handle, indent=4, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
            handle.close()
            handle = None

            if os.path.exists(self.filename):
                try:
                    shutil.copy2(self.filename, f"{self.filename}.bak")
                except OSError:
                    pass

            os.replace(temp_path, self.filename)
            return True
        except OSError as error:
            print(f"❌ خطا در ذخیره پایگاه‌داده: {error}")
            if handle is not None:
                handle.close()
            return False

    def save_data(self, data=None):
        with self._lock:
            if data is not None:
                self.data = data
            return self._write(self.data)

    # ── خواندن / نوشتن مقادیر ────────────────────────────────────────────────
    def get(self, category, key, default=None):
        with self._lock:
            return self.data.get(category, {}).get(str(key), default)

    def set(self, category, key, value):
        with self._lock:
            self.data.setdefault(category, {})[str(key)] = value
            return self._write(self.data)

    def delete(self, category, key):
        with self._lock:
            if category in self.data and str(key) in self.data[category]:
                del self.data[category][str(key)]
                return self._write(self.data)
            return False

    def get_all(self, category):
        with self._lock:
            return dict(self.data.get(category, {}))

    @contextmanager
    def atomic(self):
        """خواندن-تغییر-نوشتن ایمن.

        استفاده:
            with db.atomic() as data:
                data["credits"]["123"] = data["credits"].get("123", 0) - 10

        تا پایان بلوک هیچ نویسنده دیگری اجازه تغییر ندارد و در انتها یک بار
        به‌صورت اتمیک ذخیره می‌شود.
        """
        with self._lock:
            for category in DEFAULT_CATEGORIES:
                self.data.setdefault(category, {})
            yield self.data
            self._write(self.data)

    # ── کمکی‌های سکه ─────────────────────────────────────────────────────────
    def get_credits(self, user_id):
        with self._lock:
            try:
                return int(self.data.get("credits", {}).get(str(user_id), 0) or 0)
            except (TypeError, ValueError):
                return 0

    def add_credits(self, user_id, amount):
        """افزودن (یا کم کردن با مقدار منفی) سکه به‌صورت اتمیک. موجودی نهایی برمی‌گردد."""
        with self.atomic() as data:
            current = data.setdefault("credits", {})
            try:
                balance = int(current.get(str(user_id), 0) or 0)
            except (TypeError, ValueError):
                balance = 0
            balance = max(0, balance + int(amount))
            current[str(user_id)] = balance
            return balance

    def spend_credits(self, user_id, amount):
        """کم کردن سکه فقط در صورت کافی بودن موجودی.

        برمی‌گرداند: (موفق؟, موجودی نهایی). این کار چک-و-کم کردن را در یک قفل
        انجام می‌دهد تا با دوبار کلیک سریع، موجودی منفی نشود.
        """
        amount = int(amount)
        with self.atomic() as data:
            current = data.setdefault("credits", {})
            try:
                balance = int(current.get(str(user_id), 0) or 0)
            except (TypeError, ValueError):
                balance = 0
            if balance < amount:
                return False, balance
            balance -= amount
            current[str(user_id)] = balance
            return True, balance

    # ── فیلترهای آماده ───────────────────────────────────────────────────────
    def _filter(self, category, predicate):
        with self._lock:
            items = self.data.get(category, {})
            return {key: value for key, value in items.items() if predicate(value)}

    def get_pending_verifications(self):
        return self._filter("verifications", lambda v: isinstance(v, dict) and v.get("status") == "pending")

    def get_pending_payments(self):
        return self._filter("payments", lambda v: isinstance(v, dict) and v.get("status") == "pending")

    def get_verified_users(self):
        return self._filter("users", lambda v: isinstance(v, dict) and v.get("verified"))

    def get_rejected_users(self):
        return self._filter("users", lambda v: isinstance(v, dict) and v.get("rejected"))

    # ── تنظیمات ──────────────────────────────────────────────────────────────
    def get_setting(self, key, default=None):
        with self._lock:
            return self.data.get("settings", {}).get(key, default)

    def set_setting(self, key, value):
        with self._lock:
            self.data.setdefault("settings", {})[key] = value
            return self._write(self.data)

    def set_transfer_status(self, enabled):
        return self.set_setting("transfer_enabled", bool(enabled))

    def get_transfer_status(self):
        return self.get_setting("transfer_enabled", True)

    def get_welcome_photo(self):
        return self.get_setting("welcome_photo_id", None)

    def set_welcome_photo(self, photo_id):
        return self.set_setting("welcome_photo_id", photo_id)

    def delete_welcome_photo(self):
        with self._lock:
            self.data.get("settings", {}).pop("welcome_photo_id", None)
            return self._write(self.data)


def read_only_snapshot(filename="database.json"):
    """خواندن پایگاه‌داده بدون گرفتن مالکیت آن (برای ربات هلپر).

    اگر فایل اصلی در حال نوشتن باشد و JSON ناقص خوانده شود، نسخه .bak امتحان
    می‌شود تا پنل هلپر با خطا مواجه نشود.
    """
    for path in (filename, f"{filename}.bak"):
        try:
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            continue
    return {}
