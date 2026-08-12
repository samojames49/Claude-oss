"""زیرنویس فارسی (SoftSub) روی پخش ویدیویی ویس‌چت."""

from __future__ import annotations

import re
from pathlib import Path

from pyrogram import Client, filters

from .. import config
from ..core.decorators import player_handler
from ..core.filters import argument, command
from ..core.queues import queues
from ..core.service import player
from ..core.targets import playback_chat

SUBTITLE_EXTENSIONS = (".srt", ".vtt", ".ass", ".ssa", ".sub")
OFF_WORDS = ("حذف", "خاموش", "بردار", "off", "remove", "none", "غیرفعال")
_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _is_subtitle(message) -> bool:
    document = getattr(message, "document", None)
    if document is None:
        return False
    name = (getattr(document, "file_name", "") or "").lower()
    return name.endswith(SUBTITLE_EXTENSIONS)


def _safe_path(chat_id: int, file_name: str) -> Path:
    """نام فایل را ساده می‌کنیم چون مسیر داخل فیلتر ffmpeg قرار می‌گیرد."""
    suffix = Path(file_name).suffix.lower() or ".srt"
    stem = _SAFE_NAME.sub("_", Path(file_name).stem)[:40] or "sub"
    directory = config.CACHE_DIR / "subtitles"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{abs(chat_id)}_{stem}{suffix}"


@Client.on_message(
    command(["subtitle", "softsub", "sub"], bare=["زیرنویس", "ساب"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True, require_active=True)
async def subtitle_command(client: Client, message, s):
    """با ریپلای روی فایل زیرنویس، آن را روی ویدیوی در حال پخش می‌چسباند."""
    chat_id = playback_chat(message.chat.id)
    if not config.SUBTITLE_ENABLED:
        await message.reply_text(s("subtitle_disabled"))
        return

    if argument(message).strip().lower() in OFF_WORDS:
        await player.set_subtitle(chat_id, None)
        await message.reply_text(s("subtitle_removed"))
        return

    replied = getattr(message, "reply_to_message", None)
    if replied is None or not _is_subtitle(replied):
        await message.reply_text(s("subtitle_usage"))
        return

    document = replied.document
    if document.file_size and document.file_size > config.SUBTITLE_MAX_MB * 1024 * 1024:
        await message.reply_text(s("err_file_too_big", limit=config.SUBTITLE_MAX_MB))
        return

    track = queues.current(chat_id)
    if track is not None and not track.video:
        await message.reply_text(s("subtitle_audio_only"))
        return

    status = await message.reply_text(s("downloading"))
    target = _safe_path(chat_id, document.file_name or "subtitle.srt")
    try:
        await client.download_media(replied, file_name=str(target))
    finally:
        try:
            await status.delete()
        except Exception:  # noqa: BLE001
            pass

    updated = await player.set_subtitle(chat_id, str(target))
    await message.reply_text(s("subtitle_applied", title=updated.short_title))
