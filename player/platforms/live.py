"""لینک‌های مستقیم و پخش زنده (رادیو، m3u8، mpd و فایل‌های مستقیم)."""

from __future__ import annotations

from urllib.parse import urlparse

LIVE_EXTENSIONS = (".m3u8", ".m3u", ".mpd", ".ts", ".pls")
DIRECT_EXTENSIONS = (
    ".mp3",
    ".m4a",
    ".aac",
    ".ogg",
    ".opus",
    ".flac",
    ".wav",
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
    ".avi",
)


def _path(url: str) -> str:
    try:
        return urlparse(url).path.lower()
    except ValueError:
        return ""


def is_live_url(url: str) -> bool:
    path = _path(url)
    return any(path.endswith(ext) for ext in LIVE_EXTENSIONS)


def is_direct_media_url(url: str) -> bool:
    path = _path(url)
    return any(path.endswith(ext) for ext in DIRECT_EXTENSIONS)


def is_streamable_url(url: str) -> bool:
    return is_live_url(url) or is_direct_media_url(url)


def title_from_url(url: str) -> str:
    path = _path(url)
    name = path.rsplit("/", 1)[-1] if path else ""
    if name:
        return name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip() or url
    host = urlparse(url).netloc
    return host or url
