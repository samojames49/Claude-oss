"""ورود و خروج دستی اسیستنت به گروه."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant

from ..core.calls import calls_service
from ..core.decorators import player_handler
from ..core.filters import command
from ..core.service import player


@Client.on_message(
    command(["userbotjoin", "assistantjoin", "joinvc"], bare=["ورود اسیستنت"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def userbot_join(_client: Client, message, s):
    chat_id = message.chat.id
    assistant = calls_service.assistant(chat_id)
    try:
        await assistant.client.get_chat_member(chat_id, assistant.id)
        await message.reply_text(s("assistant_already_in"))
        return
    except UserNotParticipant:
        pass
    except Exception:  # noqa: BLE001 - ادامه می‌دهیم و تلاش می‌کنیم عضو شود
        pass

    status = await message.reply_text(s("joining"))
    await calls_service.ensure_assistant(chat_id)
    await status.edit_text(s("assistant_joined"))


@Client.on_message(
    command(["userbotleave", "assistantleave", "leavevc"], bare=["خروج اسیستنت"]) & filters.group,
    group=1,
)
@player_handler(admin_only=True)
async def userbot_leave(_client: Client, message, s):
    chat_id = message.chat.id
    await player.cleanup(chat_id)
    await calls_service.leave_chat(chat_id)
    await message.reply_text(s("assistant_left"))
