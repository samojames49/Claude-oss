"""پخش فایل‌های صوتی/ویدیویی که داخل خود تلگرام فرستاده شده‌اند."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import config
from ..core.errors import FileTooBig
from ..core.track import Track
from ..utils.logger import get_logger

LOGGER = get_logger("telegram")

AUDIO_KINDS = ("audio", "voice")
VIDEO_KINDS = ("video", "video_note", "animation")


def extract_media(message: Any) -> tuple[str, Any] | None:
    """نوع و آبجکت مدیای یک پیام (اگر قابل پخش باشد)."""
    if message is None:
        return None
    for kind in ("audio", "voice", "video", "video_note", "animation", "document"):
        media = getattr(message, kind, None)
        if media is None:
            continue
        if kind == "document":
            mime = (getattr(media, "mime_type", "") or "").lower()
            if not (mime.startswith("audio/") or mime.startswith("video/")):
                continue
            kind = "video" if mime.startswith("video/") else "audio"
        return kind, media
    return None


def has_playable_media(message: Any) -> bool:
    return extract_media(message) is not None


def _media_title(kind: str, media: Any) -> str:
    title = getattr(media, "title", None)
    if title:
        performer = getattr(media, "performer", None)
        return f"{performer} - {title}" if performer else str(title)
    name = getattr(media, "file_name", None)
    if name:
        return Path(str(name)).stem
    return "صدای ضبط‌شده" if kind == "voice" else "فایل تلگرام"


async def to_track(
    client: Any,
    message: Any,
    *,
    video: bool = False,
    requester_id: int = 0,
    requester_name: str = "",
    progress: Any = None,
) -> Track:
    """دانلود فایل تلگرام و ساخت یک آیتم پخش از آن."""
    found = extract_media(message)
    if found is None:
        raise ValueError("پیام مدیای قابل پخش ندارد.")
    kind, media = found

    size_mb = int(getattr(media, "file_size", 0) or 0) / (1024 * 1024)
    if size_mb > config.MAX_TELEGRAM_FILE_MB:
        raise FileTooBig(config.MAX_TELEGRAM_FILE_MB)

    destination = config.DOWNLOADS_DIR / "telegram"
    destination.mkdir(parents=True, exist_ok=True)
    path = await client.download_media(
        message,
        file_name=str(destination) + "/",
        progress=progress,
    )
    if not path:
        raise ValueError("دانلود فایل تلگرام ناموفق بود.")

    is_video = video or kind in VIDEO_KINDS
    return Track(
        title=_media_title(kind, media),
        source=str(path),
        file_path=str(path),
        kind="telegram",
        duration=int(getattr(media, "duration", 0) or 0),
        video=is_video,
        thumbnail=None,
        requester_id=requester_id,
        requester_name=requester_name,
        message_id=getattr(message, "id", None),
    )
