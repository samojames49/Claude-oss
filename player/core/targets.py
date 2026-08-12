"""تعیین این‌که پخش باید در خود گروه انجام شود یا در کانال متصل به آن.

با «تنظیم کانال پلیر» یک کانال به گروه وصل می‌شود و با «پخش کانال فعال» تمام پخش‌ها
به ویس‌چت آن کانال منتقل می‌شوند؛ دستورها همچنان در گروه گرفته و پاسخ داده می‌شوند.
"""

from __future__ import annotations

from .db import db


def playback_chat(chat_id: int | None) -> int | None:
    """چتی که ویس‌چتش باید استفاده شود."""
    if chat_id is None:
        return None
    if not db.chat_setting(chat_id, "play_in_channel", False):
        return chat_id
    try:
        channel = int(db.chat_setting(chat_id, "player_channel", 0) or 0)
    except (TypeError, ValueError):
        return chat_id
    return channel or chat_id


def is_redirected(chat_id: int) -> bool:
    return playback_chat(chat_id) != chat_id
