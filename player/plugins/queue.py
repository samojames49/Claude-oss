"""دستورهای مربوط به صف پخش."""

from __future__ import annotations

from pyrogram import Client, filters

from ..core.decorators import player_handler
from ..core.filters import argument, command
from ..core.queues import queues
from ..core.service import player
from ..core.targets import playback_chat
from ..utils.formatters import to_latin_digits
from ..utils.keyboards import player_panel, queue_panel


@Client.on_message(command(["queue", "playlist", "q"], bare=["صف", "لیست"]) & filters.group, group=1)
@player_handler(require_active=True)
async def queue_command(_client: Client, message, s):
    text = await player.queue_text(playback_chat(message.chat.id))
    await message.reply_text(text, reply_markup=queue_panel(s.language))


@Client.on_message(
    command(["current", "now", "np", "nowplaying"], bare=["فعلی", "درحال پخش"]) & filters.group,
    group=1,
)
@player_handler(require_active=True)
async def current_command(_client: Client, message, s):
    chat_id = playback_chat(message.chat.id)
    text = await player.status_text(chat_id)
    await message.reply_text(
        text,
        reply_markup=player_panel(
            s.language,
            paused=queues.is_paused(chat_id),
            muted=queues.is_muted(chat_id),
        ),
    )


@Client.on_message(command(["remove", "rm"], bare=["حذف"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def remove_command(_client: Client, message, s):
    raw = to_latin_digits(argument(message))
    if not raw.isdigit():
        await message.reply_text(s("err_invalid_number"))
        return
    removed = queues.remove(playback_chat(message.chat.id), int(raw))
    if removed is None:
        await message.reply_text(s("err_invalid_number"))
        return
    await message.reply_text(s("removed_from_queue", title=removed.short_title))


@Client.on_message(command(["clear", "clearqueue"], bare=["پاک کردن صف"]) & filters.group, group=1)
@player_handler(admin_only=True, require_active=True)
async def clear_command(_client: Client, message, s):
    queues.clear(playback_chat(message.chat.id))
    await message.reply_text(s("queue_cleared"))
