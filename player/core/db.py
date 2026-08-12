"""پایگاه‌دادهٔ سبک JSON با نوشتن اتمیک و قفل asyncio.

برای ربات پلیر به دیتابیس سنگین نیازی نیست؛ داده‌ها کم‌حجم‌اند (گروه‌ها، کاربران،
تنظیمات، آمار) و این ماژول بدون هیچ سرویس بیرونی کار می‌کند.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from time import time
from typing import Any

from .. import config

_DEFAULT: dict[str, Any] = {
    "chats": {},
    "users": {},
    "sudoers": [],
    "blocked_users": [],
    "blocked_chats": [],
    "settings": {"maintenance": False},
    "stats": {"plays": 0, "tracks": {}},
}

_CHAT_DEFAULT: dict[str, Any] = {
    "title": "",
    "language": None,
    "play_mode": None,  # None => از تنظیمات سراسری
    "auto_leave": None,
    "now_playing_message": True,
    "auth_users": {},
    "plays": 0,
    "approved": False,
    "added_at": 0,
}


class Database:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path or config.DB_FILE)
        self._lock = asyncio.Lock()
        self._data: dict[str, Any] = json.loads(json.dumps(_DEFAULT))
        self._loaded = False
        self._dirty = False

    # ── چرخهٔ حیات ────────────────────────────────────────────────────────────
    def load(self) -> None:
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                if isinstance(data, dict):
                    for key, value in _DEFAULT.items():
                        data.setdefault(key, json.loads(json.dumps(value)))
                    self._data = data
            except (json.JSONDecodeError, OSError):
                backup = self.path.with_suffix(".corrupt.json")
                try:
                    self.path.replace(backup)
                except OSError:
                    pass
        self._loaded = True

    async def start(self) -> None:
        if not self._loaded:
            self.load()

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=str(self.path.parent),
            prefix=".player_db_",
            suffix=".tmp",
            delete=False,
        )
        try:
            json.dump(self._data, handle, ensure_ascii=False, indent=1)
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            handle.close()
        os.replace(handle.name, self.path)
        self._dirty = False

    async def save(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._flush)

    def mark_dirty(self) -> None:
        self._dirty = True

    async def autosave_loop(self, interval: int = 30) -> None:
        """هر چند ثانیه اگر تغییری بود، روی دیسک می‌نویسد."""
        while True:
            await asyncio.sleep(interval)
            if self._dirty:
                try:
                    await self.save()
                except OSError:
                    pass

    # ── گروه‌ها ───────────────────────────────────────────────────────────────
    def chat(self, chat_id: int) -> dict[str, Any]:
        chats = self._data.setdefault("chats", {})
        entry = chats.get(str(chat_id))
        if entry is None:
            entry = json.loads(json.dumps(_CHAT_DEFAULT))
            entry["added_at"] = int(time())
            chats[str(chat_id)] = entry
            self.mark_dirty()
        else:
            for key, value in _CHAT_DEFAULT.items():
                entry.setdefault(key, json.loads(json.dumps(value)))
        return entry

    def is_served_chat(self, chat_id: int) -> bool:
        return str(chat_id) in self._data.get("chats", {})

    def add_chat(self, chat_id: int, title: str = "") -> bool:
        is_new = not self.is_served_chat(chat_id)
        entry = self.chat(chat_id)
        if title and entry.get("title") != title:
            entry["title"] = title
            self.mark_dirty()
        return is_new

    def remove_chat(self, chat_id: int) -> None:
        if self._data.get("chats", {}).pop(str(chat_id), None) is not None:
            self.mark_dirty()

    def served_chats(self) -> list[int]:
        out = []
        for key in self._data.get("chats", {}):
            try:
                out.append(int(key))
            except ValueError:
                continue
        return out

    def chat_setting(self, chat_id: int, key: str, default: Any = None) -> Any:
        value = self.chat(chat_id).get(key)
        return default if value is None else value

    def set_chat_setting(self, chat_id: int, key: str, value: Any) -> None:
        self.chat(chat_id)[key] = value
        self.mark_dirty()

    # ── کاربران ───────────────────────────────────────────────────────────────
    def add_user(self, user_id: int, name: str = "") -> bool:
        users = self._data.setdefault("users", {})
        key = str(user_id)
        if key in users:
            if name and users[key].get("name") != name:
                users[key]["name"] = name
                self.mark_dirty()
            return False
        users[key] = {"name": name, "joined": int(time())}
        self.mark_dirty()
        return True

    def served_users(self) -> list[int]:
        out = []
        for key in self._data.get("users", {}):
            try:
                out.append(int(key))
            except ValueError:
                continue
        return out

    # ── سودو ──────────────────────────────────────────────────────────────────
    def sudoers(self) -> set[int]:
        return set(self._data.get("sudoers", [])) | config.sudoers()

    def is_sudo(self, user_id: int) -> bool:
        return user_id in self.sudoers()

    def add_sudo(self, user_id: int) -> bool:
        stored = self._data.setdefault("sudoers", [])
        if user_id in stored:
            return False
        stored.append(user_id)
        self.mark_dirty()
        return True

    def remove_sudo(self, user_id: int) -> bool:
        stored = self._data.setdefault("sudoers", [])
        if user_id not in stored:
            return False
        stored.remove(user_id)
        self.mark_dirty()
        return True

    # ── مسدودسازی ─────────────────────────────────────────────────────────────
    def is_blocked_user(self, user_id: int) -> bool:
        return user_id in self._data.get("blocked_users", [])

    def block_user(self, user_id: int) -> bool:
        stored = self._data.setdefault("blocked_users", [])
        if user_id in stored:
            return False
        stored.append(user_id)
        self.mark_dirty()
        return True

    def unblock_user(self, user_id: int) -> bool:
        stored = self._data.setdefault("blocked_users", [])
        if user_id not in stored:
            return False
        stored.remove(user_id)
        self.mark_dirty()
        return True

    def is_blocked_chat(self, chat_id: int) -> bool:
        return chat_id in self._data.get("blocked_chats", [])

    def block_chat(self, chat_id: int) -> bool:
        stored = self._data.setdefault("blocked_chats", [])
        if chat_id in stored:
            return False
        stored.append(chat_id)
        self.mark_dirty()
        return True

    def unblock_chat(self, chat_id: int) -> bool:
        stored = self._data.setdefault("blocked_chats", [])
        if chat_id not in stored:
            return False
        stored.remove(chat_id)
        self.mark_dirty()
        return True

    # ── کاربران مجاز هر گروه ─────────────────────────────────────────────────
    def auth_users(self, chat_id: int) -> dict[str, Any]:
        return self.chat(chat_id).setdefault("auth_users", {})

    def is_auth_user(self, chat_id: int, user_id: int) -> bool:
        return str(user_id) in self.auth_users(chat_id)

    def add_auth_user(self, chat_id: int, user_id: int, name: str = "") -> bool:
        users = self.auth_users(chat_id)
        if str(user_id) in users:
            return False
        users[str(user_id)] = {"name": name, "added_at": int(time())}
        self.mark_dirty()
        return True

    def remove_auth_user(self, chat_id: int, user_id: int) -> bool:
        users = self.auth_users(chat_id)
        if users.pop(str(user_id), None) is None:
            return False
        self.mark_dirty()
        return True

    # ── تنظیمات سراسری و آمار ────────────────────────────────────────────────
    def setting(self, key: str, default: Any = None) -> Any:
        return self._data.setdefault("settings", {}).get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        self._data.setdefault("settings", {})[key] = value
        self.mark_dirty()

    @property
    def maintenance(self) -> bool:
        return bool(self.setting("maintenance", False))

    def count_play(self, chat_id: int, title: str) -> None:
        stats = self._data.setdefault("stats", {"plays": 0, "tracks": {}})
        stats["plays"] = int(stats.get("plays", 0)) + 1
        tracks = stats.setdefault("tracks", {})
        key = title[:80]
        tracks[key] = int(tracks.get(key, 0)) + 1
        if len(tracks) > 500:  # جلوگیری از رشد بی‌نهایت
            trimmed = sorted(tracks.items(), key=lambda item: item[1], reverse=True)[:200]
            stats["tracks"] = dict(trimmed)
        chat = self.chat(chat_id)
        chat["plays"] = int(chat.get("plays", 0)) + 1
        self.mark_dirty()

    def total_plays(self) -> int:
        return int(self._data.get("stats", {}).get("plays", 0))

    def top_tracks(self, limit: int = 10) -> list[tuple[str, int]]:
        tracks = self._data.get("stats", {}).get("tracks", {})
        return sorted(tracks.items(), key=lambda item: item[1], reverse=True)[:limit]


db = Database()
