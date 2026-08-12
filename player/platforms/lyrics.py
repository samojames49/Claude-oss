"""دریافت متن آهنگ از سرویس عمومی LRCLIB (بدون کلید API)."""

from __future__ import annotations

import aiohttp

from ..utils.logger import get_logger

LOGGER = get_logger("lyrics")

SEARCH_URL = "https://lrclib.net/api/search"
HEADERS = {"User-Agent": "TelegramPlayerBot/1.0 (+https://t.me)"}


async def search(query: str, timeout: int = 12) -> tuple[str, str] | None:
    """(عنوان، متن) اولین نتیجهٔ دارای متن را برمی‌گرداند."""
    if not query.strip():
        return None
    try:
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=client_timeout, headers=HEADERS) as session:
            async with session.get(SEARCH_URL, params={"q": query}) as response:
                if response.status != 200:
                    return None
                data = await response.json(content_type=None)
    except Exception as error:  # noqa: BLE001
        LOGGER.warning("دریافت متن آهنگ ناموفق بود: %s", error)
        return None

    if not isinstance(data, list):
        return None
    for item in data:
        text = (item or {}).get("plainLyrics")
        if text:
            name = " - ".join(
                filter(None, [(item or {}).get("artistName"), (item or {}).get("trackName")])
            )
            return name or query, str(text).strip()
    return None
