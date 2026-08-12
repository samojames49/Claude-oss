"""فهرست شبکه‌های «پخش زنده» (تلویزیون، ماهواره، رادیو) از یک فایل JSON.

فایل پیش‌فرض `player/data/live_channels.json` است و مدیر ربات می‌تواند آن را کامل
عوض کند یا با `LIVE_CHANNELS_FILE` به فایل خودش اشاره بدهد.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .. import config
from ..core.track import Track
from ..utils.logger import get_logger

LOGGER = get_logger("livetv")


@dataclass
class LiveChannel:
    name: str
    url: str
    video: bool = True
    category: str = ""

    def to_track(self, *, requester_id: int = 0, requester_name: str = "") -> Track:
        return Track(
            title=self.name,
            source=self.url,
            kind="live",
            duration=0,
            video=self.video,
            url=self.url,
            requester_id=requester_id,
            requester_name=requester_name,
        )


@dataclass
class LiveCategory:
    id: str
    title: str
    channels: list[LiveChannel]


_CACHE: tuple[float, list[LiveCategory]] | None = None


def _parse(raw: dict) -> list[LiveCategory]:
    categories: list[LiveCategory] = []
    for index, entry in enumerate(raw.get("categories", []) or []):
        if not isinstance(entry, dict):
            continue
        category_id = str(entry.get("id") or f"c{index}")
        channels: list[LiveChannel] = []
        for item in entry.get("channels", []) or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            url = str(item.get("url") or "").strip()
            if not name or not url:
                continue
            channels.append(
                LiveChannel(
                    name=name,
                    url=url,
                    video=bool(item.get("video", True)),
                    category=category_id,
                )
            )
        if channels:
            categories.append(
                LiveCategory(
                    id=category_id,
                    title=str(entry.get("title") or category_id),
                    channels=channels,
                )
            )
    return categories


def load(force: bool = False) -> list[LiveCategory]:
    """خواندن فایل شبکه‌ها با کش بر اساس زمان تغییر فایل."""
    global _CACHE

    path = config.live_channels_file()
    try:
        stamp = path.stat().st_mtime
    except OSError:
        if _CACHE is not None:
            return _CACHE[1]
        LOGGER.warning("فایل شبکه‌های پخش زنده پیدا نشد: %s", path)
        return []

    if not force and _CACHE is not None and _CACHE[0] == stamp:
        return _CACHE[1]

    try:
        with path.open(encoding="utf-8") as handle:
            categories = _parse(json.load(handle))
    except (OSError, json.JSONDecodeError) as error:
        LOGGER.error("خواندن فایل شبکه‌های پخش زنده ناموفق بود: %s", error)
        return _CACHE[1] if _CACHE else []

    _CACHE = (stamp, categories)
    return categories


def categories() -> list[LiveCategory]:
    return load()


def category(category_id: str) -> LiveCategory | None:
    for entry in load():
        if entry.id == category_id:
            return entry
    return None


def channel(category_id: str, index: int) -> LiveChannel | None:
    entry = category(category_id)
    if entry is None or index < 0 or index >= len(entry.channels):
        return None
    return entry.channels[index]


def total_channels() -> int:
    return sum(len(entry.channels) for entry in load())


def search(query: str) -> list[LiveChannel]:
    """جستجوی نام شبکه در همهٔ دسته‌ها."""
    needle = query.strip().lower()
    if not needle:
        return []
    found: list[LiveChannel] = []
    for entry in load():
        for item in entry.channels:
            if needle in item.name.lower():
                found.append(item)
    return found
