"""پشتیبانی ساده از لینک‌های اسپاتیفای: تبدیل لینک به عبارت جستجو.

بدون نیاز به کلید API؛ از سرویس عمومی oEmbed اسپاتیفای فقط نام قطعه گرفته می‌شود و
سپس همان نام در یوتیوب جستجو و پخش می‌شود.
"""

from __future__ import annotations

import re

import aiohttp

from ..utils.logger import get_logger

LOGGER = get_logger("spotify")

SPOTIFY_RE = re.compile(
    r"https?://(?:open|play)\.spotify\.com/(?:intl-\w+/)?(track|album|playlist|episode)/([\w]+)",
    re.IGNORECASE,
)
OEMBED = "https://open.spotify.com/oembed?url={url}"


def is_spotify_url(text: str) -> bool:
    return bool(SPOTIFY_RE.search(text or ""))


def link_kind(text: str) -> str | None:
    match = SPOTIFY_RE.search(text or "")
    return match.group(1).lower() if match else None


async def to_query(url: str, timeout: int = 10) -> str | None:
    """نام قطعه/آلبوم اسپاتیفای را برمی‌گرداند تا در یوتیوب جستجو شود."""
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as session:
            async with session.get(OEMBED.format(url=url)) as response:
                if response.status != 200:
                    return None
                data = await response.json(content_type=None)
    except Exception as error:  # noqa: BLE001 - شبکه/فرمت پاسخ
        LOGGER.warning("خواندن اطلاعات اسپاتیفای ناموفق بود: %s", error)
        return None
    title = (data or {}).get("title")
    return str(title).strip() if title else None
