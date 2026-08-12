"""مدیریت صف پخش هر گروه (در حافظه)."""

from __future__ import annotations

import random
from time import time

from .track import Track


class QueueManager:
    """صف پخش، آهنگ فعال، تکرار و وضعیت توقف را برای هر گروه نگه می‌دارد."""

    def __init__(self) -> None:
        self._queues: dict[int, list[Track]] = {}
        self._active: dict[int, Track] = {}
        self._loops: dict[int, int] = {}
        self._paused: set[int] = set()
        self._muted: set[int] = set()
        self._volumes: dict[int, int] = {}
        self._panels: dict[int, int] = {}  # آیدی پیام پنل «در حال پخش»
        self._started_at: dict[int, float] = {}
        self._last_activity: dict[int, float] = {}
        self._empty_since: dict[int, float] = {}

    # ── وضعیت ────────────────────────────────────────────────────────────────
    def active_chats(self) -> list[int]:
        return list(self._active.keys())

    def is_active(self, chat_id: int) -> bool:
        return chat_id in self._active

    def current(self, chat_id: int) -> Track | None:
        return self._active.get(chat_id)

    def set_current(self, chat_id: int, track: Track | None) -> None:
        if track is None:
            self._active.pop(chat_id, None)
            self._started_at.pop(chat_id, None)
        else:
            self._active[chat_id] = track
            self._started_at[chat_id] = time()
            self.touch(chat_id)

    def started_at(self, chat_id: int) -> float:
        return self._started_at.get(chat_id, 0.0)

    def touch(self, chat_id: int) -> None:
        self._last_activity[chat_id] = time()
        self._empty_since.pop(chat_id, None)

    def last_activity(self, chat_id: int) -> float:
        return self._last_activity.get(chat_id, 0.0)

    def mark_empty(self, chat_id: int) -> float:
        """زمان شروع خالی‌بودن ویس‌چت را ثبت و برمی‌گرداند."""
        return self._empty_since.setdefault(chat_id, time())

    def clear_empty(self, chat_id: int) -> None:
        self._empty_since.pop(chat_id, None)

    # ── صف ───────────────────────────────────────────────────────────────────
    def queue(self, chat_id: int) -> list[Track]:
        return self._queues.setdefault(chat_id, [])

    def size(self, chat_id: int) -> int:
        return len(self._queues.get(chat_id, []))

    def add(self, chat_id: int, track: Track) -> int:
        """افزودن به انتهای صف؛ شمارهٔ جایگاه (۱ به بعد) را برمی‌گرداند."""
        queue = self.queue(chat_id)
        queue.append(track)
        self.touch(chat_id)
        return len(queue)

    def add_next(self, chat_id: int, track: Track) -> None:
        self.queue(chat_id).insert(0, track)
        self.touch(chat_id)

    def pop_next(self, chat_id: int) -> Track | None:
        """آیتم بعدی را با در نظر گرفتن تکرار برمی‌گرداند."""
        loops = self._loops.get(chat_id, 0)
        if loops > 0:
            current = self._active.get(chat_id)
            if current is not None:
                self._loops[chat_id] = loops - 1
                if self._loops[chat_id] <= 0:
                    self._loops.pop(chat_id, None)
                repeat = current.clone()
                repeat.seek = 0
                return repeat
        queue = self._queues.get(chat_id)
        if not queue:
            return None
        return queue.pop(0)

    def peek_next(self, chat_id: int) -> Track | None:
        queue = self._queues.get(chat_id)
        return queue[0] if queue else None

    def remove(self, chat_id: int, index: int) -> Track | None:
        """حذف آیتم با شمارهٔ نمایش‌داده‌شده (۱ به بعد)."""
        queue = self._queues.get(chat_id)
        if not queue or index < 1 or index > len(queue):
            return None
        return queue.pop(index - 1)

    def shuffle(self, chat_id: int) -> int:
        queue = self._queues.get(chat_id) or []
        random.shuffle(queue)
        return len(queue)

    def clear(self, chat_id: int) -> None:
        self._queues.pop(chat_id, None)

    def reset(self, chat_id: int) -> None:
        """پاک‌سازی کامل وضعیت یک گروه (هنگام پایان پخش)."""
        self._queues.pop(chat_id, None)
        self._active.pop(chat_id, None)
        self._loops.pop(chat_id, None)
        self._paused.discard(chat_id)
        self._muted.discard(chat_id)
        self._volumes.pop(chat_id, None)
        self._panels.pop(chat_id, None)
        self._started_at.pop(chat_id, None)
        self._last_activity.pop(chat_id, None)
        self._empty_since.pop(chat_id, None)

    # ── تکرار ────────────────────────────────────────────────────────────────
    def loop(self, chat_id: int) -> int:
        return self._loops.get(chat_id, 0)

    def set_loop(self, chat_id: int, count: int) -> int:
        if count <= 0:
            self._loops.pop(chat_id, None)
            return 0
        self._loops[chat_id] = count
        return count

    # ── توقف/بی‌صدا/صدا ──────────────────────────────────────────────────────
    def is_paused(self, chat_id: int) -> bool:
        return chat_id in self._paused

    def set_paused(self, chat_id: int, paused: bool) -> None:
        if paused:
            self._paused.add(chat_id)
        else:
            self._paused.discard(chat_id)
        self.touch(chat_id)

    def is_muted(self, chat_id: int) -> bool:
        return chat_id in self._muted

    def set_muted(self, chat_id: int, muted: bool) -> None:
        if muted:
            self._muted.add(chat_id)
        else:
            self._muted.discard(chat_id)

    def volume(self, chat_id: int) -> int:
        return self._volumes.get(chat_id, 100)

    def set_volume(self, chat_id: int, volume: int) -> None:
        self._volumes[chat_id] = volume

    # ── پنل «در حال پخش» ─────────────────────────────────────────────────────
    def panel(self, chat_id: int) -> int | None:
        return self._panels.get(chat_id)

    def set_panel(self, chat_id: int, message_id: int | None) -> None:
        if message_id is None:
            self._panels.pop(chat_id, None)
        else:
            self._panels[chat_id] = message_id

    def video_chats(self) -> list[int]:
        return [chat_id for chat_id, track in self._active.items() if track.video]


queues = QueueManager()
