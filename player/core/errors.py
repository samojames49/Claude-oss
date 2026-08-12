"""خطاهای قابل‌نمایش به کاربر (به کلید رشتهٔ ترجمه‌شده اشاره می‌کنند)."""

from __future__ import annotations

from typing import Any


class UserError(Exception):
    """خطایی که پیام آن باید به زبان گروه به کاربر نشان داده شود."""

    key = "err_generic"

    def __init__(self, key: str | None = None, **params: Any) -> None:
        self.key = key or self.key
        self.params = params
        super().__init__(self.key)


class NoVoiceChat(UserError):
    key = "err_no_vc"


class NotPlaying(UserError):
    key = "err_no_active"


class AssistantJoinError(UserError):
    key = "err_assistant_failed"

    def __init__(self, error: str = "") -> None:
        super().__init__(error=error)


class AssistantBanned(UserError):
    key = "err_assistant_banned"

    def __init__(self, assistant: str = "") -> None:
        super().__init__(assistant=assistant)


class DurationLimit(UserError):
    key = "err_duration_limit"

    def __init__(self, duration: str, limit: int) -> None:
        super().__init__(duration=duration, limit=limit)


class QueueFull(UserError):
    key = "err_queue_limit"

    def __init__(self, limit: int) -> None:
        super().__init__(limit=limit)


class NoResult(UserError):
    key = "err_no_result"


class FileTooBig(UserError):
    key = "err_file_too_big"

    def __init__(self, limit: int) -> None:
        super().__init__(limit=limit)
