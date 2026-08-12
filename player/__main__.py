"""نقطهٔ شروع ربات پلیر:  python -m player"""

from __future__ import annotations

import asyncio

from . import config
from .utils.logger import LOGGER


async def _run() -> None:
    config.validate()

    # ایمپورت بعد از اعتبارسنجی تنظیمات انجام می‌شود تا کلاینت‌ها با مقادیر درست ساخته شوند
    from .core.callwatch import callwatch
    from .core.clients import start_clients, stop_clients
    from .core.db import db
    from .core.service import player

    await db.start()
    await start_clients()

    player.setup_handlers()
    player.start_watcher()
    callwatch.start()
    autosave = asyncio.create_task(db.autosave_loop())

    from .core.clients import bot

    me = await bot.get_me()
    LOGGER.info("🎧 %s (@%s) آماده است.", config.BOT_NAME, me.username)

    if config.LOGGER_ID:
        try:
            await bot.send_message(
                config.LOGGER_ID,
                f"🎧 **{config.BOT_NAME}** راه‌اندازی شد.\n"
                f"اسیستنت‌ها: `{len(config.STRING_SESSIONS)}`",
            )
        except Exception as error:  # noqa: BLE001
            LOGGER.warning(
                "ارسال پیام راه‌اندازی به گروه لاگ ناموفق بود (LOGGER_ID را بررسی کنید): %s",
                error,
            )

    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        autosave.cancel()
        await db.save()
        await stop_clients()
        LOGGER.info("ربات متوقف شد.")


def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        LOGGER.info("خروج با درخواست کاربر.")


if __name__ == "__main__":
    main()
