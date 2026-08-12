"""دستورهای وضعیت: /ping، /uptime، /stats."""

from __future__ import annotations

from time import time

from pyrogram import Client, filters

from .. import __version__, config
from ..core.calls import calls_service
from ..core.db import db
from ..core.decorators import player_handler
from ..core.filters import command
from ..core.queues import queues
from ..core.service import player
from ..utils.formatters import human_timedelta

try:
    import psutil
except ImportError:  # pragma: no cover - اختیاری
    psutil = None


def _system_usage() -> tuple[float, float, float]:
    if psutil is None:
        return 0.0, 0.0, 0.0
    try:
        return (
            psutil.cpu_percent(interval=0.2),
            psutil.virtual_memory().percent,
            psutil.disk_usage("/").percent,
        )
    except Exception:  # noqa: BLE001
        return 0.0, 0.0, 0.0


@Client.on_message(command(["ping", "alive"], bare=["پینگ"]), group=1)
@player_handler(group_only=False)
async def ping_command(_client: Client, message, s):
    started = time()
    status = await message.reply_text("🏓 …")
    latency = round((time() - started) * 1000)
    cpu, ram, disk = _system_usage()
    await status.edit_text(
        s(
            "ping_reply",
            ping=latency,
            uptime=human_timedelta(player.uptime),
            cpu=cpu,
            ram=ram,
            disk=disk,
            active=len(queues.active_chats()),
        )
    )


@Client.on_message(command(["uptime"], bare=["آپتایم"]), group=1)
@player_handler(group_only=False)
async def uptime_command(_client: Client, message, s):
    cpu, ram, disk = _system_usage()
    await message.reply_text(
        s(
            "ping_reply",
            ping=round(calls_service.ping()),
            uptime=human_timedelta(player.uptime),
            cpu=cpu,
            ram=ram,
            disk=disk,
            active=len(queues.active_chats()),
        )
    )


@Client.on_message(command(["stats", "status"], bare=["آمار"]), group=1)
@player_handler(group_only=False)
async def stats_command(_client: Client, message, s):
    data = player.stats()
    text = s(
        "stats_reply",
        bot_name=config.BOT_NAME,
        chats=data["chats"],
        users=data["users"],
        plays=data["plays"],
        active=data["active"],
        assistants=data["assistants"],
        uptime=human_timedelta(player.uptime),
        version=__version__,
    )
    if db.is_sudo(message.from_user.id if message.from_user else 0):
        top = db.top_tracks(5)
        if top:
            text += "\n\n🔝 **پرپخش‌ترین‌ها:**\n" + "\n".join(
                f"{index}. {title} — `{count}`" for index, (title, count) in enumerate(top, 1)
            )
    await message.reply_text(text)
