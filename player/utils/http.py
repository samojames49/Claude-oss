"""ابزار دانلود ساده روی aiohttp."""

from __future__ import annotations

from pathlib import Path

import aiohttp

from .logger import get_logger

LOGGER = get_logger("http")


async def download_file(url: str, destination: Path | str, timeout: int = 20) -> bool:
    """دانلود یک فایل کوچک (تامبنیل و مانند آن)."""
    path = Path(destination)
    try:
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=client_timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return False
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(await response.read())
        return True
    except Exception as error:  # noqa: BLE001 - شبکه
        LOGGER.debug("دانلود %s ناموفق بود: %s", url[:80], error)
        return False
