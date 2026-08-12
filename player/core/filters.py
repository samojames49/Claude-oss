"""فیلترهای سفارشی: دستورهای چند‌پیشوندی و معادل‌های فارسی بدون اسلش."""

from __future__ import annotations

from pyrogram import filters as pyro_filters
from pyrogram.types import Message

PREFIXES = ("/", "!", ".", "#", "،")


def command(
    commands: str | list[str] | tuple[str, ...],
    bare: str | list[str] | tuple[str, ...] | None = None,
    prefixes: tuple[str, ...] = PREFIXES,
):
    """فیلتر دستور.

    - `commands`: دستورهای انگلیسی که با پیشوند (`/play`, `!play`, …) کار می‌کنند.
    - `bare`: معادل‌های فارسی که بدون پیشوند هم پذیرفته می‌شوند (مثل «پخش»).
    """
    english = [commands] if isinstance(commands, str) else list(commands)
    english = [item.lower() for item in english]
    if bare is None:
        persian: list[str] = []
    elif isinstance(bare, str):
        persian = [bare]
    else:
        persian = list(bare)

    # عبارت‌های چندکلمه‌ای فارسی (مثل «پخش ویدیو») باید قبل از تک‌کلمه‌ای بررسی شوند
    persian.sort(key=lambda item: len(item.split()), reverse=True)

    async def func(flt, client, message: Message) -> bool:
        text = (message.text or message.caption or "").strip()
        if not text:
            return False

        username = getattr(getattr(client, "me", None), "username", None)

        for phrase in flt.persian:
            if text == phrase or text.startswith(phrase + " ") or text.startswith(phrase + "\n"):
                message.command = [phrase] + text[len(phrase) :].split()
                return True

        first = text.split(maxsplit=1)[0]
        for prefix in flt.prefixes:
            if first.startswith(prefix) and len(first) > len(prefix):
                candidate = first[len(prefix) :]
                break
        else:
            return False

        if "@" in candidate:
            candidate, _, mentioned = candidate.partition("@")
            if username and mentioned.lower() != username.lower():
                return False

        if candidate.lower() not in flt.english and candidate not in flt.persian:
            return False

        parts = text.split()
        message.command = [candidate.lower()] + parts[1:]
        return True

    return pyro_filters.create(
        func,
        "PlayerCommandFilter",
        english=english,
        persian=persian,
        prefixes=prefixes,
    )


def argument(message: Message, join: bool = True) -> str:
    """متن بعد از دستور."""
    parts = getattr(message, "command", None)
    if not parts:
        return ""
    if join:
        return " ".join(parts[1:]).strip()
    return parts[1] if len(parts) > 1 else ""
